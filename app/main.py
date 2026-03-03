import streamlit as st

# Set page configuration
st.set_page_config(page_title="OmniPulse Analytics", page_icon="📊", layout="wide")

# Sidebar Navigation
st.sidebar.title("OmniPulse SaaS")
page = st.sidebar.radio("Navigation", ["1. Authentication", "2. Data Ingestion", "3. Processing Engine", "4. Premium Dashboard"])

# --- Page Routing ---
if page == "1. Authentication":
    st.title("🔐 Login / Register")
    st.write("Welcome! Please log in or register your company to continue.")
    # We will build the login form here next

elif page == "2. Data Ingestion":
    st.title("📥 Upload Raw Data")
    st.write("Upload your standard CSV file based on your industry (Retail, Telecom, Healthcare).")
    # We will build the Pandas validation and DB upload here

elif page == "3. Processing Engine":
    st.title("⚙️ Clean & Process Data")
    st.write("Transform your raw data into analysis-ready format.")
    # We will add the dbt trigger button here

elif page == "4. Premium Dashboard":
    st.title("📈 AI Forecasting & Analytics")
    st.write("Unlock premium insights and revenue predictions.")
    # We will add the Paystack logic and Scikit-Learn charts here