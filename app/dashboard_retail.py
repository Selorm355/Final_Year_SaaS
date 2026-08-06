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
            unit_price_ghs,
            total_profit_ghs,
            (quantity * unit_price_ghs) AS total_sale_value
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
            st.error(f"⚠️ CRASH DETAILS: {e}")
            return

    if df.empty:
        st.info("No retail data found. Please upload your raw data in the Data Ingestion tab.")
        return

    # --- ADVANCED METRICS CALCULATION ---
    total_revenue = df['total_sale_value'].sum()
    total_profit = df['total_profit_ghs'].sum()
    gross_margin = (total_profit / total_revenue) * 100 if total_revenue > 0 else 0
    
    total_items = df['quantity'].sum()
    total_transactions = df['receipt_id'].nunique()
    
    aov = total_revenue / total_transactions if total_transactions > 0 else 0
    basket_size = total_items / total_transactions if total_transactions > 0 else 0

    # --- TOP ROW: EXECUTIVE KPI CARDS ---
    st.markdown("### 📊 Enterprise Retail Command Center")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Revenue", f"GH₵ {total_revenue:,.0f}")
    with col2:
        st.metric("Gross Profit", f"GH₵ {total_profit:,.0f}")
    with col3:
        st.metric("Margin", f"{gross_margin:.1f}%")
    with col4:
        st.metric("Avg Order Value", f"GH₵ {aov:,.2f}")
    with col5:
        st.metric("Avg Basket Size", f"{basket_size:.1f} items")

    st.divider()

    # --- SAAS TABBED LAYOUT (Now with 4 Tabs!) ---
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Executive Overview", 
        "🛍️ Product Intelligence", 
        "💰 Profitability Analysis",
        "📅 Operational Intelligence"
    ])

    # === TAB 1: EXECUTIVE OVERVIEW ===
    with tab1:
        col_chart_title, col_toggle, col_ai = st.columns([2, 1, 1])
        with col_chart_title:
            time_grouping = st.radio("Group Data By:", options=["Day", "Week", "Month"], horizontal=True)
        with col_ai:
            enable_ai = st.toggle("🤖 Enable AI Forecast")

        df_time = df.set_index('transaction_date')
        if time_grouping == "Day":
            trend_df = df_time.resample('D').agg({'total_sale_value': 'sum', 'total_profit_ghs': 'sum'}).reset_index()
            periods, freq_code = 7, 'D'
        elif time_grouping == "Week":
            trend_df = df_time.resample('W-MON').agg({'total_sale_value': 'sum', 'total_profit_ghs': 'sum'}).reset_index()
            periods, freq_code = 4, 'W'
        else:
            trend_df = df_time.resample('ME').agg({'total_sale_value': 'sum', 'total_profit_ghs': 'sum'}).reset_index()
            periods, freq_code = 3, 'M'
            
        trend_df = trend_df[trend_df['total_sale_value'] > 0]

        if enable_ai:
            with st.spinner("AI is analyzing historical trends to predict the future..."):
                plot_df = ai_forecasting.generate_forecast(
                    trend_df, date_col='transaction_date', metric_col='total_sale_value', forecast_periods=periods, freq=freq_code
                )
                fig_trend = px.line(
                    plot_df, x='transaction_date', y='predicted_value', color='Type', line_dash='Type',
                    color_discrete_map={'Historical Data': '#00b4d8', 'Forecast (AI)': '#ff9f1c'},
                    labels={'transaction_date': 'Date', 'predicted_value': 'Revenue (GH₵)'}
                )
        else:
            fig_trend = px.area(
                trend_df, x='transaction_date', y='total_sale_value',
                labels={'transaction_date': 'Date', 'total_sale_value': 'Revenue (GH₵)'},
                color_discrete_sequence=['#00b4d8'] 
            )

        fig_trend.update_traces(hovertemplate="<b>Date:</b> %{x}<br><b>Revenue:</b> GH₵ %{y:,.2f}<extra></extra>")
        fig_trend.update_layout(xaxis_title="", yaxis_title="")
        st.plotly_chart(fig_trend, use_container_width=True)

    # === TAB 2: PRODUCT INTELLIGENCE ===
    with tab2:
        top_products = df.groupby('item_name').agg(
            revenue=('total_sale_value', 'sum'),
            volume=('quantity', 'sum'),
            profit=('total_profit_ghs', 'sum')
        ).reset_index().sort_values(by='revenue', ascending=False)
        
        # Apply the cap gracefully 
        top_10_products = top_products.head(10)

        col_left, col_right = st.columns(2)
        with col_left:
            fig_bar = px.bar(
                top_10_products.sort_values(by='revenue', ascending=True), 
                x='revenue', y='item_name', orientation='h', 
                title="Top Revenue Drivers", # Dynamic title
                labels={'revenue': 'Revenue (GH₵)', 'item_name': ''}, color_discrete_sequence=['#ff9f1c']
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_right:
            fig_donut = px.pie(
                top_10_products, values='volume', names='item_name', hole=0.4, 
                title="Quantity Sold (Top Products)" # Dynamic title
            )
            st.plotly_chart(fig_donut, use_container_width=True)
            
        st.subheader("Deep Dive: Top Products Roster")
        st.dataframe(
            top_10_products,
            column_config={
                "item_name": st.column_config.TextColumn("Product Name"),
                "revenue": st.column_config.ProgressColumn("Total Revenue (GH₵)", format="GH₵ %f", min_value=0, max_value=float(top_products['revenue'].max())),
                "volume": st.column_config.NumberColumn("Units Sold"),
                "profit": st.column_config.NumberColumn("Total Profit (GH₵)", format="GH₵ %f")
            },
            hide_index=True,
            use_container_width=True
        )

    # === TAB 3: PROFITABILITY ANALYSIS ===
    with tab3:
        st.subheader("Margin & Absolute Profitability Analysis")
        
        top_products['margin_pct'] = (top_products['profit'] / top_products['revenue']) * 100
        all_margin_items = top_products.sort_values(by='margin_pct', ascending=False)
        
        st.markdown("Analyze the relationship between percentage margins and absolute cash profit across **all products**.")
        
        col_matrix, col_bar = st.columns(2)
        
        with col_bar:
            # Removed the .head(10) cap so it shows ALL products
            fig_margin = px.bar(
                all_margin_items.sort_values(by='margin_pct', ascending=True),
                x='margin_pct', 
                y='item_name', 
                orientation='h',
                title="Product Profitability Ranking (All Items)",
                labels={'margin_pct': 'Margin (%)', 'item_name': ''},
                color_discrete_sequence=['#2ec4b6'],
                text='profit'
            )
            fig_margin.update_traces(
                texttemplate='GH₵ %{text:,.0f}', 
                textposition='inside',
                insidetextanchor='middle',
                hovertemplate="<b>%{y}</b><br>Margin: %{x:.1f}%<br>Absolute Profit: GH₵ %{text:,.2f}<extra></extra>"
            )
            # Increased height to 800 so 30+ product labels don't overlap
            fig_margin.update_layout(height=800)
            st.plotly_chart(fig_margin, use_container_width=True)

        with col_matrix:
            # Scatter plot is already UNCAPPED, just matching the new height!
            fig_scatter = px.scatter(
                all_margin_items,
                x='margin_pct',
                y='profit',
                size='revenue',
                color='margin_pct',
                hover_name='item_name',
                title="The Profitability Matrix (All Products)",
                labels={'margin_pct': 'Profit Margin (%)', 'profit': 'Total Absolute Profit (GH₵)'},
                color_continuous_scale="Teal"
            )
            fig_scatter.update_traces(
                hovertemplate="<b>%{hovertext}</b><br>Margin: %{x:.1f}%<br>Absolute Profit: GH₵ %{y:,.2f}<br>Total Revenue: GH₵ %{marker.size:,.2f}<extra></extra>"
            )
            fig_scatter.update_layout(height=800) # Matched height with the bar chart
            st.plotly_chart(fig_scatter, use_container_width=True) 
    
    # === TAB 4: OPERATIONAL INTELLIGENCE ===
    with tab4:
        st.subheader("Traffic & Basket Analysis")
        col_day, col_basket = st.columns(2)
        
        with col_day:
            # Extract day of the week from the transaction_date
            df['day_of_week'] = df['transaction_date'].dt.day_name()
            # Enforce chronological ordering for the chart
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            day_stats = df.groupby('day_of_week')['total_sale_value'].sum().reindex(day_order).reset_index()
            day_stats['total_sale_value'] = day_stats['total_sale_value'].fillna(0)
            
            fig_day = px.bar(
                day_stats, x='day_of_week', y='total_sale_value',
                title="Revenue by Day of the Week",
                labels={'day_of_week': '', 'total_sale_value': 'Revenue (GH₵)'},
                color_discrete_sequence=['#8338ec'] # Vibrant Purple
            )
            st.plotly_chart(fig_day, use_container_width=True)
            
        with col_basket:
            # Calculate exactly how many items were bought in each specific receipt
            basket_sizes = df.groupby('receipt_id')['quantity'].sum().reset_index()
            
            fig_basket = px.histogram(
                basket_sizes, x='quantity',
                title="Basket Size Distribution",
                labels={'quantity': 'Items per Transaction'},
                color_discrete_sequence=['#ff006e'], # Punchy Pink
                nbins=15
            )
            fig_basket.update_layout(yaxis_title="Number of Transactions")
            st.plotly_chart(fig_basket, use_container_width=True)