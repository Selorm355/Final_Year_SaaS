import streamlit as st
import pandas as pd
import plotly.express as px
import os
import ai_forecasting
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(f"postgresql://{os.environ.get('POSTGRES_USER')}:{os.environ.get('POSTGRES_PASSWORD')}@db:5432/{os.environ.get('POSTGRES_DB')}")

def fetch_hospitality_data():
    query = """
        SELECT 
            check_in_date, 
            booking_id, 
            room_type, 
            nights_stayed, 
            total_paid_ghs
        FROM silver.silver_hospitality_clean
    """
    df = pd.read_sql(query, engine)
    df['check_in_date'] = pd.to_datetime(df['check_in_date'])
    return df

def render_dashboard(company_id):
    with st.spinner("Gathering hotel metrics..."):
        try:
            df = fetch_hospitality_data()
        except Exception as e:
            st.error(f"⚠️ CRASH DETAILS: {e}")
            return

    if df.empty:
        st.info("No hospitality data found. Please upload your raw data.")
        return

    # --- ADVANCED METRICS CALCULATION ---
    total_revenue = df['total_paid_ghs'].sum()
    total_nights = df['nights_stayed'].sum()
    total_bookings = df['booking_id'].nunique()
    
    # Gold standard hospitality metrics
    adr = total_revenue / total_nights if total_nights > 0 else 0
    alos = total_nights / total_bookings if total_bookings > 0 else 0
    avg_booking_value = total_revenue / total_bookings if total_bookings > 0 else 0

    # --- TOP ROW: EXECUTIVE KPI CARDS ---
    st.markdown("### 🏨 Enterprise Hospitality Command Center")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    col1.metric("Total Revenue", f"GH₵ {total_revenue:,.0f}")
    col2.metric("Total Bookings", f"{total_bookings:,}")
    col3.metric("Avg Daily Rate (ADR)", f"GH₵ {adr:,.2f}")
    col4.metric("Avg Length of Stay", f"{alos:.1f} nights")
    col5.metric("Avg Booking Value", f"GH₵ {avg_booking_value:,.2f}")

    st.divider()

    # --- SAAS TABBED LAYOUT ---
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Executive Overview", 
        "🛏️ Room Intelligence", 
        "💰 Room Economics",
        "📅 Booking Patterns"
    ])

    # === TAB 1: EXECUTIVE OVERVIEW ===
    with tab1:
        col_chart_title, col_toggle, col_ai = st.columns([2, 1, 1])
        with col_chart_title:
            time_grouping = st.radio("Group Data By:", options=["Day", "Week", "Month"], horizontal=True, key="hosp_time")
        with col_ai:
            enable_ai = st.toggle("🤖 Enable AI Forecast", key="hosp_ai")

        df_time = df.set_index('check_in_date')
        if time_grouping == "Day":
            trend_df = df_time.resample('D').agg({'total_paid_ghs': 'sum', 'nights_stayed': 'sum'}).reset_index()
            periods, freq_code = 7, 'D'
        elif time_grouping == "Week":
            trend_df = df_time.resample('W-MON').agg({'total_paid_ghs': 'sum', 'nights_stayed': 'sum'}).reset_index()
            periods, freq_code = 4, 'W'
        else:
            trend_df = df_time.resample('ME').agg({'total_paid_ghs': 'sum', 'nights_stayed': 'sum'}).reset_index()
            periods, freq_code = 3, 'M'
            
        trend_df = trend_df[trend_df['total_paid_ghs'] > 0]

        if enable_ai:
            with st.spinner("AI is analyzing hotel booking trends..."):
                plot_df = ai_forecasting.generate_forecast(
                    trend_df, date_col='check_in_date', metric_col='total_paid_ghs', forecast_periods=periods, freq=freq_code
                )
                fig_trend = px.line(
                    plot_df, x='check_in_date', y='predicted_value', color='Type', line_dash='Type',
                    color_discrete_map={'Historical Data': '#008080', 'Forecast (AI)': '#006666'},
                    labels={'check_in_date': 'Date', 'predicted_value': 'Revenue (GH₵)'}
                )
        else:
            fig_trend = px.area(
                trend_df, x='check_in_date', y='total_paid_ghs',
                labels={'check_in_date': 'Date', 'total_paid_ghs': 'Revenue (GH₵)'},
                color_discrete_sequence=['#008080']
            )

        fig_trend.update_traces(hovertemplate="<b>Date:</b> %{x}<br><b>Revenue:</b> GH₵ %{y:,.2f}<extra></extra>")
        fig_trend.update_layout(xaxis_title="", yaxis_title="")
        st.plotly_chart(fig_trend, use_container_width=True)

    # === TAB 2: ROOM INTELLIGENCE ===
    with tab2:
        # Fully uncapped room statistics to maximize insights
        room_stats = df.groupby('room_type').agg(
            bookings=('booking_id', 'count'),
            nights=('nights_stayed', 'sum'),
            revenue=('total_paid_ghs', 'sum')
        ).reset_index().sort_values(by='revenue', ascending=False)

        col_left, col_right = st.columns(2)
        with col_left:
            fig_bar = px.bar(
                room_stats.sort_values(by='revenue', ascending=True), 
                x='revenue', y='room_type', orientation='h',
                title="Total Revenue by Room Category",
                labels={'revenue': 'Revenue (GH₵)', 'room_type': ''},
                color_discrete_sequence=['#006666']
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_right:
            fig_donut = px.pie(
                room_stats, values='nights', names='room_type', hole=0.4,
                title="Volume Share (Total Nights Stayed)"
            )
            fig_donut.update_traces(textinfo='percent', hovertemplate="<b>%{label}</b><br>Nights: %{value}<extra></extra>")
            st.plotly_chart(fig_donut, use_container_width=True)

        st.subheader("Deep Dive: Room Performance Matrix")
        st.dataframe(
            room_stats,
            column_config={
                "room_type": st.column_config.TextColumn("Room Category"),
                "bookings": st.column_config.NumberColumn("Total Bookings"),
                "nights": st.column_config.NumberColumn("Total Nights Stayed"),
                "revenue": st.column_config.ProgressColumn("Total Revenue (GH₵)", format="GH₵ %f", min_value=0, max_value=float(room_stats['revenue'].max())),
            },
            hide_index=True,
            use_container_width=True
        )

    # === TAB 3: ROOM ECONOMICS ===
    with tab3:
        st.subheader("Pricing Efficiency by Category")
        room_stats['adr'] = room_stats['revenue'] / room_stats['nights']
        
        col_adr, col_scatter = st.columns(2)
        
        with col_adr:
            fig_adr = px.bar(
                room_stats.sort_values(by='adr', ascending=True),
                x='adr', y='room_type', orientation='h',
                title="Average Daily Rate (ADR) per Room Type",
                labels={'adr': 'ADR (GH₵)', 'room_type': ''},
                color_discrete_sequence=['#2F4F4F'],
                text='adr'
            )
            fig_adr.update_traces(
                texttemplate='GH₵ %{text:,.2f}', 
                textposition='inside', 
                insidetextanchor='middle'
            )
            st.plotly_chart(fig_adr, use_container_width=True)
            
        with col_scatter:
            fig_scatter = px.scatter(
                room_stats, x='adr', y='revenue', size='nights', color='adr',
                hover_name='room_type',
                title="Room Economics Matrix",
                labels={'adr': 'Average Daily Rate (GH₵)', 'revenue': 'Total Revenue (GH₵)'},
                color_continuous_scale=['#008080', '#006666']
            )
            fig_scatter.update_traces(
                hovertemplate="<b>%{hovertext}</b><br>ADR: GH₵ %{x:,.2f}<br>Total Revenue: GH₵ %{y:,.2f}<br>Nights Stayed: %{marker.size}<extra></extra>"
            )
            st.plotly_chart(fig_scatter, use_container_width=True)

    # === TAB 4: BOOKING PATTERNS ===
    with tab4:
        st.subheader("Check-in Traffic & Stay Duration")
        col_day, col_los = st.columns(2)
        
        with col_day:
            df['check_in_day'] = df['check_in_date'].dt.day_name()
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            day_stats = df.groupby('check_in_day')['booking_id'].count().reindex(day_order).reset_index()
            day_stats['booking_id'] = day_stats['booking_id'].fillna(0)
            
            fig_day = px.bar(
                day_stats, x='check_in_day', y='booking_id',
                title="Check-In Volume by Day of the Week",
                labels={'check_in_day': '', 'booking_id': 'Number of Check-Ins'},
                color_discrete_sequence=['#008080']
            )
            st.plotly_chart(fig_day, use_container_width=True)
            
        with col_los:
            fig_los = px.histogram(
                df, x='nights_stayed',
                title="Length of Stay Distribution",
                labels={'nights_stayed': 'Number of Nights per Booking'},
                color_discrete_sequence=['#006666'],
                nbins=14
            )
            fig_los.update_layout(yaxis_title="Number of Bookings")
            st.plotly_chart(fig_los, use_container_width=True)