import streamlit as st
import pandas as pd
import os
from sqlalchemy import create_engine
import navigation

def show_data_preview_page():
    navigation.render_back_button("Data Ingestion", "Data Ingestion")
    st.title("🗄️ Data Preview")
    
    if not st.session_state.get("logged_in"):
        st.warning("⚠️ Please log in to view your data preview.")
        return

    company_id = st.session_state["company_id"]
    industry = st.session_state["industry"].lower() 
    
    st.write("Welcome to your Data Preview. Verify that your raw uploads have been successfully modeled by our engine.")

    # --- Database Connection ---
    try:
        pg_user = os.environ.get("POSTGRES_USER")
        pg_pass = os.environ.get("POSTGRES_PASSWORD")
        pg_db = os.environ.get("POSTGRES_DB")
        engine = create_engine(f"postgresql://{pg_user}:{pg_pass}@db:5432/{pg_db}")
    except Exception as e:
        st.error(f"🚨 Could not connect to the database: {e}")
        return

    # --- 1. Fetch & Display the Gold Layer (Front and Center) ---
    st.markdown("### 🥇 Daily Business Metrics")
    st.caption("Your data aggregated into daily metrics. This powers your Premium Dashboard.")
    
    gold_query = f"SELECT * FROM gold.gold_{industry}_metrics WHERE company_id = '{company_id}' ORDER BY 2 DESC LIMIT 100"
    
    try:
        gold_df = pd.read_sql(gold_query, engine)
        if gold_df.empty:
            st.info("No metrics calculated yet. Please upload data in the Data Ingestion portal.")
        else:
            st.dataframe(gold_df.drop(columns=['company_id']), use_container_width=True)
    except Exception as e:
        st.error(f"Waiting for metrics to build...")

    st.divider()

    # --- 2. Fetch & Display the Silver Layer (Hidden in an Expander for Auditing) ---
    st.markdown("### 🥈 Audit Trail")
    with st.expander("🔍 View Individual Cleaned Transactions (Line-by-Line)"):
        st.caption("Your raw data with corrected data types, removed duplicates, and dropped invalid rows.")
        
        silver_query = f"SELECT * FROM silver.silver_{industry}_clean WHERE company_id = '{company_id}' ORDER BY 2 DESC LIMIT 100"
        
        try:
            silver_df = pd.read_sql(silver_query, engine)
            if silver_df.empty:
                st.info("No cleaned data found yet.")
            else:
                st.dataframe(silver_df.drop(columns=['company_id']), use_container_width=True)
        except Exception as e:
            st.error(f"Waiting for clean records to build...")

    # --- 3. SEAMLESS UX ROUTING BUTTON ---
    st.divider()
    
    # Center-aligning the text using HTML injection
    st.markdown("<h3 style='text-align: center;'>🚀 Ready for Insights?</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Your data has been successfully mapped, cleaned, and warehoused. It is ready for AI analysis.</p>", unsafe_allow_html=True)
    
    st.write("") # Quick spacing
    
    # Using 3 columns to center the button perfectly
    col1, col2, col3 = st.columns([1, 1.5, 1])
    
    with col2:
        # use_container_width=True makes it fill the middle column beautifully
        if st.button("Generate Enterprise Dashboard", type="primary", use_container_width=True):
            st.session_state["active_page"] = "Premier Dashboard"
            st.rerun()