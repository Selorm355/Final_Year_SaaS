import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Optional forecast module import
try:
    import ai_forecasting
except ImportError:
    ai_forecasting = None

# --- Page Config ---
st.set_page_config(
    page_title="OmniPulse Analytics",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Modern Orbit UI CSS Injection ---
CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }

    /* Overall App Background */
    .stApp {
        background-color: #EDF1F7 !important;
        color: #1E2530 !important;
    }

    /* Main Container Padding */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2.5rem !important;
        max-width: 1350px !important;
    }

    /* Custom KPI Metric Cards */
    .orbit-card {
        background: #FFFFFF;
        border-radius: 22px;
        padding: 20px 24px;
        box-shadow: 0 8px 24px rgba(149, 157, 165, 0.08);
        border: 1px solid rgba(230, 235, 245, 0.8);
        transition: transform 0.15s ease-in-out;
    }
    .orbit-card:hover {
        transform: translateY(-2px);
    }
    .orbit-label {
        font-size: 0.82rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        color: #8C98A9;
        margin-bottom: 8px;
    }
    .orbit-value {
        font-size: 1.65rem;
        font-weight: 700;
        color: #121826;
        letter-spacing: -0.5px;
    }
    .orbit-badge {
        display: inline-block;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 3px 8px;
        border-radius: 12px;
        margin-top: 6px;
    }
    .badge-positive {
        background: #E8F8F0;
        color: #0E9F6E;
    }

    /* Chart Containers */
    .orbit-chart-card {
        background: #FFFFFF;
        border-radius: 24px;
        padding: 24px;
        box-shadow: 0 8px 24px rgba(149, 157, 165, 0.08);
        border: 1px solid rgba(230, 235, 245, 0.8);
        margin-bottom: 1.5rem;
    }
    .chart-header {
        font-size: 1.15rem;
        font-weight: 700;
        color: #121826;
        margin-bottom: 4px;
    }
    .chart-subtitle {
        font-size: 0.82rem;
        color: #8C98A9;
        margin-bottom: 16px;
    }

    /* Style Streamlit Tabs to match soft pill design */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #E2E8F0;
        padding: 6px;
        border-radius: 16px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 12px;
        padding: 8px 18px;
        font-weight: 600;
        font-size: 0.88rem;
        color: #64748B;
        border: none !important;
        background: transparent !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
    }
    
    /* Clean up dataframe display */
    [data-testid="stDataFrame"] {
        border-radius: 16px;
        overflow: hidden;
        border: 1px solid #E2E8F0;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# --- Database Connection ---
load_dotenv()
pg_user = os.environ.get("POSTGRES_USER", "postgres")
pg_pass = os.environ.get("POSTGRES_PASSWORD", "postgres")
pg_db = os.environ.get("POSTGRES_DB", "postgres")

engine = create_engine(f"postgresql://{pg_user}:{pg_pass}@db:5432/{pg_db}")

def fetch_retail_data():
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
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])
    return df

