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

# --- Modern Orbit UI CSS ---
CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }

    /* App Canvas Background */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stMain"] {
        background-color: #F0F8FF !important;
        color: #2F4F4F !important;
    }

    /* Main Container Padding */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2.5rem !important;
        max-width: 1350px !important;
    }

    /* Guaranteed Solid White KPI Metric Cards */
    div.orbit-kpi-card,
    .orbit-kpi-card {
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
        border: 1.5px solid #CBD5E1 !important;
        border-radius: 15px !important;
        padding: 20px 24px !important;
        box-shadow: 0 6px 20px rgba(0, 128, 128, 0.10) !important;
        box-sizing: border-box !important;
        width: 100% !important;
        display: block !important;
        position: relative !important;
        transition: transform 0.15s ease-in-out !important;
    }
    div.orbit-kpi-card:hover {
        transform: translateY(-2px) !important;
    }

    /* KPI Card Typography */
    .orbit-label {
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.6px !important;
        color: #5A7B7B !important;
        margin-bottom: 6px !important;
    }
    .orbit-value {
        font-size: 1.65rem !important;
        font-weight: 700 !important;
        color: #2F4F4F !important;
        letter-spacing: -0.5px !important;
        line-height: 1.2 !important;
    }
    .orbit-badge {
        display: inline-block !important;
        font-size: 0.75rem !important;
        font-weight: 600 !important;
        padding: 3px 8px !important;
        border-radius: 12px !important;
        margin-top: 6px !important;
    }
    .badge-positive {
        background: rgba(0, 128, 128, 0.12) !important;
        color: #006666 !important;
    }

    /* Native Container Wrapper Solid White Fallback */
    [data-testid="stVerticalBlockBorderWrapper"],
    [data-testid="stVerticalBlockBorderWrapper"] > div {
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"] {
        border: 1.5px solid #CBD5E1 !important;
        border-radius: 15px !important;
        padding: 14px 18px !important;
        box-shadow: 0 4px 16px rgba(0, 128, 128, 0.08) !important;
        margin-bottom: 1.2rem !important;
    }

    /* Chart Titles */
    .chart-header {
        font-size: 1.15rem !important;
        font-weight: 700 !important;
        color: #2F4F4F !important;
        margin-bottom: 4px !important;
    }
    .chart-subtitle {
        font-size: 0.82rem !important;
        color: #5A7B7B !important;
        margin-bottom: 12px !important;
    }

    /* Horizontal Radio Buttons Arrangement */
    [data-testid="stRadio"] > div[role="radiogroup"] {
        flex-direction: row !important;
        gap: 18px !important;
        align-items: center !important;
        flex-wrap: nowrap !important;
    }

    /* Confinement for Plotly elements */
    [data-testid="stPlotlyChart"] {
        width: 100% !important;
        max-width: 100% !important;
        height: 400px !important;
        max-height: 400px !important;
        overflow: hidden !important;
        position: relative !important;
    }

    [data-testid="stPlotlyChart"] > div {
        max-width: 100% !important;
        overflow: visible !important;
    }

    [data-testid="stFullScreenFrame"] [data-testid="stPlotlyChart"] {
        height: 100% !important;
        max-height: 100% !important;
    }

    [data-testid="stElementToolbar"] {
        opacity: 1 !important;
        visibility: visible !important;
        display: flex !important;
    }

    /* Modebar Positioning */
    .js-plotly-plot .plotly .modebar {
        top: 8px !important;
        right: 8px !important;
        margin-bottom: 10px !important;
        margin-right: 8px !important;
        padding: 4px 6px !important;
        border-radius: 8px !important;
        background: rgba(255, 255, 255, 0.9) !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06) !important;
    }
    .js-plotly-plot .plotly .modebar-btn {
        margin-right: 4px !important;
        margin-bottom: 2px !important;
    }

    /* Centered Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px !important;
        background-color: transparent !important;
        padding: 10px 0 !important;
        border-bottom: none !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        width: 100% !important;
    }
    .stTabs [data-baseweb="tab-highlight"],
    .stTabs [data-baseweb="tab-border"] {
        display: none !important;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #FFFFFF !important;
        color: #006666 !important;
        border: 1.5px solid #008080 !important;
        border-radius: 15px !important;
        padding: 8px 22px !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        transition: all 0.2s ease-in-out !important;
        box-shadow: 0 2px 6px rgba(0, 128, 128, 0.08) !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: rgba(0, 128, 128, 0.08) !important;
        color: #004D40 !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #008080 !important;
        color: #FFFFFF !important;
        border: 1.5px solid #008080 !important;
        border-radius: 15px !important;
        box-shadow: 0 4px 14px rgba(0, 128, 128, 0.35) !important;
        padding: 8px 15px !important;
    }

    [data-testid="stDataFrame"] {
        border-radius: 12px !important;
        overflow: hidden !important;
        border: 1px solid #E2E8F0 !important;
    }
</style>
"""

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

# --- Filter Synchronization State Handlers ---
TABS = ["tab1", "tab2", "tab3", "tab4"]

def sync_mode(source_tab):
    val = st.session_state[f"mode_{source_tab}"]
    st.session_state["dash_filter_mode"] = val
    for t in TABS:
        st.session_state[f"mode_{t}"] = val

def sync_date_range(source_tab):
    val = st.session_state[f"date_{source_tab}"]
    if isinstance(val, (list, tuple)) and len(val) == 2:
        st.session_state["dash_date_range"] = val
        for t in TABS:
            st.session_state[f"date_{t}"] = val

def sync_month_start(source_tab):
    val = st.session_state[f"m_start_{source_tab}"]
    st.session_state["dash_start_month"] = val
    for t in TABS:
        st.session_state[f"m_start_{t}"] = val

def sync_month_end(source_tab):
    val = st.session_state[f"m_end_{source_tab}"]
    st.session_state["dash_end_month"] = val
    for t in TABS:
        st.session_state[f"m_end_{t}"] = val

def render_dashboard(company_id=None):
    # Injected inside render_dashboard so CSS is refreshed on every rerun
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    with st.spinner("Crunching your retail intelligence..."):
        try:
            df = fetch_retail_data()
        except Exception as e:
            st.error(f"⚠️ Could not load data: {e}")
            return

    if df.empty:
        st.info("No retail data found. Please upload records in the Ingestion tab.")
        return

    # --- Pre-calculate Temporal Anchors ---
    min_date = df['transaction_date'].min().date()
    max_date = df['transaction_date'].max().date()

    df_sorted = df.sort_values('transaction_date')
    month_periods = df_sorted['transaction_date'].dt.to_period('M').unique()
    month_options = [p.strftime('%B %Y') for p in month_periods]
    month_lookup = {p.strftime('%B %Y'): p for p in month_periods}
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    # --- Initialize Master Filter State ---
    if "dash_filter_mode" not in st.session_state:
        st.session_state["dash_filter_mode"] = "⚡ Full History"
    if "dash_date_range" not in st.session_state:
        st.session_state["dash_date_range"] = (min_date, max_date)
    if "dash_start_month" not in st.session_state:
        st.session_state["dash_start_month"] = month_options[0]
    if "dash_end_month" not in st.session_state:
        st.session_state["dash_end_month"] = month_options[-1]
    if st.session_state.get("dash_filter_mode") == "📆 Day to Day":
        st.session_state["dash_filter_mode"] = "⚡ Full History"

    # Synchronize all tab-specific session keys
    for t in TABS:
        if f"mode_{t}" not in st.session_state:
            st.session_state[f"mode_{t}"] = st.session_state["dash_filter_mode"]
        if f"date_{t}" not in st.session_state:
            st.session_state[f"date_{t}"] = st.session_state["dash_date_range"]
        if f"m_start_{t}" not in st.session_state:
            st.session_state[f"m_start_{t}"] = st.session_state["dash_start_month"]
        if f"m_end_{t}" not in st.session_state:
            st.session_state[f"m_end_{t}"] = st.session_state["dash_end_month"]
        if st.session_state.get(f"mode_{t}") == "📆 Day to Day":
            st.session_state[f"mode_{t}"] = "⚡ Full History"

    # --- Filter Dataset by Active Selection ---
    filtered_df = df.copy()
    current_mode = st.session_state["dash_filter_mode"]

    if current_mode == "📅 Date Range":
        d_range = st.session_state["dash_date_range"]
        if isinstance(d_range, (list, tuple)) and len(d_range) == 2:
            s_d, e_d = d_range
            filtered_df = filtered_df[
                (filtered_df['transaction_date'].dt.date >= s_d) & 
                (filtered_df['transaction_date'].dt.date <= e_d)
            ]
    elif current_mode == "🗓️ Month to Month":
        p_start = month_lookup[st.session_state["dash_start_month"]]
        p_end = month_lookup[st.session_state["dash_end_month"]]
        p_min, p_max = min(p_start, p_end), max(p_start, p_end)
        filtered_df = filtered_df[
            (filtered_df['transaction_date'].dt.to_period('M') >= p_min) & 
            (filtered_df['transaction_date'].dt.to_period('M') <= p_max)
        ]
    if filtered_df.empty:
        active_df = df
        filter_warning = True
    else:
        active_df = filtered_df
        filter_warning = False

    # --- Calculations from Active (Filtered) Data ---
    total_revenue = active_df['total_sale_value'].sum()
    total_profit = active_df['total_profit_ghs'].sum()
    gross_margin = (total_profit / total_revenue) * 100 if total_revenue > 0 else 0
    total_items = active_df['quantity'].sum()
    total_transactions = active_df['receipt_id'].nunique()
    aov = total_revenue / total_transactions if total_transactions > 0 else 0
    basket_size = total_items / total_transactions if total_transactions > 0 else 0

    # --- Top Header ---
    c_title, c_user = st.columns([4, 1])
    with c_title:
        st.markdown("<h2 style='font-weight:700; color:#2F4F4F; margin-bottom: 0;'>Enterprise Retail Command Center</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color:#5A7B7B; font-size:0.9rem; margin-top:2px;'>Real-time metrics, unit economics, and performance insights</p>", unsafe_allow_html=True)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # --- 5 KPI Cards (Permanent Solid White with Native Inline Fallbacks) ---
    KPI_STYLE = "background-color: #FFFFFF; background: #FFFFFF; border: 1.5px solid #CBD5E1; border-radius: 15px; padding: 20px 24px; box-shadow: 0 6px 20px rgba(0, 128, 128, 0.10); box-sizing: border-box; width: 100%; display: block;"

    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    with kpi1:
        st.markdown(f"""
            <div class="orbit-kpi-card" style="{KPI_STYLE}">
                <div class="orbit-label">Total Revenue</div>
                <div class="orbit-value">GH₵ {total_revenue:,.0f}</div>
                <div class="orbit-badge badge-positive">↑ Active Growth</div>
            </div>
        """, unsafe_allow_html=True)
    with kpi2:
        st.markdown(f"""
            <div class="orbit-kpi-card" style="{KPI_STYLE}">
                <div class="orbit-label">Gross Profit</div>
                <div class="orbit-value">GH₵ {total_profit:,.0f}</div>
                <div class="orbit-badge badge-positive">Net Margin Solid</div>
            </div>
        """, unsafe_allow_html=True)
    with kpi3:
        st.markdown(f"""
            <div class="orbit-kpi-card" style="{KPI_STYLE}">
                <div class="orbit-label">Gross Margin</div>
                <div class="orbit-value">{gross_margin:.1f}%</div>
                <div class="orbit-badge badge-positive">Target: >30%</div>
            </div>
        """, unsafe_allow_html=True)
    with kpi4:
        st.markdown(f"""
            <div class="orbit-kpi-card" style="{KPI_STYLE}">
                <div class="orbit-label">Avg Order Value</div>
                <div class="orbit-value">GH₵ {aov:,.1f}</div>
                <div class="orbit-badge badge-positive">Per Receipt</div>
            </div>
        """, unsafe_allow_html=True)
    with kpi5:
        st.markdown(f"""
            <div class="orbit-kpi-card" style="{KPI_STYLE}">
                <div class="orbit-label">Avg Basket Size</div>
                <div class="orbit-value">{basket_size:.1f} <span style="font-size:1rem;font-weight:500;">items</span></div>
                <div class="orbit-badge badge-positive">Per Customer</div>
            </div>
        """, unsafe_allow_html=True)

    st.divider()

    # --- Center Tabs Navigation ---
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Executive Overview", 
        "🛍️ Product Intelligence", 
        "💰 Profitability Analysis",
        "📅 Operational Intelligence"
    ])

    plot_layout_defaults = dict(
        paper_bgcolor='#FFFFFF',
        plot_bgcolor='#FFFFFF',
        font=dict(family="Plus Jakarta Sans, sans-serif", color="#5A7B7B", size=12),
        margin=dict(t=30, l=10, r=10, b=10),
        height=400,
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(showgrid=True, gridcolor="#E0E0E0", zeroline=False),
        dragmode='pan',
        hoverlabel=dict(bgcolor="#FFFFFF", font_size=12, font_family="Plus Jakarta Sans"),
        modebar=dict(
            orientation='h',
            bgcolor='rgba(255, 255, 255, 0.85)',
            color='#5A7B7B',
            activecolor='#008080'
        )
    )

    chart_config = {
        'displayModeBar': True,
        'displaylogo': False,
        'scrollZoom': False,
        'modeBarButtons': [
            ['toImage', 'zoomIn2d', 'zoomOut2d', 'resetScale2d']
        ],
        'toImageButtonOptions': {
            'format': 'png',
            'filename': 'omnipulse_chart',
            'height': 500,
            'width': 850,
            'scale': 2
        }
    }

    # --- Horizontal Filter Command Bar ---
    def render_filter_bar(tab_id):
        with st.container(border=True):
            col_head, col_mode, col_stat = st.columns([1.3, 4.5, 1.4])
            with col_head:
                st.markdown("""
                <div style="font-size: 0.85rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: #008080; padding-top: 8px;">
                    ⚡ Filter Scope
                </div>
                """, unsafe_allow_html=True)

            with col_mode:
                st.radio(
                    "Filter Dimension",
                    options=["⚡ Full History", "📅 Date Range", "🗓️ Month to Month"],
                    key=f"mode_{tab_id}",
                    on_change=sync_mode,
                    args=(tab_id,),
                    horizontal=True,
                    label_visibility="collapsed"
                )

            with col_stat:
                st.markdown(f"""
                <div style="text-align: right; font-size: 0.82rem; color: #5A7B7B; line-height: 1.3; padding-top: 4px;">
                    <b>{len(active_df):,}</b> txns active<br>
                    <span style="color: #008080; font-weight: 700;">GH₵ {total_revenue:,.0f}</span>
                </div>
                """, unsafe_allow_html=True)

            mode = st.session_state[f"mode_{tab_id}"]
            if mode != "⚡ Full History":
                st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
                col_sub_label, col_sub_inputs, _ = st.columns([1.3, 4.5, 1.4])
                with col_sub_label:
                    if mode == "📅 Date Range":
                        st.markdown("<div style='font-size:0.85rem; font-weight:600; color:#5A7B7B; padding-top:8px;'>Date Window:</div>", unsafe_allow_html=True)
                    elif mode == "🗓️ Month to Month":
                        st.markdown("<div style='font-size:0.85rem; font-weight:600; color:#5A7B7B; padding-top:8px;'>Month Range:</div>", unsafe_allow_html=True)
                with col_sub_inputs:
                    if mode == "📅 Date Range":
                        st.date_input(
                            "Select Date Range",
                            key=f"date_{tab_id}",
                            on_change=sync_date_range,
                            args=(tab_id,),
                            min_value=min_date,
                            max_value=max_date,
                            label_visibility="collapsed"
                        )
                    elif mode == "🗓️ Month to Month":
                        c_m1, c_m2 = st.columns(2)
                        with c_m1:
                            st.selectbox(
                                "From Month",
                                options=month_options,
                                key=f"m_start_{tab_id}",
                                on_change=sync_month_start,
                                args=(tab_id,),
                                label_visibility="collapsed"
                            )
                        with c_m2:
                            st.selectbox(
                                "To Month",
                                options=month_options,
                                key=f"m_end_{tab_id}",
                                on_change=sync_month_end,
                                args=(tab_id,),
                                label_visibility="collapsed"
                            )
        if filter_warning:
            st.warning("⚠️ No records matched this precise window. Displaying all available records.")

    # === TAB 1: EXECUTIVE OVERVIEW ===
    with tab1:
        render_filter_bar("tab1")

        col_ctrl1, col_ctrl2 = st.columns([3, 1])
        with col_ctrl1:
            time_grouping = st.radio("Resolution:", options=["Day", "Week", "Month"], horizontal=True, label_visibility="collapsed")
        with col_ctrl2:
            enable_ai = st.toggle("🤖 AI Trend Forecast")

        df_time = active_df.set_index('transaction_date')
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

        if enable_ai and ai_forecasting and not trend_df.empty:
            plot_df = ai_forecasting.generate_forecast(
                trend_df, date_col='transaction_date', metric_col='total_sale_value', forecast_periods=periods, freq=freq_code
            )
            fig_trend = px.line(
                plot_df, x='transaction_date', y='predicted_value', color='Type',
                color_discrete_map={'Historical Data': '#008080', 'Forecast (AI)': '#006666'}
            )
        else:
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(
                x=trend_df['transaction_date'],
                y=trend_df['total_sale_value'],
                fill='tozeroy',
                fillcolor='rgba(0, 128, 128, 0.12)',
                line=dict(color='#008080', width=3, shape='spline'),
                hovertemplate="<b>%{x|%b %d, %Y}</b><br>Revenue: GH₵ %{y:,.2f}<extra></extra>"
            ))

        fig_trend.update_layout(**plot_layout_defaults)
        st.plotly_chart(fig_trend, use_container_width=True, config=chart_config)

    # === TAB 2: PRODUCT INTELLIGENCE ===
    with tab2:
        render_filter_bar("tab2")

        top_products = active_df.groupby('item_name').agg(
            revenue=('total_sale_value', 'sum'),
            volume=('quantity', 'sum'),
            profit=('total_profit_ghs', 'sum')
        ).reset_index().sort_values(by='revenue', ascending=False)

        top_10 = top_products.head(10)

        col_left, col_right = st.columns(2)
        with col_left:
            with st.container(border=True):
                st.markdown('<div class="chart-header">Top Revenue Drivers</div><div class="chart-subtitle">Ranked by gross sales volume</div>', unsafe_allow_html=True)
                fig_bar = px.bar(
                    top_10.sort_values(by='revenue', ascending=True), 
                    x='revenue', y='item_name', orientation='h',
                    color_discrete_sequence=['#008080']
                )
                fig_bar.update_layout(**plot_layout_defaults)
                fig_bar.update_traces(marker_line_width=0, marker=dict(cornerradius=6), hovertemplate="<b>%{y}</b><br>Revenue: GH₵ %{x:,.2f}<extra></extra>")
                st.plotly_chart(fig_bar, use_container_width=True, config=chart_config)

        with col_right:
            with st.container(border=True):
                st.markdown('<div class="chart-header">Quantity Distribution</div><div class="chart-subtitle">Breakdown of total units sold</div>', unsafe_allow_html=True)
                orbit_colors = ['#008080', '#0E9594', '#12B886', '#20C997', '#2F4F4F', '#3D5A5A', '#5A7B7B', '#7A9A9A', '#9BBAB4', '#BBD5D0']
                fig_donut = px.pie(
                    top_10, values='volume', names='item_name',
                    color_discrete_sequence=orbit_colors
                )
                fig_donut.update_layout(**plot_layout_defaults)
                fig_donut.update_traces(
                    textposition='inside',
                    textinfo='percent',
                    marker=dict(line=dict(color='#FFFFFF', width=2)),
                    hovertemplate="<b>%{label}</b><br>Units Sold: %{value:,.0f}<br>Share: %{percent}<extra></extra>"
                )
                st.plotly_chart(fig_donut, use_container_width=True, config=chart_config)

        with st.container(border=True):
            st.markdown('<div class="chart-header">Product Roster & Margin Health</div>', unsafe_allow_html=True)
            st.dataframe(
                top_10,
                column_config={
                    "item_name": st.column_config.TextColumn("Product"),
                    "revenue": st.column_config.ProgressColumn("Total Revenue", format="GH₵ %,.2f", min_value=0, max_value=float(top_products['revenue'].max()) if not top_products.empty else 100),
                    "volume": st.column_config.NumberColumn("Quantity", format="%,d"),
                    "profit": st.column_config.NumberColumn("Gross Profit (GH₵)", format="GH₵ %,.2f")
                },
                hide_index=True,
                use_container_width=True
            )

    # === TAB 3: PROFITABILITY ANALYSIS ===
    with tab3:
        render_filter_bar("tab3")

        top_products['margin_pct'] = (top_products['profit'] / top_products['revenue']) * 100
        all_margin_items = top_products.sort_values(by='margin_pct', ascending=False)

        col_matrix, col_bar = st.columns(2)
        with col_bar:
            with st.container(border=True):
                st.markdown('<div class="chart-header">Product Profitability Ranking</div><div class="chart-subtitle">Sorted by Margin %</div>', unsafe_allow_html=True)
                fig_margin = px.bar(
                    all_margin_items.sort_values(by='margin_pct', ascending=True),
                    x='margin_pct', y='item_name', orientation='h',
                    color_discrete_sequence=['#006666'], text='profit'
                )
                fig_margin.update_traces(
                    texttemplate='GH₵ %{text:,.0f}', textposition='inside',
                    marker=dict(cornerradius=4),
                    hovertemplate="<b>%{y}</b><br>Margin: %{x:.1f}%<br>Profit: GH₵ %{text:,.2f}<extra></extra>"
                )
                fig_margin.update_layout(**plot_layout_defaults)
                st.plotly_chart(fig_margin, use_container_width=True, config=chart_config)

        with col_matrix:
            with st.container(border=True):
                st.markdown('<div class="chart-header">The Profitability Matrix</div><div class="chart-subtitle">Margin vs Absolute Profit (Bubble size = Revenue)</div>', unsafe_allow_html=True)
                fig_scatter = px.scatter(
                    all_margin_items, x='margin_pct', y='profit', size='revenue',
                    color='margin_pct', hover_name='item_name',
                    color_continuous_scale=['#008080', '#006666']
                )
                fig_scatter.update_layout(**plot_layout_defaults)
                fig_scatter.update_traces(
                    hovertemplate="<b>%{hovertext}</b><br>Margin: %{x:.1f}%<br>Profit: GH₵ %{y:,.2f}<extra></extra>"
                )
                st.plotly_chart(fig_scatter, use_container_width=True, config=chart_config)

    # === TAB 4: OPERATIONAL INTELLIGENCE ===
    with tab4:
        render_filter_bar("tab4")

        col_day, col_basket = st.columns(2)
        with col_day:
            with st.container(border=True):
                st.markdown('<div class="chart-header">Revenue by Day of the Week</div><div class="chart-subtitle">Identify peak operational traffic</div>', unsafe_allow_html=True)
                active_df['day_of_week'] = active_df['transaction_date'].dt.day_name()
                day_stats = active_df.groupby('day_of_week')['total_sale_value'].sum().reindex(days_order).fillna(0).reset_index()
                
                fig_day = px.bar(
                    day_stats, x='day_of_week', y='total_sale_value',
                    color_discrete_sequence=['#008080']
                )
                fig_day.update_layout(**plot_layout_defaults)
                fig_day.update_traces(marker=dict(cornerradius=8), hovertemplate="<b>%{x}</b><br>Revenue: GH₵ %{y:,.2f}<extra></extra>")
                st.plotly_chart(fig_day, use_container_width=True, config=chart_config)

        with col_basket:
            with st.container(border=True):
                st.markdown('<div class="chart-header">Basket Size Distribution</div><div class="chart-subtitle">Transaction volume by item count</div>', unsafe_allow_html=True)
                basket_sizes = active_df.groupby('receipt_id')['quantity'].sum().reset_index()
                
                fig_basket = px.histogram(
                    basket_sizes, x='quantity',
                    color_discrete_sequence=['#006666'], nbins=15
                )
                fig_basket.update_layout(**plot_layout_defaults)
                fig_basket.update_traces(marker=dict(cornerradius=6), hovertemplate="Basket Size: %{x} items<br>Orders: %{y}<extra></extra>")
                st.plotly_chart(fig_basket, use_container_width=True, config=chart_config)

if __name__ == "__main__":
    render_dashboard()