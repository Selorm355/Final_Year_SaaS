import streamlit as st
import auth  
import user_connection # Imports your new database manager

# --- Database Initialization ---
# This runs once when the app starts to ensure the users table exists
try:
    user_connection.init_db()
except Exception as e:
    st.error(f"Failed to connect to the database: {e}")

# Set page configuration
st.set_page_config(page_title="OmniPulse Analytics", page_icon="📊", layout="wide")

# Initialize session state for login tracking if it doesn't exist yet
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# Sidebar Navigation
st.sidebar.title("OmniPulse SaaS")
page = st.sidebar.radio("Navigation", [
    "1. Account Access", 
    "2. Data Ingestion", 
    "3. Processing Engine", 
    "4. Premium Dashboard"
])

# --- Page Routing ---
if page == "1. Account Access":
    auth.show_auth_page()

elif page == "2. Data Ingestion":
    st.title("📥 Upload Raw Data")
    if not st.session_state["logged_in"]:
        st.warning("⚠️ Please log in from the Account Access page first.")
    else:
        st.write(f"Welcome! Upload your standard CSV file for the **{st.session_state['industry']}** industry.")
        # File uploader will go here

elif page == "3. Processing Engine":
    st.title("⚙️ Clean & Process Data")
    if not st.session_state["logged_in"]:
        st.warning("⚠️ Please log in first.")
    else:
        st.write("Transform your raw data into analysis-ready format.")
        # dbt trigger will go here

elif page == "4. Premium Dashboard":
    st.title("📈 AI Forecasting & Analytics")
    if not st.session_state["logged_in"]:
        st.warning("⚠️ Please log in first.")
    else:
        st.write("Unlock premium insights and revenue predictions.")
        # Charts and AI logic will go here