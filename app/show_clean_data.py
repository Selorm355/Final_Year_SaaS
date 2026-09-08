import streamlit as st
import pandas as pd
import os
from sqlalchemy import create_engine
import navigation


def _preview_column_config(df):
    currency_terms = ("cost", "price", "revenue", "profit", "fee", "paid", "value", "cogs")
    column_config = {}

    for column in df.columns:
        if not pd.api.types.is_numeric_dtype(df[column]):
            continue

        column_name = column.lower()
        if any(term in column_name for term in currency_terms):
            number_format = "GH₵ %,.2f"
        elif pd.api.types.is_integer_dtype(df[column]):
            number_format = "%,d"
        else:
            number_format = "%,.2f"

        column_config[column] = st.column_config.NumberColumn(format=number_format)

    return column_config


def show_data_preview_page():
    navigation.render_back_button("Data Ingestion", "Data Ingestion")
    st.title("🗄️ Data Preview")

    if not st.session_state.get("logged_in"):
        st.warning("⚠️ Please log in to view your data preview.")
        return

    company_id = st.session_state["company_id"]
    industry = st.session_state["industry"].lower()

    st.write("Welcome to your Data Preview. Verify that your raw uploads have been successfully modeled by our engine.")

    try:
        pg_user = os.environ.get("POSTGRES_USER")
        pg_pass = os.environ.get("POSTGRES_PASSWORD")
        pg_db = os.environ.get("POSTGRES_DB")
        engine = create_engine(f"postgresql://{pg_user}:{pg_pass}@db:5432/{pg_db}")
    except Exception as e:
        st.error(f"🚨 Could not connect to the database: {e}")
        return

    st.markdown("### 🥇 Daily Business Metrics")
    st.caption("Your data aggregated into daily metrics. This powers your Premium Dashboard.")

    gold_query = f"SELECT * FROM gold.gold_{industry}_metrics WHERE company_id = '{company_id}' ORDER BY 2 DESC LIMIT 100"

    try:
        gold_df = pd.read_sql(gold_query, engine)
        if gold_df.empty:
            st.info("No metrics calculated yet. Please upload data in the Data Ingestion portal.")
        else:
            display_df = gold_df.drop(columns=['company_id'])
            st.dataframe(
                display_df,
                column_config=_preview_column_config(display_df),
                use_container_width=True
            )
    except Exception:
        st.error("Waiting for metrics to build...")

    st.divider()

    st.markdown("### 🥈 Audit Trail")
    with st.expander("🔍 View Individual Cleaned Transactions (Line-by-Line)"):
        st.caption("Your raw data with corrected data types, removed duplicates, and dropped invalid rows.")

        silver_query = f"SELECT * FROM silver.silver_{industry}_clean WHERE company_id = '{company_id}' ORDER BY 2 DESC LIMIT 100"

        try:
            silver_df = pd.read_sql(silver_query, engine)
            if silver_df.empty:
                st.info("No cleaned data found yet.")
            else:
                display_df = silver_df.drop(columns=['company_id'])
                st.dataframe(
                    display_df,
                    column_config=_preview_column_config(display_df),
                    use_container_width=True
                )
        except Exception:
            st.error("Waiting for clean records to build...")

    st.divider()
    st.markdown("<h3 style='text-align: center;'>🚀 Ready for Insights?</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Your data has been successfully mapped, cleaned, and warehoused. It is ready for AI analysis.</p>", unsafe_allow_html=True)

    st.write("")

    col1, col2, col3 = st.columns([1, 1.5, 1])

    with col2:
        if st.button("Generate Enterprise Dashboard", type="primary", use_container_width=True):
            st.session_state["active_page"] = "Premium Dashboard"
            st.session_state["sidebar_nav"] = "Premium Dashboard"
            st.rerun()