import streamlit as st
import pandas as pd
import io
import os
import boto3
import requests
from datetime import datetime
from streamlit_lottie import st_lottie
from load_to_bronze import process_minio_to_bronze
import navigation

TEMPLATES = {
    "Retail": ["Date", "Receipt_ID", "Item_Name", "Quantity", "Unit_Cost", "Unit_Price"],
    "Healthcare": ["Date", "Patient_ID", "Diagnosis", "Treatment_Type", "Consultation_Fee"],
    "Hospitality": ["Date", "Booking_ID", "Room_Type", "Nights_Stayed", "Total_Paid"]
}

COLUMN_DESCRIPTIONS = {
    "Retail": {
        "Date": "When transaction occurred (tracks seasonal trends & AI forecast).",
        "Receipt_ID": "Unique checkout receipt number to compute basket sizes & AOV.",
        "Item_Name": "Exact SKU or product description sold.",
        "Quantity": "Total volume of items purchased per line item.",
        "Unit_Cost": "Cost of goods sold (COGS) to calculate gross margins.",
        "Unit_Price": "Retail selling price paid by customer."
    },
    "Healthcare": {
        "Date": "Admission or visit date for epidemiological tracking.",
        "Patient_ID": "Unique patient record key to calculate retention & visit volume.",
        "Diagnosis": "Primary condition diagnosed for resource mapping.",
        "Treatment_Type": "Departmental service rendered.",
        "Consultation_Fee": "Final charged amount for patient encounter."
    },
    "Hospitality": {
        "Date": "Check-in date driving ADR and occupancy forecasts.",
        "Booking_ID": "Reservation ID to prevent duplicate revenue counting.",
        "Room_Type": "Category of suite or standard room booked.",
        "Nights_Stayed": "Length of stay to compute ALOS metrics.",
        "Total_Paid": "Final folio total for ADR calculations."
    }
}

def load_lottieurl(url: str):
    try:
        r = requests.get(url, timeout=5)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None

def save_to_minio(file_bytes, filename):
    try:
        minio_user = os.environ.get("MINIO_ROOT_USER", "minioadmin")
        minio_password = os.environ.get("MINIO_ROOT_PASSWORD", "minioadmin")
        s3 = boto3.client(
            's3', endpoint_url='http://minio:9000',
            aws_access_key_id=minio_user, aws_secret_access_key=minio_password
        )
        bucket_name = "omnipulse-raw-data"
        try:
            s3.head_bucket(Bucket=bucket_name)
        except:
            s3.create_bucket(Bucket=bucket_name)

        s3.upload_fileobj(io.BytesIO(file_bytes), bucket_name, filename)
        return True
    except Exception as e:
        st.error(f"Data Lake Error: {e}")
        return False

def process_and_upload(df, expected_columns, company_id, industry, filename):
    final_df = df[expected_columns].copy()
    final_df['company_id'] = company_id
    
    csv_bytes = final_df.to_csv(index=False).encode('utf-8')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    secure_filename = f"{company_id}_{industry}_{timestamp}_{filename}"
    
    if save_to_minio(csv_bytes, secure_filename):
        anim_container = st.empty()
        with anim_container.container():
            st.markdown("<h4 style='text-align: center; color: #0F172A;'>🤖 Automating Pipeline: Cleaning & calculating metrics...</h4>", unsafe_allow_html=True)
            lottie_processing = load_lottieurl("https://lottie.host/80dc1de6-fa2c-4903-b097-4c40ebcb1e83/8E5qF41K3P.json")
            if lottie_processing:
                st_lottie(lottie_processing, height=180, key="data_loading")
        
        try:
            process_minio_to_bronze()
            anim_container.empty()
            st.session_state["active_page"] = "Data Preview"
            st.rerun()
        except Exception as e:
            anim_container.empty()
            st.error(f"⚠️ Pipeline execution failed: {e}")

