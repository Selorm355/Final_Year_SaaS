import os
import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt
import secrets
import string

# --- NEW: Key Generator ---
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

# --- 2. THE SELF-HEALING INIT (Workspace & Billing Update) ---
def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # Auto-create medallion schemas so users never see a schema error
    cur.execute("CREATE SCHEMA IF NOT EXISTS bronze;")
    cur.execute("CREATE SCHEMA IF NOT EXISTS silver;")
    cur.execute("CREATE SCHEMA IF NOT EXISTS gold;")

    # Removed the UNIQUE constraint from email alone. 
    # Added subscription tracking and a Composite Unique Constraint at the bottom.
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

# --- 4. THE LOGIN LOGIC (Workspace Update) ---
def authenticate_user(email, company_name, raw_password):
    # Now requires company_name to find the exact workspace
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

# --- 5. THE PASSWORD RESET LOGIC (Workspace Update) ---
def reset_password(email, company_name, raw_recovery_key, new_raw_password):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Locate the exact workspace
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