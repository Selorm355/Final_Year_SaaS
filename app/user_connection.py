import os
import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt
import secrets
import string

# --- KEY GENERATOR ---
def generate_recovery_key():
    """Generates a secure 12-character key like A7X9-B2M4-99QQ"""
    alphabet = string.ascii_uppercase + string.digits
    parts = [''.join(secrets.choice(alphabet) for _ in range(4)) for _ in range(3)]
    return '-'.join(parts)

# --- 1. THE BRIDGE ---
def get_connection():
    return psycopg2.connect(
        host="db",
        port="5432",
        database=os.environ.get("POSTGRES_DB"),
        user=os.environ.get("POSTGRES_USER"),
        password=os.environ.get("POSTGRES_PASSWORD")
    )

# --- 2. THE SELF-HEALING INIT (Medallion & Billing Foundation) ---
def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # Auto-create medallion schemas so users never see a schema error
    cur.execute("CREATE SCHEMA IF NOT EXISTS bronze;")
    cur.execute("CREATE SCHEMA IF NOT EXISTS silver;")
    cur.execute("CREATE SCHEMA IF NOT EXISTS gold;")

    # 1. Base Users Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            company_id SERIAL PRIMARY KEY,
            company_name VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL,
            industry VARCHAR(50) NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            recovery_key VARCHAR(255) NOT NULL, 
            subscription_tier VARCHAR(50) DEFAULT 'Free',
            upload_count INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (email, company_name) 
        );
    """)

    # Self-healing column addition for existing databases
    cur.execute("""
        ALTER TABLE users 
        ADD COLUMN IF NOT EXISTS dashboard_views_left INT DEFAULT 3;
    """)

    # 2. Subscriptions Table (Active Contracts)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            subscription_id SERIAL PRIMARY KEY,
            company_id INT REFERENCES users(company_id) ON DELETE CASCADE,
            plan_type VARCHAR(50) NOT NULL,
            status VARCHAR(50) DEFAULT 'ACTIVE',
            start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            end_date TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 3. Transactions Table (Financial Audit Trail)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id SERIAL PRIMARY KEY,
            company_id INT REFERENCES users(company_id) ON DELETE CASCADE,
            client_reference VARCHAR(255) UNIQUE NOT NULL,
            hubtel_transaction_id VARCHAR(255),
            amount NUMERIC(10, 2) NOT NULL,
            plan_type VARCHAR(50) NOT NULL,
            payment_status VARCHAR(50) DEFAULT 'PENDING',
            payment_method VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    conn.commit()
    cur.close()
    conn.close()

# --- 3. THE REGISTRATION LOGIC ---
def register_user(company_name, email, industry, raw_password):
    hashed_bytes = bcrypt.hashpw(raw_password.encode('utf-8'), bcrypt.gensalt())
    password_hash = hashed_bytes.decode('utf-8')
    
    raw_recovery_key = generate_recovery_key()
    key_hashed_bytes = bcrypt.hashpw(raw_recovery_key.encode('utf-8'), bcrypt.gensalt())
    recovery_key_hash = key_hashed_bytes.decode('utf-8')
    
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO users (company_name, email, industry, password_hash, recovery_key)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING company_id;
        """, (company_name, email, industry, password_hash, recovery_key_hash))
        
        conn.commit()
        return True, "Registration successful!", raw_recovery_key
        
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return False, "This Company Name is already registered under this email.", None
    finally:
        cur.close()
        conn.close()

# --- 4. THE LOGIN LOGIC ---
def authenticate_user(email, company_name, raw_password):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor) 
    cur.execute("SELECT * FROM users WHERE email = %s AND company_name = %s;", (email, company_name))
    user = cur.fetchone()
    cur.close()
    conn.close()
    
    if not user:
        return False, None
        
    if bcrypt.checkpw(raw_password.encode('utf-8'), user['password_hash'].encode('utf-8')):
        return True, user
    else:
        return False, None

