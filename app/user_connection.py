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

# --- 2. THE SELF-HEALING INIT ---
def init_db():
    conn = get_connection()
    cur = conn.cursor()
    
    # CRITICAL FIX: recovery_key is now VARCHAR(255) to fit the 60-character bcrypt hash!
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            company_id SERIAL PRIMARY KEY,
            company_name VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            industry VARCHAR(50) NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            recovery_key VARCHAR(255) NOT NULL, 
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    conn.commit()
    cur.close()
    conn.close()

# --- 3. THE REGISTRATION LOGIC ---
def register_user(company_name, email, industry, raw_password):
    hashed_bytes = bcrypt.hashpw(raw_password.encode('utf-8'), bcrypt.gensalt())
    password_hash = hashed_bytes.decode('utf-8')
    
    # Generate the raw key, but hash it before saving!
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
        """, (company_name, email, industry, password_hash, recovery_key_hash)) # Saving the HASH
        
        conn.commit()
        return True, "Registration successful!", raw_recovery_key # Returning RAW to Streamlit
        
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return False, "This email is already registered.", None
    finally:
        cur.close()
        conn.close()

# --- 4. THE LOGIN LOGIC ---
def authenticate_user(email, raw_password):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor) 
    cur.execute("SELECT * FROM users WHERE email = %s;", (email,))
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
def reset_password(email, raw_recovery_key, new_raw_password):
    """Verifies the hashed recovery key and overwrites the old password."""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # 1. Fetch the user by email first
    cur.execute("SELECT * FROM users WHERE email = %s;", (email,))
    user = cur.fetchone()
    
    if not user:
        cur.close()
        conn.close()
        return False, "Invalid Email or Recovery Key."
        
    # 2. Check if the typed recovery key matches the hashed key in the database
    if bcrypt.checkpw(raw_recovery_key.encode('utf-8'), user['recovery_key'].encode('utf-8')):
        
        # 3. Hash the new password
        new_hashed_bytes = bcrypt.hashpw(new_raw_password.encode('utf-8'), bcrypt.gensalt())
        new_password_hash = new_hashed_bytes.decode('utf-8')
        
        # 4. Update the database
        cur.execute("""
            UPDATE users 
            SET password_hash = %s 
            WHERE email = %s;
        """, (new_password_hash, email))
        
        conn.commit()
        cur.close()
        conn.close()
        return True, "Password successfully reset! You can now log in."
    else:
        cur.close()
        conn.close()
        return False, "Invalid Email or Recovery Key."