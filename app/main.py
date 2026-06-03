import streamlit as st

# --- 1. PAGE CONFIG MUST BE THE FIRST STREAMLIT COMMAND ---
st.set_page_config(page_title="OmniPulse Analytics", page_icon="📊", layout="wide")

import auth  
import user_connection 
import data_ingestion 
import show_clean_data # <-- NEW: Import your Data Preview page
import premium_dashboard # <-- this is the premiumdashbord import has nothing to do with medallion architecture, it is links the main.py to the premium_dashboard.py file where the premium dashboard is built.

# --- Database Initialization ---
try:
    user_connection.init_db()
except Exception as e:
    st.error(f"Failed to connect to the database: {e}")

# Initialize session state for login tracking
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# Initialize the default starting page for the remote control
if "sidebar_nav" not in st.session_state:
    st.session_state["sidebar_nav"] = "1. Account Access"

# Track the previous selected page so we can reset landing state only when navigating back to Account Access.
if "prev_sidebar_nav" not in st.session_state:
    st.session_state["prev_sidebar_nav"] = st.session_state["sidebar_nav"]

# --- NEW: THE TELEPORTATION INTERCEPTOR ---
# If a script asked us to change pages, do it BEFORE drawing the sidebar!
if "go_to_page" in st.session_state:
    st.session_state["sidebar_nav"] = st.session_state["go_to_page"]
    del st.session_state["go_to_page"] # Throw away the sticky note

# Sidebar Navigation (Now controlled by session_state!)
st.sidebar.title("OmniPulse SaaS")
page = st.sidebar.radio(
    "Navigation", 
    ["1. Account Access", "2. Data Ingestion", "3. Data Preview", "4. Premium Dashboard"],
    key="sidebar_nav" # <-- THIS is the remote control
)

# --- Page Routing ---
if page == "1. Account Access":
    # Reset to the landing auth screen when the user navigates back to Account Access
    # from another page, so the Log In / Register buttons are visible again.
    if st.session_state.get("prev_sidebar_nav") != "1. Account Access":
        st.session_state["auth_screen"] = "landing"
    auth.show_auth_page()

elif page == "2. Data Ingestion":
    data_ingestion.show_ingestion_page()

elif page == "3. Data Preview":
    show_clean_data.show_data_preview_page()

elif page == "4. Premium Dashboard":
    # Hand control over to the Traffic Cop!
    premium_dashboard.show_dashboard()

st.session_state["prev_sidebar_nav"] = page