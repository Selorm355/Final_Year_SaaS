import streamlit as st
import pandas as pd
import plotly.express as px
import os
import ai_forecasting
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(f"postgresql://{os.environ.get('POSTGRES_USER')}:{os.environ.get('POSTGRES_PASSWORD')}@db:5432/{os.environ.get('POSTGRES_DB')}")

def fetch_healthcare_data():
    query = """
        SELECT 
            visit_date, 
            patient_id, 
            diagnosis, 
            treatment_type, 
            consultation_fee
        FROM silver.silver_healthcare_clean
    """
    df = pd.read_sql(query, engine)
    df['visit_date'] = pd.to_datetime(df['visit_date'])
    return df

def render_dashboard(company_id):
    with st.spinner("Analyzing patient records..."):
        try:
            df = fetch_healthcare_data()
        except Exception:
            st.error("⚠️ Could not load data. Please ingest your healthcare data first.")
            return

    if df.empty:
        st.info("No healthcare data found. Please upload your raw data.")
        return

    st.subheader("📈 Clinic Performance Trends")
    time_grouping = st.radio("Group Data By:", options=["Day", "Week", "Month"], horizontal=True, key="hc_time")

    df_time = df.set_index('visit_date')
    if time_grouping == "Day":
        trend_df = df_time.resample('D').agg({'consultation_fee': 'sum', 'patient_id': 'nunique'}).reset_index()
    elif time_grouping == "Week":
        trend_df = df_time.resample('W-MON').agg({'consultation_fee': 'sum', 'patient_id': 'nunique'}).reset_index()
    else:
        trend_df = df_time.resample('ME').agg({'consultation_fee': 'sum', 'patient_id': 'nunique'}).reset_index()
        
    trend_df = trend_df[trend_df['consultation_fee'] > 0]
    trend_df.rename(columns={'patient_id': 'unique_patients'}, inplace=True)

    # KPI CARDS
    total_revenue = df['consultation_fee'].sum()
    total_patients = df['patient_id'].nunique()
    avg_fee = total_revenue / total_patients if total_patients > 0 else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Clinic Revenue", f"GH₵ {total_revenue:,.2f}")
    col2.metric("Total Unique Patients", f"{total_patients:,}")
    col3.metric("Avg Revenue per Patient", f"GH₵ {avg_fee:,.2f}")

    st.divider()

    # MAIN CHART WITH AI INTEGRATION
    st.divider()
    col_chart_title, col_ai_toggle = st.columns([3, 1])
    
    with col_chart_title:
        st.subheader("⏱️ Revenue Trends & AI Prediction")
    with col_ai_toggle:
        enable_ai = st.toggle("🤖 Enable AI Forecast", key="hc_ai")

    if enable_ai:
        with st.spinner("AI is analyzing clinic historical trends..."):
            if time_grouping == "Day":
                periods, freq_code = 7, 'D'
            elif time_grouping == "Week":
                periods, freq_code = 4, 'W'
            else:
                periods, freq_code = 3, 'M'

            # Feed the brain the Healthcare columns!
            plot_df = ai_forecasting.generate_forecast(
                trend_df, 
                date_col='visit_date', 
                metric_col='consultation_fee',
                forecast_periods=periods,
                freq=freq_code
            )
            
            fig_trend = px.line(
                plot_df, x='visit_date', y='predicted_value', color='Type', line_dash='Type',
                color_discrete_map={'Historical Data': '#2a9d8f', 'Forecast (AI)': '#ff9f1c'},
                labels={'visit_date': 'Date', 'predicted_value': 'Revenue (GH₵)'}
            )
    else:
        fig_trend = px.area(
            trend_df, x='visit_date', y='consultation_fee',
            labels={'visit_date': 'Date', 'consultation_fee': 'Revenue (GH₵)'},
            color_discrete_sequence=['#2a9d8f'] 
        )

    fig_trend.update_traces(hovertemplate="<b>Date:</b> %{x}<br><b>Revenue:</b> GH₵ %{y:,.2f}<extra></extra>")
    fig_trend.update_layout(xaxis_title="", yaxis_title="")
    st.plotly_chart(fig_trend, use_container_width=True)

    # BOTTOM ROW
    st.subheader("🩺 Clinical Insights")
    
    top_diagnoses = df.groupby('diagnosis').size().reset_index(name='count').sort_values(by='count', ascending=False).head(10)
    treatment_revenue = df.groupby('treatment_type')['consultation_fee'].sum().reset_index()

    col_left, col_right = st.columns(2)
    with col_left:
        fig_bar = px.bar(
            top_diagnoses.sort_values(by='count', ascending=True), 
            x='count', y='diagnosis', orientation='h',
            title="Top 10 Most Common Diagnoses",
            color_discrete_sequence=['#e76f51']
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_right:
        fig_donut = px.pie(
            treatment_revenue, values='consultation_fee', names='treatment_type', hole=0.4,
            title="Revenue by Treatment Type"
        )
        fig_donut.update_traces(textinfo='percent', hovertemplate="<b>%{label}</b><br>Revenue: GH₵ %{value:,.2f}<extra></extra>")
        st.plotly_chart(fig_donut, use_container_width=True)