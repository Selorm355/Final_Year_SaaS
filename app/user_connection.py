import os
import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt

# --- 1. THE BRIDGE (Connection Setup) ---
def get_connection():
    """Establishes a connection to the PostgreSQL database container."""
    # Notice the host is "db" (the name of your service in docker-compose)
    # and the port is 5432 (the internal Docker port, not your external 5442)
    return psycopg2.connect(
        host="db",
        port="5432",
        database=os.environ.get("POSTGRES_DB"),
        user=os.environ.get("POSTGRES_USER"),
        password=os.environ.get("POSTGRES_PASSWORD")
    )

# --- 2. THE SELF-HEALING INIT (Option B) ---
def init_db():
    """Runs when the app starts. Creates the users table if it doesn't exist."""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            company_id SERIAL PRIMARY KEY,
            company_name VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            industry VARCHAR(50) NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    conn.commit()
    cur.close()
    conn.close()

# --- 3. THE REGISTRATION LOGIC ---
def register_user(company_name, email, industry, raw_password):
    """Hashes the password and saves the new company into the database."""
    # 1. Scramble the password using bcrypt
    hashed_bytes = bcrypt.hashpw(raw_password.encode('utf-8'), bcrypt.gensalt())
    password_hash = hashed_bytes.decode('utf-8')
    
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        # 2. Insert into the database
        cur.execute("""
            INSERT INTO users (company_name, email, industry, password_hash)
            VALUES (%s, %s, %s, %s)
            RETURNING company_id;
        """, (company_name, email, industry, password_hash))
        
        new_id = cur.fetchone()[0]
        conn.commit()
        return True, "Registration successful!"
        
    except psycopg2.errors.UniqueViolation:
        # If the email already exists, Postgres throws a UniqueViolation error
        conn.rollback()
        return False, "This email is already registered."
    finally:
        cur.close()
        conn.close()

# --- 4. THE LOGIN LOGIC ---
def authenticate_user(email, raw_password):
    """Checks if the email exists and if the passwords match."""
    conn = get_connection()
    # RealDictCursor makes the output look like a Python dictionary, making it easy to read
    cur = conn.cursor(cursor_factory=RealDictCursor) 
    
    cur.execute("SELECT * FROM users WHERE email = %s;", (email,))
    user = cur.fetchone()
    
    cur.close()
    conn.close()
    
    # If user doesn't exist
    if not user:
        return False, None
        
    # Check if the typed password matches the scrambled password in the database
    if bcrypt.checkpw(raw_password.encode('utf-8'), user['password_hash'].encode('utf-8')):
        # Success! Return the user data so Streamlit can save it in Session State
        return True, user
    else:
        # Passwords don't match
        return False, None