def show_ingestion_page():
    company_id = st.session_state.get("company_id", "MC-001")
    company_name = st.session_state.get("company_name", "Enterprise Workspace")
    industry = st.session_state.get("industry", "Retail").capitalize()

    # Top Header
    navigation.render_top_header(
        title="📥 Data Ingestion Portal",
        subtitle=f"Workspace: <strong style='color:#0F172A;'>{company_name}</strong> &nbsp;•&nbsp; Schema: <strong style='color:#6C8DFF;'>{industry}</strong>"
    )

    # --- STEP 1: GUIDELINES & SCHEMA DOWNLOAD ---
    st.markdown(f"""
        <div class="orbit-card">
            <h3 style="margin-top:0; font-weight:800; font-size:1.15rem; color:#0F172A;">📋 Step 1: Industry Data Guidelines</h3>
            <p style="color:#64748B; font-size:0.9rem; margin-bottom:14px;">
                Ensure your dataset contains the required fields for the <b>{industry}</b> pipeline:
            </p>
    """, unsafe_allow_html=True)

    # Column Chips
    tags_html = " ".join([f"<span style='background:#EEF2FF; color:#4F46E5; border:1px solid #C7D2FE; font-weight:700; font-size:0.78rem; padding:5px 12px; border-radius:12px; display:inline-block; margin:3px;'>✓ {col}</span>" for col in TEMPLATES[industry]])
    st.markdown(f"<div style='margin-bottom:16px;'>{tags_html}</div>", unsafe_allow_html=True)

    with st.expander(f"💡 Why do we need these specific {industry} fields?"):
        for col, desc in COLUMN_DESCRIPTIONS[industry].items():
            st.markdown(f"- **`{col}`**: {desc}")

    template_df = pd.DataFrame(columns=TEMPLATES[industry])
    template_csv = template_df.to_csv(index=False).encode('utf-8')
    
    st.download_button(
        label=f"⬇️ Download {industry} Template (.csv)",
        data=template_csv,
        file_name=f"{industry.lower()}_schema_template.csv",
        mime="text/csv"
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # --- STEP 2: DROPZONE ---
    st.markdown("""
        <div class="orbit-card">
            <h3 style="margin-top:0; font-weight:800; font-size:1.15rem; color:#0F172A;">📤 Step 2: Upload File</h3>
            <p style="color:#64748B; font-size:0.9rem; margin-bottom:16px;">Drag and drop your spreadsheet (.csv or .xlsx, max 10MB)</p>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Upload Data File", type=["csv", "xlsx"], label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)

    # --- STEP 3: VALIDATION & MAPPING ---
    if uploaded_file is not None:
        file_size_mb = uploaded_file.size / (1024 * 1024)
        if file_size_mb > 10.0:
            st.error(f"❌ File limit exceeded ({file_size_mb:.1f}MB). Max allowed: 10MB.")
            return

        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
        except Exception:
            st.error("⚠️ Could not parse file. Ensure it is a valid CSV or Excel document.")
            return

        expected_columns = TEMPLATES[industry]
        uploaded_columns = list(df.columns)
        missing_columns = [col for col in expected_columns if col not in uploaded_columns]

        st.markdown("""
            <div class="orbit-card">
                <h3 style="margin-top:0; font-weight:800; font-size:1.15rem; color:#0F172A;">⚡ Step 3: Validation & Synchronization</h3>
        """, unsafe_allow_html=True)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("File Size", f"{file_size_mb:.2f} MB")
        m2.metric("Total Rows", f"{len(df):,}")
        m3.metric("Columns", f"{len(uploaded_columns)}")
        m4.metric("Status", "Aligned" if not missing_columns else "Mapping Needed")

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

        if not missing_columns:
            st.success("✅ Perfect Match! All mandatory schema columns are present.")
            if st.button("🚀 Push to Bronze & Launch Pipeline", type="primary", use_container_width=True):
                process_and_upload(df, expected_columns, company_id, industry, uploaded_file.name)
        else:
            st.warning(f"⚠️ {len(missing_columns)} column(s) require manual field mapping.")
            with st.form("mapping_form"):
                mapping_dict = {}
                for expected_col in expected_columns:
                    default_index = uploaded_columns.index(expected_col) if expected_col in uploaded_columns else 0
                    mapping_dict[expected_col] = st.selectbox(
                        f"Which uploaded column matches '{expected_col}'?",
                        options=uploaded_columns,
                        index=default_index,
                        help=COLUMN_DESCRIPTIONS[industry][expected_col] 
                    )
                
                if st.form_submit_button("Confirm Mapping & Ingest Data", type="primary", use_container_width=True):
                    rename_map = {mapping_dict[k]: k for k in mapping_dict}
                    mapped_df = df.rename(columns=rename_map)
                    process_and_upload(mapped_df, expected_columns, company_id, industry, uploaded_file.name)

        st.markdown("</div>", unsafe_allow_html=True)