def render_dashboard(company_id=None):
    with st.spinner("Crunching your retail intelligence..."):
        try:
            df = fetch_retail_data()
        except Exception as e:
            st.error(f"⚠️ Could not load data: {e}")
            return

    if df.empty:
        st.info("No retail data found. Please upload records in the Ingestion tab.")
        return

    # --- Calculations ---
    total_revenue = df['total_sale_value'].sum()
    total_profit = df['total_profit_ghs'].sum()
    gross_margin = (total_profit / total_revenue) * 100 if total_revenue > 0 else 0
    total_items = df['quantity'].sum()
    total_transactions = df['receipt_id'].nunique()
    aov = total_revenue / total_transactions if total_transactions > 0 else 0
    basket_size = total_items / total_transactions if total_transactions > 0 else 0

    # --- Top Navigation Header ---
    c_title, c_user = st.columns([4, 1])
    with c_title:
        st.markdown("<h2 style='font-weight:700; color:#121826; margin-bottom: 0;'>Enterprise Retail Command Center</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color:#8C98A9; font-size:0.9rem; margin-top:2px;'>Real-time metrics, unit economics, and performance insights</p>", unsafe_allow_html=True)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # --- 5 KPI Card Section ---
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    
    with kpi1:
        st.markdown(f"""
            <div class="orbit-card">
                <div class="orbit-label">Total Revenue</div>
                <div class="orbit-value">GH₵ {total_revenue:,.0f}</div>
                <div class="orbit-badge badge-positive">↑ Active Growth</div>
            </div>
        """, unsafe_allow_html=True)
    with kpi2:
        st.markdown(f"""
            <div class="orbit-card">
                <div class="orbit-label">Gross Profit</div>
                <div class="orbit-value">GH₵ {total_profit:,.0f}</div>
                <div class="orbit-badge badge-positive">Net Margin Solid</div>
            </div>
        """, unsafe_allow_html=True)
    with kpi3:
        st.markdown(f"""
            <div class="orbit-card">
                <div class="orbit-label">Gross Margin</div>
                <div class="orbit-value">{gross_margin:.1f}%</div>
                <div class="orbit-badge badge-positive">Target: >30%</div>
            </div>
        """, unsafe_allow_html=True)
    with kpi4:
        st.markdown(f"""
            <div class="orbit-card">
                <div class="orbit-label">Avg Order Value</div>
                <div class="orbit-value">GH₵ {aov:,.1f}</div>
                <div class="orbit-badge badge-positive">Per Receipt</div>
            </div>
        """, unsafe_allow_html=True)
    with kpi5:
        st.markdown(f"""
            <div class="orbit-card">
                <div class="orbit-label">Avg Basket Size</div>
                <div class="orbit-value">{basket_size:.1f} <span style="font-size:1rem;font-weight:500;">items</span></div>
                <div class="orbit-badge badge-positive">Per Customer</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # --- Tabs Layout ---
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Executive Overview", 
        "🛍️ Product Intelligence", 
        "💰 Profitability Analysis",
        "📅 Operational Intelligence"
    ])

    # Shared Chart Layout Theme
    plot_layout_defaults = dict(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Plus Jakarta Sans, sans-serif", color="#64748B", size=12),
        margin=dict(t=20, l=10, r=10, b=10),
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(showgrid=True, gridcolor="#F1F5F9", zeroline=False),
        hoverlabel=dict(bgcolor="#FFFFFF", font_size=12, font_family="Plus Jakarta Sans")
    )

    # === TAB 1: EXECUTIVE OVERVIEW ===
    with tab1:
        st.markdown('<div class="orbit-chart-card">', unsafe_allow_html=True)
        col_ctrl1, col_ctrl2 = st.columns([3, 1])
        with col_ctrl1:
            time_grouping = st.radio("Resolution:", options=["Day", "Week", "Month"], horizontal=True, label_visibility="collapsed")
        with col_ctrl2:
            enable_ai = st.toggle("🤖 AI Trend Forecast")

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

        if enable_ai and ai_forecasting:
            plot_df = ai_forecasting.generate_forecast(
                trend_df, date_col='transaction_date', metric_col='total_sale_value', forecast_periods=periods, freq=freq_code
            )
            fig_trend = px.line(
                plot_df, x='transaction_date', y='predicted_value', color='Type',
                color_discrete_map={'Historical Data': '#3B82F6', 'Forecast (AI)': '#EC4899'}
            )
        else:
            fig_trend = go.Figure()
            # Smooth rounded area curve matching the Dribbble style
            fig_trend.add_trace(go.Scatter(
                x=trend_df['transaction_date'],
                y=trend_df['total_sale_value'],
                fill='tozeroy',
                fillcolor='rgba(59, 130, 246, 0.08)',
                line=dict(color='#3B82F6', width=3, shape='spline'),
                hovertemplate="<b>%{x|%b %d, %Y}</b><br>Revenue: GH₵ %{y:,.2f}<extra></extra>"
            ))

        fig_trend.update_layout(**plot_layout_defaults)
        st.plotly_chart(fig_trend, use_container_width=True, config={'displayModeBar': False})
        st.markdown('</div>', unsafe_allow_html=True)

    # === TAB 2: PRODUCT INTELLIGENCE ===
    with tab2:
        top_products = df.groupby('item_name').agg(
            revenue=('total_sale_value', 'sum'),
            volume=('quantity', 'sum'),
            profit=('total_profit_ghs', 'sum')
        ).reset_index().sort_values(by='revenue', ascending=False)

        top_10 = top_products.head(10)

        col_left, col_right = st.columns(2)
        with col_left:
            st.markdown('<div class="orbit-chart-card"><div class="chart-header">Top Revenue Drivers</div><div class="chart-subtitle">Ranked by gross sales volume</div>', unsafe_allow_html=True)
            fig_bar = px.bar(
                top_10.sort_values(by='revenue', ascending=True), 
                x='revenue', y='item_name', orientation='h',
                color_discrete_sequence=['#4F46E5']
            )
            fig_bar.update_layout(**plot_layout_defaults)
            fig_bar.update_traces(marker_line_width=0, marker=dict(cornerradius=6), hovertemplate="<b>%{y}</b><br>Revenue: GH₵ %{x:,.2f}<extra></extra>")
            st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})
            st.markdown('</div>', unsafe_allow_html=True)

        with col_right:
            st.markdown('<div class="orbit-chart-card"><div class="chart-header">Volume Distribution</div><div class="chart-subtitle">Breakdown of total units sold</div>', unsafe_allow_html=True)
            # Modern pastel donut palette
            orbit_colors = ['#4F46E5', '#38BDF8', '#F43F5E', '#FB923C', '#10B981', '#A855F7', '#FBBF24', '#94A3B8']
            fig_donut = px.pie(
                top_10, values='volume', names='item_name', hole=0.6,
                color_discrete_sequence=orbit_colors
            )
            fig_donut.update_layout(**plot_layout_defaults)
            fig_donut.update_traces(textposition='inside', textinfo='percent', hovertemplate="<b>%{label}</b><br>Units: %{value}<br>Share: %{percent}<extra></extra>")
            st.plotly_chart(fig_donut, use_container_width=True, config={'displayModeBar': False})
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="orbit-chart-card"><div class="chart-header">Product Roster & Margin Health</div>', unsafe_allow_html=True)
        st.dataframe(
            top_10,
            column_config={
                "item_name": st.column_config.TextColumn("Product"),
                "revenue": st.column_config.ProgressColumn("Total Revenue", format="GH₵ %d", min_value=0, max_value=float(top_products['revenue'].max())),
                "volume": st.column_config.NumberColumn("Quantity"),
                "profit": st.column_config.NumberColumn("Gross Profit (GH₵)", format="GH₵ %d")
            },
            hide_index=True,
            use_container_width=True
        )
        st.markdown('</div>', unsafe_allow_html=True)

    # === TAB 3: PROFITABILITY ANALYSIS ===
    with tab3:
        top_products['margin_pct'] = (top_products['profit'] / top_products['revenue']) * 100
        all_margin_items = top_products.sort_values(by='margin_pct', ascending=False)

        col_matrix, col_bar = st.columns(2)
        with col_bar:
            st.markdown('<div class="orbit-chart-card"><div class="chart-header">Product Profitability Ranking</div><div class="chart-subtitle">Sorted by Margin %</div>', unsafe_allow_html=True)
            fig_margin = px.bar(
                all_margin_items.sort_values(by='margin_pct', ascending=True),
                x='margin_pct', y='item_name', orientation='h',
                color_discrete_sequence=['#0D9488'], text='profit'
            )
            fig_margin.update_traces(
                texttemplate='GH₵ %{text:,.0f}', textposition='inside',
                marker=dict(cornerradius=4),
                hovertemplate="<b>%{y}</b><br>Margin: %{x:.1f}%<br>Profit: GH₵ %{text:,.2f}<extra></extra>"
            )
            fig_margin.update_layout(**plot_layout_defaults, height=650)
            st.plotly_chart(fig_margin, use_container_width=True, config={'displayModeBar': False})
            st.markdown('</div>', unsafe_allow_html=True)

        with col_matrix:
            st.markdown('<div class="orbit-chart-card"><div class="chart-header">The Profitability Matrix</div><div class="chart-subtitle">Margin vs Absolute Profit (Bubble size = Revenue)</div>', unsafe_allow_html=True)
            fig_scatter = px.scatter(
                all_margin_items, x='margin_pct', y='profit', size='revenue',
                color='margin_pct', hover_name='item_name',
                color_continuous_scale="Tealgrn"
            )
            fig_scatter.update_layout(**plot_layout_defaults, height=650)
            fig_scatter.update_traces(
                hovertemplate="<b>%{hovertext}</b><br>Margin: %{x:.1f}%<br>Profit: GH₵ %{y:,.2f}<extra></extra>"
            )
            st.plotly_chart(fig_scatter, use_container_width=True, config={'displayModeBar': False})
            st.markdown('</div>', unsafe_allow_html=True)

    # === TAB 4: OPERATIONAL INTELLIGENCE ===
    with tab4:
        col_day, col_basket = st.columns(2)
        with col_day:
            st.markdown('<div class="orbit-chart-card"><div class="chart-header">Revenue by Day of the Week</div><div class="chart-subtitle">Identify peak operational traffic</div>', unsafe_allow_html=True)
            df['day_of_week'] = df['transaction_date'].dt.day_name()
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            day_stats = df.groupby('day_of_week')['total_sale_value'].sum().reindex(day_order).fillna(0).reset_index()
            
            fig_day = px.bar(
                day_stats, x='day_of_week', y='total_sale_value',
                color_discrete_sequence=['#6366F1']
            )
            fig_day.update_layout(**plot_layout_defaults)
            fig_day.update_traces(marker=dict(cornerradius=8), hovertemplate="<b>%{x}</b><br>Revenue: GH₵ %{y:,.2f}<extra></extra>")
            st.plotly_chart(fig_day, use_container_width=True, config={'displayModeBar': False})
            st.markdown('</div>', unsafe_allow_html=True)

        with col_basket:
            st.markdown('<div class="orbit-chart-card"><div class="chart-header">Basket Size Distribution</div><div class="chart-subtitle">Transaction volume by item count</div>', unsafe_allow_html=True)
            basket_sizes = df.groupby('receipt_id')['quantity'].sum().reset_index()
            
            fig_basket = px.histogram(
                basket_sizes, x='quantity',
                color_discrete_sequence=['#F43F5E'], nbins=15
            )
            fig_basket.update_layout(**plot_layout_defaults)
            fig_basket.update_traces(marker=dict(cornerradius=6), hovertemplate="Basket Size: %{x} items<br>Orders: %{y}<extra></extra>")
            st.plotly_chart(fig_basket, use_container_width=True, config={'displayModeBar': False})
            st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    render_dashboard()