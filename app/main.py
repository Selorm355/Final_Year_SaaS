import streamlit as st
import auth  
import user_connection 
import data_ingestion # --- NEW: Import your ingestion script

# --- Database Initialization ---
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
    # The data_ingestion script handles its own title and login warnings!
    data_ingestion.show_ingestion_page()

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