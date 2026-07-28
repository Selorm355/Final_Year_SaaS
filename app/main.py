import streamlit as st
import json
import os
from cryptography.fernet import Fernet 

# --- 1. PAGE CONFIG MUST BE THE FIRST STREAMLIT COMMAND ---
st.set_page_config(page_title="OmniPulse Analytics", page_icon="📊", layout="wide")

import auth  
import user_connection 
import data_ingestion 
import show_clean_data 
import premium_dashboard 

# --- ENCRYPTION SETUP ---
# Pulling the secret key securely from the environment variable
fernet_secret = os.getenv("FERNET_KEY")
if not fernet_secret:
    st.error("🚨 CRITICAL CONFIG ERROR: FERNET_KEY is missing from environment variables. Check your .env file.")
    st.stop()

FERNET_KEY = fernet_secret.encode() # Convert string from .env to bytes for Fernet
cipher_suite = Fernet(FERNET_KEY)

# --- Database Initialization ---
try:
    user_connection.init_db()
except Exception as e:
    st.error(f"Failed to connect to the database: {e}")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# --- 2. THE SECURE TOKEN HYDRATOR ---
# Instantly reads the URL, decrypts the token, and hydrates the session
if not st.session_state["logged_in"] and "token" in st.query_params:
    try:
        encrypted_token = st.query_params["token"]
        
        # 🚨 Decrypt the payload before reading it!
        decrypted_bytes = cipher_suite.decrypt(encrypted_token.encode())
        session_data = json.loads(decrypted_bytes.decode())
        
        st.session_state["logged_in"] = True
        st.session_state["company_id"] = session_data["company_id"]
        st.session_state["industry"] = session_data["industry"]
        st.session_state["company_name"] = session_data["company_name"]
        
        # Hydrate the full user dictionary so the Paywall Gatekeeper can read it!
        st.session_state["user"] = session_data
        
        # Route them safely to the dashboard upon refresh
        st.session_state["go_to_page"] = "2. Data Ingestion"
    except Exception:
        # If the token was tampered with, Fernet throws an InvalidToken exception.
        # We silently fail and leave them logged out.
        pass 

# Initialize the default starting page
if "sidebar_nav" not in st.session_state:
    st.session_state["sidebar_nav"] = "1. Account Access"

if "prev_sidebar_nav" not in st.session_state:
    st.session_state["prev_sidebar_nav"] = st.session_state["sidebar_nav"]

# --- THE TELEPORTATION INTERCEPTOR ---
if "go_to_page" in st.session_state:
    st.session_state["sidebar_nav"] = st.session_state["go_to_page"]
    del st.session_state["go_to_page"] 

# Sidebar Navigation
st.sidebar.title("OmniPulse SaaS")
page = st.sidebar.radio(
    "Navigation", 
    ["1. Account Access", "2. Data Ingestion", "3. Data Preview", "4. Premium Dashboard"],
    key="sidebar_nav" 
)

# --- Page Routing ---
if page == "1. Account Access":
    if st.session_state.get("prev_sidebar_nav") != "1. Account Access":
        st.session_state["auth_screen"] = "landing"
    auth.show_auth_page()

elif page == "2. Data Ingestion":
    data_ingestion.show_ingestion_page()

elif page == "3. Data Preview":
    show_clean_data.show_data_preview_page()

# 🚨 UPDATED: Now points to the Trial & Paywall Gatekeeper!
elif page == "4. Premium Dashboard":
    premium_dashboard.render_dashboard_gatekeeper()

st.session_state["prev_sidebar_nav"] = page