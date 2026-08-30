import streamlit as st
import json
import os
from cryptography.fernet import Fernet 

# --- 1. PAGE CONFIG ---
st.set_page_config(
    page_title="OmniPulse Analytics", 
    page_icon="📊", 
    layout="wide",
    initial_sidebar_state="expanded"
)

import auth  
import user_connection 
import data_ingestion 
import show_clean_data 
import premium_dashboard 

# --- ENCRYPTION SETUP ---
fernet_secret = os.getenv("FERNET_KEY")
if not fernet_secret:
    st.error("CRITICAL CONFIG ERROR: FERNET_KEY is missing from environment variables. Check your .env file.")
    st.stop()

FERNET_KEY = fernet_secret.encode()
cipher_suite = Fernet(FERNET_KEY)

# --- Database Initialization ---
try:
    user_connection.init_db()
except Exception as e:
    st.error(f"Failed to connect to the database: {e}")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# --- 2. THE SECURE TOKEN HYDRATOR ---
if not st.session_state["logged_in"] and "token" in st.query_params:
    try:
        encrypted_token = st.query_params["token"]
        decrypted_bytes = cipher_suite.decrypt(encrypted_token.encode())
        session_data = json.loads(decrypted_bytes.decode())
        
        st.session_state["logged_in"] = True
        st.session_state["company_id"] = session_data["company_id"]
        st.session_state["industry"] = session_data["industry"]
        st.session_state["company_name"] = session_data["company_name"]
        st.session_state["user"] = session_data
        
        st.session_state["go_to_page"] = "Data Ingestion"
        
        st.query_params.clear()
    except Exception:
        pass 

if "prev_sidebar_nav" not in st.session_state:
    st.session_state["prev_sidebar_nav"] = "Account Access"

if "go_to_page" in st.session_state:
    st.session_state["sidebar_nav"] = st.session_state["go_to_page"]
    del st.session_state["go_to_page"] 

# --- 3. DYNAMIC UI CONTROLLER ---
ui_container = st.empty()

if not st.session_state["logged_in"]:
    # 🔒 LOGGED OUT STATE
    page = "Account Access"
    st.session_state["sidebar_nav"] = page
    
    # Hide the sidebar and toggle arrow on the auth page
    ui_container.markdown("""
        <style>
            [data-testid="stSidebar"] { display: none !important; }
            [data-testid="collapsedControl"] { display: none !important; }
        </style>
    """, unsafe_allow_html=True)
    
else:
    # 🔓 LOGGED IN STATE
    ui_container.empty() # Clear the CSS so arrows and sidebar appear natively
    st.sidebar.title("OmniPulse SaaS")
    
    # Clean menu with Account Access included and numbers removed
    nav_options = ["Account Access", "Data Ingestion", "Data Preview", "Premium Dashboard", "Logout"]
    
    if st.session_state.get("sidebar_nav") not in nav_options:
        st.session_state["sidebar_nav"] = "Data Ingestion"
        
    page = st.sidebar.radio("Navigation", nav_options, key="sidebar_nav")

# --- 4. SECURE PAGE ROUTING ---
if page == "Account Access":
    if st.session_state.get("prev_sidebar_nav") != "Account Access":
        st.session_state["auth_screen"] = "landing"
    auth.show_auth_page()

elif page == "Data Ingestion":
    data_ingestion.show_ingestion_page()

elif page == "Data Preview":
    show_clean_data.show_data_preview_page()

elif page == "Premium Dashboard":
    premium_dashboard.render_dashboard_gatekeeper()

elif page == "Logout":
    st.session_state.clear()
    st.query_params.clear()
    st.rerun()

st.session_state["prev_sidebar_nav"] = page