# --- 5. THE PASSWORD RESET LOGIC ---
def reset_password(email, company_name, raw_recovery_key, new_raw_password):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("SELECT * FROM users WHERE email = %s AND company_name = %s;", (email, company_name))
    user = cur.fetchone()
    
    if not user:
        cur.close()
        conn.close()
        return False, "Invalid Email, Company Name, or Recovery Key."
        
    if bcrypt.checkpw(raw_recovery_key.encode('utf-8'), user['recovery_key'].encode('utf-8')):
        new_hashed_bytes = bcrypt.hashpw(new_raw_password.encode('utf-8'), bcrypt.gensalt())
        new_password_hash = new_hashed_bytes.decode('utf-8')
        
        cur.execute("""
            UPDATE users 
            SET password_hash = %s 
            WHERE email = %s AND company_name = %s;
        """, (new_password_hash, email, company_name))
        
        conn.commit()
        cur.close()
        conn.close()
        return True, "Password successfully reset! You can now log in."
    else:
        cur.close()
        conn.close()
        return False, "Invalid Email, Company Name, or Recovery Key."

# =========================================================
# --- 6. BILLING & SUBSCRIPTION ENGINE (Phase 1 Additions) ---
# =========================================================

def get_subscription_info(company_id):
    """
    Checks whether a company has an active paid subscription or free trial credits.
    Returns a dictionary with subscription status and remaining trial views.
    """
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("""
        SELECT subscription_tier, dashboard_views_left 
        FROM users 
        WHERE company_id = %s;
    """, (company_id,))
    user = cur.fetchone()
    
    if not user:
        cur.close()
        conn.close()
        return None

    # Check for active subscription row
    cur.execute("""
        SELECT * FROM subscriptions 
        WHERE company_id = %s AND status = 'ACTIVE' AND end_date > CURRENT_TIMESTAMP
        ORDER BY end_date DESC LIMIT 1;
    """, (company_id,))
    active_sub = cur.fetchone()
    
    cur.close()
    conn.close()

    is_paid = (active_sub is not None) or (user['subscription_tier'] in ['Pro', 'Enterprise'])

    return {
        "tier": user['subscription_tier'],
        "views_left": user['dashboard_views_left'] if user['dashboard_views_left'] is not None else 0,
        "is_paid": is_paid,
        "active_subscription": active_sub
    }

def consume_trial_view(company_id):
    """
    Deducts 1 dashboard view credit from a free tier user.
    Returns the updated number of views left.
    """
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("""
        UPDATE users 
        SET dashboard_views_left = GREATEST(0, dashboard_views_left - 1)
        WHERE company_id = %s AND subscription_tier = 'Free'
        RETURNING dashboard_views_left;
    """, (company_id,))
    
    result = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    
    if result:
        return result['dashboard_views_left']
    return 0

def record_pending_transaction(company_id, client_reference, amount, plan_type):
    """
    Creates a pending transaction receipt before sending the user to Hubtel.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO transactions (company_id, client_reference, amount, plan_type, payment_status)
            VALUES (%s, %s, %s, %s, 'PENDING');
        """, (company_id, client_reference, amount, plan_type))
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

def get_pending_transaction(client_reference):
    """Retrieves a transaction by its client reference."""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM transactions WHERE client_reference = %s;", (client_reference,))
    tx = cur.fetchone()
    cur.close()
    conn.close()
    return tx

def activate_subscription_and_log_transaction(company_id, client_reference, hubtel_tx_id, payment_method, plan_type, duration_days=30):
    """
    Upon payment verification:
    1. Updates transactions table to SUCCESS.
    2. Updates user table subscription_tier to 'Pro' or 'Enterprise'.
    3. Adds an active record to the subscriptions table with accurate expiration math.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        # 1. Update transaction record
        cur.execute("""
            UPDATE transactions 
            SET payment_status = 'SUCCESS',
                hubtel_transaction_id = %s,
                payment_method = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE client_reference = %s AND company_id = %s;
        """, (hubtel_tx_id, payment_method, client_reference, company_id))

        # 2. Upgrade user tier
        new_tier = 'Enterprise' if 'yearly' in plan_type.lower() else 'Pro'
        cur.execute("""
            UPDATE users 
            SET subscription_tier = %s 
            WHERE company_id = %s;
        """, (new_tier, company_id))

        # 3. Insert active subscription contract
        cur.execute("""
            INSERT INTO subscriptions (company_id, plan_type, status, start_date, end_date)
            VALUES (%s, %s, 'ACTIVE', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP + (%s || ' days')::INTERVAL);
        """, (company_id, plan_type, duration_days))

        conn.commit()
        return True, "Subscription activated successfully!"
    except Exception as e:
        conn.rollback()
        return False, f"Failed to activate subscription: {e}"
    finally:
        cur.close()
        conn.close()