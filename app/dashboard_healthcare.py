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
    # 1. UPDATED SQL: Querying consultation_fee_ghs from Silver layer
    query = """
        SELECT 
            visit_date, 
            patient_id, 
            diagnosis, 
            treatment_type, 
            consultation_fee_ghs
        FROM silver.silver_healthcare_clean
    """
    df = pd.read_sql(query, engine)
    df['visit_date'] = pd.to_datetime(df['visit_date'])
    return df

def render_dashboard(company_id):
    with st.spinner("Analyzing patient records..."):
        try:
            df = fetch_healthcare_data()
        except Exception as e:
            st.error(f"⚠️ CRASH DETAILS: {e}")
            return

    if df.empty:
        st.info("No healthcare data found. Please upload your raw data.")
        return

    # --- ADVANCED METRICS CALCULATION ---
    total_revenue = df['consultation_fee_ghs'].sum()
    total_visits = len(df)
    total_patients = df['patient_id'].nunique()
    
    avg_fee = total_revenue / total_visits if total_visits > 0 else 0
    return_rate = ((total_visits - total_patients) / total_visits) * 100 if total_visits > 0 else 0

    # --- TOP ROW: EXECUTIVE KPI CARDS ---
    st.markdown("### 🏥 Enterprise Clinic Command Center")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    col1.metric("Total Clinic Revenue", f"GH₵ {total_revenue:,.0f}")
    col2.metric("Total Visits", f"{total_visits:,}")
    col3.metric("Unique Patients", f"{total_patients:,}")
    col4.metric("Avg Revenue / Visit", f"GH₵ {avg_fee:,.2f}")
    col5.metric("Patient Return Rate", f"{return_rate:.1f}%")

    st.divider()

    # --- SAAS TABBED LAYOUT ---
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Executive Overview", 
        "🩺 Clinical Intelligence", 
        "💊 Treatment Economics",
        "📅 Patient Flow"
    ])

    # === TAB 1: EXECUTIVE OVERVIEW ===
    with tab1:
        col_chart_title, col_toggle, col_ai = st.columns([2, 1, 1])
        with col_chart_title:
            time_grouping = st.radio("Group Data By:", options=["Day", "Week", "Month"], horizontal=True, key="hc_time")
        with col_ai:
            enable_ai = st.toggle("🤖 Enable AI Forecast", key="hc_ai")

        df_time = df.set_index('visit_date')
        
        if time_grouping == "Day":
            trend_df = df_time.resample('D').agg({'consultation_fee_ghs': 'sum', 'patient_id': 'nunique'}).reset_index()
            periods, freq_code = 7, 'D'
        elif time_grouping == "Week":
            trend_df = df_time.resample('W-MON').agg({'consultation_fee_ghs': 'sum', 'patient_id': 'nunique'}).reset_index()
            periods, freq_code = 4, 'W'
        else:
            trend_df = df_time.resample('ME').agg({'consultation_fee_ghs': 'sum', 'patient_id': 'nunique'}).reset_index()
            periods, freq_code = 3, 'M'
            
        trend_df = trend_df[trend_df['consultation_fee_ghs'] > 0]

        if enable_ai:
            with st.spinner("AI is analyzing clinic historical trends..."):
                plot_df = ai_forecasting.generate_forecast(
                    trend_df, date_col='visit_date', metric_col='consultation_fee_ghs', forecast_periods=periods, freq=freq_code
                )
                fig_trend = px.line(
                    plot_df, x='visit_date', y='predicted_value', color='Type', line_dash='Type',
                    color_discrete_map={'Historical Data': '#008080', 'Forecast (AI)': '#006666'},
                    labels={'visit_date': 'Date', 'predicted_value': 'Revenue (GH₵)'}
                )
        else:
            fig_trend = px.area(
                trend_df, x='visit_date', y='consultation_fee_ghs',
                labels={'visit_date': 'Date', 'consultation_fee_ghs': 'Revenue (GH₵)'},
                color_discrete_sequence=['#008080']
            )

        fig_trend.update_traces(hovertemplate="<b>Date:</b> %{x}<br><b>Revenue:</b> GH₵ %{y:,.2f}<extra></extra>")
        fig_trend.update_layout(xaxis_title="", yaxis_title="")
        st.plotly_chart(fig_trend, use_container_width=True)

    # === TAB 2: CLINICAL INTELLIGENCE ===
    with tab2:
        # Group by Diagnosis for both Volume AND Revenue
        diag_stats = df.groupby('diagnosis').agg(
            patient_count=('patient_id', 'count'),
            revenue=('consultation_fee_ghs', 'sum')
        ).reset_index().sort_values(by='patient_count', ascending=False)
        
        col_vol, col_rev = st.columns(2)
        with col_vol:
            fig_diag_vol = px.bar(
                diag_stats.head(10).sort_values(by='patient_count', ascending=True), 
                x='patient_count', y='diagnosis', orientation='h',
                title="Top Diagnoses (By Patient Volume)",
                labels={'patient_count': 'Number of Cases', 'diagnosis': ''},
                color_discrete_sequence=['#006666']
            )
            st.plotly_chart(fig_diag_vol, use_container_width=True)
            
        with col_rev:
            fig_diag_rev = px.bar(
                diag_stats.sort_values(by='revenue', ascending=False).head(10).sort_values(by='revenue', ascending=True), 
                x='revenue', y='diagnosis', orientation='h',
                title="Top Diagnoses (By Revenue Generated)",
                labels={'revenue': 'Total Revenue (GH₵)', 'diagnosis': ''},
                color_discrete_sequence=['#2F4F4F']
            )
            st.plotly_chart(fig_diag_rev, use_container_width=True)

        st.subheader("Deep Dive: Diagnosis Roster")
        st.dataframe(
            diag_stats.head(15),
            column_config={
                "diagnosis": st.column_config.TextColumn("Condition / Diagnosis"),
                "patient_count": st.column_config.NumberColumn("Total Cases"),
                "revenue": st.column_config.ProgressColumn("Revenue Yield (GH₵)", format="GH₵ %f", min_value=0, max_value=float(diag_stats['revenue'].max())),
            },
            hide_index=True,
            use_container_width=True
        )

    # === TAB 3: TREATMENT ECONOMICS ===
    with tab3:
        treat_stats = df.groupby('treatment_type').agg(
            revenue=('consultation_fee_ghs', 'sum'),
            avg_fee=('consultation_fee_ghs', 'mean')
        ).reset_index()

        col_share, col_avg = st.columns(2)
        with col_share:
            fig_donut = px.pie(
                treat_stats, values='revenue', names='treatment_type', hole=0.4,
                title="Revenue Share by Treatment Type"
            )
            fig_donut.update_traces(textinfo='percent', hovertemplate="<b>%{label}</b><br>Revenue: GH₵ %{value:,.2f}<extra></extra>")
            st.plotly_chart(fig_donut, use_container_width=True)
            
        with col_avg:
            fig_avg = px.bar(
                treat_stats.sort_values(by='avg_fee', ascending=True),
                x='avg_fee', y='treatment_type', orientation='h',
                title="Average Revenue per Treatment Type",
                labels={'avg_fee': 'Avg Revenue (GH₵)', 'treatment_type': ''},
                color_discrete_sequence=['#008080'],
                text='avg_fee'
            )
            fig_avg.update_traces(texttemplate='GH₵ %{text:,.2f}', textposition='inside', insidetextanchor='middle')
            st.plotly_chart(fig_avg, use_container_width=True)

    # === TAB 4: PATIENT FLOW ===
    with tab4:
        st.subheader("Clinic Traffic Analysis")
        
        # Extract day of the week
        df['day_of_week'] = df['visit_date'].dt.day_name()
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        # Count visits per day
        traffic_stats = df.groupby('day_of_week')['patient_id'].count().reindex(day_order).reset_index()
        traffic_stats['patient_id'] = traffic_stats['patient_id'].fillna(0)
        
        fig_traffic = px.bar(
            traffic_stats, x='day_of_week', y='patient_id',
            title="Patient Volume by Day of the Week",
            labels={'day_of_week': '', 'patient_id': 'Number of Visits'},
            color_discrete_sequence=['#006666']
        )
        st.plotly_chart(fig_traffic, use_container_width=True)