import streamlit as st
import pandas as pd
import os
from sqlalchemy import create_engine

def show_data_preview_page():
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
                display_df = silver_df.copy()
                if 'quantity' in display_df.columns and 'unit_price' in display_df.columns:
                    quantities = pd.to_numeric(display_df['quantity'], errors='coerce')
                    unit_prices = pd.to_numeric(display_df['unit_price'], errors='coerce')
                    display_df['total'] = quantities * unit_prices
                    display_df['unit_price'] = unit_prices.apply(
                        lambda x: f"GH₵ {x:,.2f}" if pd.notna(x) else ""
                    )
                    display_df['quantity'] = quantities.apply(
                        lambda x: f"{int(x):,}" if pd.notna(x) else ""
                    )
                    display_df['total'] = display_df['total'].apply(
                        lambda x: f"GH₵ {x:,.2f}" if pd.notna(x) else ""
                    )
                    cols = list(display_df.columns)
                    # Move the new total column right after unit_price if it exists
                    if 'total' in cols and 'unit_price' in cols:
                        cols.insert(cols.index('unit_price') + 1, cols.pop(cols.index('total')))
                        display_df = display_df[cols]
                st.dataframe(display_df.drop(columns=['company_id']), use_container_width=True)
        except Exception as e:
            st.error(f"Waiting for clean records to build...")