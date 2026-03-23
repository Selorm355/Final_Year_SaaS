import streamlit as st
import pandas as pd
import plotly.express as px
import os 
import ai_forecasting
from sqlalchemy import create_engine
from dotenv import load_dotenv

# --- Database Connection ---
load_dotenv()
pg_user = os.environ.get("POSTGRES_USER")
pg_pass = os.environ.get("POSTGRES_PASSWORD")
pg_db = os.environ.get("POSTGRES_DB")

# Connect to the database (Using the Docker 'db' host)
engine = create_engine(f"postgresql://{pg_user}:{pg_pass}@db:5432/{pg_db}")

def fetch_retail_data():
    """Fetches the clean data from the database."""
    # We query the Silver layer here so we have access to both the dates AND the specific item names
    query = """
        SELECT 
            transaction_date, 
            receipt_id, 
            item_name, 
            quantity, 
            unit_price,
            (quantity * unit_price) AS total_sale_value
        FROM silver.silver_retail_clean
    """
    df = pd.read_sql(query, engine)
    # Ensure transaction_date is a proper datetime object for Pandas to group
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])
    return df

def render_dashboard(company_id):
    """The main function called by the Traffic Cop."""
    
    # 1. LOAD DATA
    with st.spinner("Crunching your retail metrics..."):
        try:
            df = fetch_retail_data()
        except Exception as e:
            st.error("⚠️ Could not load dashboard data. Please ensure you have ingested data first.")
            return

    if df.empty:
        st.info("No retail data found. Please upload your raw data in the Data Ingestion tab.")
        return

    # 2. THE TIME TOGGLE (Day / Week / Month)
    st.subheader("⏱️ Revenue Trends")
    time_grouping = st.radio(
        "Group Data By:", 
        options=["Day", "Week", "Month"], 
        horizontal=True
    )

    # 3. DATA AGGREGATION LOGIC
    # We set the date as the index so Pandas can do its time-traveling magic
    df_time = df.set_index('transaction_date')
    
    if time_grouping == "Day":
        trend_df = df_time.resample('D').agg({'total_sale_value': 'sum', 'quantity': 'sum'}).reset_index()
    elif time_grouping == "Week":
        # 'W-MON' means group by week, starting on Monday
        trend_df = df_time.resample('W-MON').agg({'total_sale_value': 'sum', 'quantity': 'sum'}).reset_index()
    else: # Month
        # 'ME' means Month End
        trend_df = df_time.resample('ME').agg({'total_sale_value': 'sum', 'quantity': 'sum'}).reset_index()
        
    # Drop any periods where there were absolutely zero sales to keep the chart clean
    trend_df = trend_df[trend_df['total_sale_value'] > 0]

    # 4. TOP ROW: EXECUTIVE KPI CARDS
    total_revenue = df['total_sale_value'].sum()
    total_items = df['quantity'].sum()
    total_transactions = df['receipt_id'].nunique()
    aov = total_revenue / total_transactions if total_transactions > 0 else 0

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Revenue", f"GH₵ {total_revenue:,.2f}")
    with col2:
        st.metric("Total Items Sold", f"{total_items:,}")
    with col3:
        st.metric("Average Order Value", f"GH₵ {aov:,.2f}")

    st.divider()

    # 5. MIDDLE ROW: THE MAIN TIME-SERIES CHART
    st.divider()
    col_chart_title, col_ai_toggle = st.columns([3, 1])
    
    with col_chart_title:
        st.subheader("⏱️ Revenue Trends & AI Prediction")
    with col_ai_toggle:
        # The cool SaaS toggle switch
        enable_ai = st.toggle("🤖 Enable AI Forecast")

    if enable_ai:
        with st.spinner("AI is analyzing historical trends to predict the future..."):
            # Set how far into the future to look based on their grouping
            if time_grouping == "Day":
                periods, freq_code = 7, 'D'    # Predict next 7 days
            elif time_grouping == "Week":
                periods, freq_code = 4, 'W'    # Predict next 4 weeks
            else:
                periods, freq_code = 3, 'M'    # Predict next 3 months

            # Call our agnostic brain!
            plot_df = ai_forecasting.generate_forecast(
                trend_df, 
                date_col='transaction_date', 
                metric_col='total_sale_value',
                forecast_periods=periods,
                freq=freq_code
            )
            
            # Plotly Line Chart showing historical vs predicted
            fig_trend = px.line(
                plot_df, 
                x='transaction_date', 
                y='predicted_value',
                color='Type',
                line_dash='Type', # Makes the forecast line dotted!
                color_discrete_map={'Historical Data': '#00b4d8', 'Forecast (AI)': '#ff9f1c'},
                labels={'transaction_date': 'Date', 'predicted_value': 'Revenue (GH₵)'}
            )
            
    else:
        # Standard Area Chart (No AI)
        fig_trend = px.area(
            trend_df, 
            x='transaction_date', 
            y='total_sale_value',
            labels={'transaction_date': 'Date', 'total_sale_value': 'Revenue (GH₵)'},
            color_discrete_sequence=['#00b4d8'] 
        )

    fig_trend.update_traces(hovertemplate="<b>Date:</b> %{x}<br><b>Revenue:</b> GH₵ %{y:,.2f}<extra></extra>")
    fig_trend.update_layout(xaxis_title="", yaxis_title="")
    st.plotly_chart(fig_trend, use_container_width=True)
    st.divider()

    # 6. BOTTOM ROW: PRODUCT BREAKDOWN
    st.subheader("🛍️ Product Performance")
    
    # Calculate best sellers by Revenue
    top_products = df.groupby('item_name').agg(
        revenue=('total_sale_value', 'sum'),
        volume=('quantity', 'sum')
    ).reset_index().sort_values(by='revenue', ascending=False).head(10)

    col_left, col_right = st.columns(2)

    with col_left:
        # Horizontal Bar Chart for Top 10 Best Sellers
        fig_bar = px.bar(
            top_products.sort_values(by='revenue', ascending=True), # Sort ascending so the biggest is on top in Plotly
            x='revenue', 
            y='item_name', 
            orientation='h',
            title="Top 10 Best Sellers (by Revenue)",
            labels={'revenue': 'Revenue (GH₵)', 'item_name': ''},
            color_discrete_sequence=['#ff9f1c'] # A nice energetic orange
        )
        fig_bar.update_traces(hovertemplate="<b>%{y}</b><br>Revenue: GH₵ %{x:,.2f}<extra></extra>")
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_right:
        # Donut Chart for Revenue Share
        fig_donut = px.pie(
            top_products, 
            values='revenue', 
            names='item_name', 
            hole=0.4, # This makes it a donut instead of a pie
            title="Revenue Share Breakdown"
        )
        fig_donut.update_traces(textinfo='percent', hovertemplate="<b>%{label}</b><br>Revenue: GH₵ %{value:,.2f}<extra></extra>")
        st.plotly_chart(fig_donut, use_container_width=True)