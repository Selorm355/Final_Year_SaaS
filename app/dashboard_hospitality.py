import streamlit as st
import pandas as pd
import plotly.express as px
import os
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
            total_paid
        FROM silver.silver_hospitality_clean
    """
    df = pd.read_sql(query, engine)
    df['check_in_date'] = pd.to_datetime(df['check_in_date'])
    return df

def render_dashboard(company_id):
    with st.spinner("Gathering hotel metrics..."):
        try:
            df = fetch_hospitality_data()
        except Exception:
            st.error("⚠️ Could not load data. Please ingest your hospitality data first.")
            return

    if df.empty:
        st.info("No hospitality data found. Please upload your raw data.")
        return

    st.subheader("🛎️ Booking & Revenue Trends")
    time_grouping = st.radio("Group Data By:", options=["Day", "Week", "Month"], horizontal=True, key="hosp_time")

    df_time = df.set_index('check_in_date')
    if time_grouping == "Day":
        trend_df = df_time.resample('D').agg({'total_paid': 'sum', 'nights_stayed': 'sum'}).reset_index()
    elif time_grouping == "Week":
        trend_df = df_time.resample('W-MON').agg({'total_paid': 'sum', 'nights_stayed': 'sum'}).reset_index()
    else:
        trend_df = df_time.resample('ME').agg({'total_paid': 'sum', 'nights_stayed': 'sum'}).reset_index()
        
    trend_df = trend_df[trend_df['total_paid'] > 0]

    # KPI CARDS
    total_revenue = df['total_paid'].sum()
    total_nights = df['nights_stayed'].sum()
    total_bookings = df['booking_id'].nunique()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Revenue", f"GH₵ {total_revenue:,.2f}")
    col2.metric("Total Nights Booked", f"{total_nights:,}")
    col3.metric("Total Bookings", f"{total_bookings:,}")

    st.divider()

    # MAIN CHART
    fig_trend = px.area(
        trend_df, x='check_in_date', y='total_paid',
        title=f"Revenue Trend ({time_grouping}ly)",
        labels={'check_in_date': 'Check-In Date', 'total_paid': 'Revenue (GH₵)'},
        color_discrete_sequence=['#8338ec'] # Luxury purple
    )
    fig_trend.update_traces(hovertemplate="<b>Date:</b> %{x}<br><b>Revenue:</b> GH₵ %{y:,.2f}<extra></extra>")
    fig_trend.update_layout(xaxis_title="", yaxis_title="")
    st.plotly_chart(fig_trend, use_container_width=True)

    st.divider()

    # BOTTOM ROW
    st.subheader("🛏️ Room Performance")
    
    room_popularity = df.groupby('room_type')['nights_stayed'].sum().reset_index().sort_values(by='nights_stayed', ascending=False)
    room_revenue = df.groupby('room_type')['total_paid'].sum().reset_index()

    col_left, col_right = st.columns(2)
    with col_left:
        fig_bar = px.bar(
            room_popularity.sort_values(by='nights_stayed', ascending=True), 
            x='nights_stayed', y='room_type', orientation='h',
            title="Most Popular Rooms (By Nights Booked)",
            color_discrete_sequence=['#3a86ff']
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_right:
        fig_donut = px.pie(
            room_revenue, values='total_paid', names='room_type', hole=0.4,
            title="Revenue Share by Room Type"
        )
        fig_donut.update_traces(textinfo='percent', hovertemplate="<b>%{label}</b><br>Revenue: GH₵ %{value:,.2f}<extra></extra>")
        st.plotly_chart(fig_donut, use_container_width=True)