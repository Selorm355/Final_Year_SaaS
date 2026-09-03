import streamlit as st
import json
import os
from cryptography.fernet import Fernet

# 1. PAGE CONFIG
st.set_page_config(
    page_title="OmniPulse Analytics",
    page_icon="🪐",
    layout="wide",
    initial_sidebar_state="expanded",
)

import auth
import user_connection
import data_ingestion
import show_clean_data
import premium_dashboard
import navigation

# --- ENCRYPTION SETUP ---
fernet_secret = os.getenv("FERNET_KEY")
if not fernet_secret:
    st.error("🚨 CRITICAL CONFIG ERROR: FERNET_KEY is missing from environment variables.")
    st.stop()

FERNET_KEY = fernet_secret.encode()
cipher_suite = Fernet(FERNET_KEY)

# --- DATABASE INITIALIZATION ---
try:
    user_connection.init_db()
except Exception as e:
    st.error(f"Failed to connect to the database: {e}")

# Session State defaults
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "active_page" not in st.session_state:
    st.session_state["active_page"] = "Data Ingestion"

if "sidebar_nav" not in st.session_state:
    st.session_state["sidebar_nav"] = "Data Ingestion"

# --- TOKEN HYDRATOR ---
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
        st.session_state["active_page"] = "Data Ingestion"
        st.session_state["sidebar_nav"] = "Data Ingestion"
        st.query_params.clear()
    except Exception:
        pass

# --- ROUTER LOGIC ---
if "go_to_page" in st.session_state:
    target = st.session_state["go_to_page"]
    if target == "2. Data Ingestion":
        target = "Data Ingestion"
    st.session_state["active_page"] = target
    st.session_state["sidebar_nav"] = target
    del st.session_state["go_to_page"]

# Condition A: Not logged in -> Show Landing / Login / Register (No Sidebar)
if not st.session_state["logged_in"]:
    st.markdown("""
        <style>
            [data-testid="stSidebar"] {display: none;}
            [data-testid="collapsedControl"] { display: none !important; }
        </style>
    """, unsafe_allow_html=True)
    auth.show_auth_page()

# Condition B: Logged In -> Apply Theme & Persistent Orbit Sidebar
else:
    navigation.inject_global_theme()
    navigation.render_authenticated_sidebar()

    current_page = st.session_state.get("active_page", st.session_state.get("sidebar_nav", "Data Ingestion"))

    if current_page == "Account Access":
        auth.show_user_profile()
    elif current_page == "Data Ingestion":
        data_ingestion.show_ingestion_page()
    elif current_page == "Data Preview":
        show_clean_data.show_data_preview_page()
    elif current_page == "Premium Dashboard":
        premium_dashboard.render_dashboard_gatekeeper()