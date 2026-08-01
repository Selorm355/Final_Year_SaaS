import streamlit as st
import pandas as pd
import io
import os
import boto3
import requests
from streamlit_lottie import st_lottie
from datetime import datetime
from load_to_bronze import process_minio_to_bronze

# --- 1. INDUSTRY TEMPLATES & DICTIONARY ---
TEMPLATES = {
    "Retail": ["Date", "Receipt_ID", "Item_Name", "Quantity", "Unit_Cost", "Unit_Price"],
    "Healthcare": ["Date", "Patient_ID", "Diagnosis", "Treatment_Type", "Consultation_Fee"],
    "Hospitality": ["Date", "Booking_ID", "Room_Type", "Nights_Stayed", "Total_Paid"]
}

COLUMN_DESCRIPTIONS = {
    "Retail": {
        "Date": "When the transaction occurred. Needed for daily sales tracking and seasonal AI predictions.",
        "Receipt_ID": "A unique ID for the transaction. Helps calculate Average Order Value per customer.",
        "Item_Name": "The product sold. Used to identify your top-selling inventory.",
        "Quantity": "How many units were sold in this single transaction.",
        "Unit_Cost": "What YOU paid for the item. Crucial for calculating your actual Profit Margins.",
        "Unit_Price": "What the CUSTOMER paid for the item. Drives your gross revenue metrics."
    },
    "Healthcare": {
        "Date": "When the patient visited. Needed to track seasonal health/epidemiology trends.",
        "Patient_ID": "Unique identifier for the patient. Helps calculate retention and return-visit rates.",
        "Diagnosis": "The medical condition diagnosed. Used for condition-tracking charts.",
        "Treatment_Type": "The service rendered (e.g., Lab Test, Consultation). Shows revenue by department.",
        "Consultation_Fee": "The final amount charged to the patient for the visit."
    },
    "Hospitality": {
        "Date": "The check-in date or transaction date. Drives seasonal demand and occupancy predictions.",
        "Booking_ID": "Unique identifier for the stay. Prevents duplicate revenue counting.",
        "Room_Type": "The category of room booked. Helps identify your most popular and profitable rooms.",
        "Nights_Stayed": "Duration of the stay. Needed to calculate Average Length of Stay (ALOS).",
        "Total_Paid": "The final bill amount. Used to calculate your Average Daily Rate (ADR)."
    }
}

# --- HELPER: LOTTIE ANIMATION LOADER ---
def load_lottieurl(url: str):
    """Fetches a Lottie animation JSON from a URL safely."""
    try:
        r = requests.get(url, timeout=5)
        if r.status_code != 200:
            return None
        return r.json()
    except Exception:
        return None

def inject_custom_css():
    """Reads the CSS file and injects it into Streamlit."""
    css_path = os.path.join(os.path.dirname(__file__), "global_style.css")
    try:
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass # Fails silently if the file isn't created yet

def save_to_minio(file_bytes, filename):
    try:
        minio_user = os.environ["MINIO_ROOT_USER"]
        minio_password = os.environ["MINIO_ROOT_PASSWORD"]

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
        st.success(f"🌊 Success! Cleaned file securely backed up to Data Lake as `{secure_filename}`.")
        
        # --- LOTTIE ANIMATION INTEGRATION ---
        animation_container = st.empty()
        
        with animation_container.container():
            st.markdown("<h4 style='text-align: center;'>🤖 Automating Pipeline: Cleaning & calculating metrics...</h4>", unsafe_allow_html=True)
            lottie_processing = load_lottieurl("https://lottie.host/80dc1de6-fa2c-4903-b097-4c40ebcb1e83/8E5qF41K3P.json")
            if lottie_processing:
                st_lottie(lottie_processing, height=200, key="data_loading")
        
        try:
            process_minio_to_bronze()
            animation_container.empty()
            st.session_state["go_to_page"] = "3. Data Preview"
            st.rerun()
        except Exception as e:
            animation_container.empty()
            st.error(f"⚠️ Pipeline execution failed: {e}")

# --- 3. THE MAIN UI WIZARD ---
def show_ingestion_page():
    inject_custom_css() # <-- Applies your violet theme immediately!
    
    if not st.session_state.get("logged_in"):
        st.error("🚨 Access Denied. Please log in to access the Data Ingestion portal.")
        return

    company_id = st.session_state["company_id"]
    industry = st.session_state["industry"]
    company_name = st.session_state["company_name"]

    st.title("📥 Data Ingestion Portal")
    st.write(f"Welcome, **{company_name}**. Power your analytics engine by uploading your records.")
    
    # --- WIZARD STEP 1 ---
    st.markdown("### Step 1: Data Guidelines")
    st.info(f"For the fastest processing, download our {industry} template. Otherwise, you can upload your own file and we will help you map your columns to our system.")
    
    with st.expander(f"💡 Why do we need these specific {industry} columns?"):
        for col, desc in COLUMN_DESCRIPTIONS[industry].items():
            st.markdown(f"- **{col}**: {desc}")

    template_df = pd.DataFrame(columns=TEMPLATES[industry])
    template_csv = template_df.to_csv(index=False).encode('utf-8')
    
    st.download_button(
        label=f"⬇️ Download Perfect {industry} Template (.csv)",
        data=template_csv, file_name=f"{industry}_template.csv", mime="text/csv",
        type="primary" # Applies your custom gradient button style!
    )
    st.divider()

    # --- WIZARD STEP 2 ---
    st.markdown("### Step 2: Upload Your File")
    uploaded_file = st.file_uploader("Drag and drop your file into the secure dropzone", type=["csv", "xlsx"])

    if uploaded_file is not None:
        file_size_mb = uploaded_file.size / (1024 * 1024)
        if file_size_mb > 10.0:
            st.error(f"❌ File too large ({file_size_mb:.1f}MB). Limit: 10MB.")
            return

        if "raw_data" not in st.session_state or st.session_state.get("uploaded_filename") != uploaded_file.name:
            try:
                if uploaded_file.name.endswith('.csv'):
                    st.session_state["raw_data"] = pd.read_csv(uploaded_file)
                else:
                    st.session_state["raw_data"] = pd.read_excel(uploaded_file)
                st.session_state["uploaded_filename"] = uploaded_file.name
            except Exception as e:
                st.error("⚠️ We couldn't read this file. Please ensure it is a valid CSV or Excel file.")
                return

        df = st.session_state["raw_data"]
        expected_columns = TEMPLATES[industry]
        uploaded_columns = list(df.columns)
        missing_columns = [col for col in expected_columns if col not in uploaded_columns]

        # --- WIZARD STEP 3 (Dynamic Metadata) ---
        st.markdown("### Step 3: Validation & Execution")
        
        # Sleek Data Snapshot Cards
        m1, m2, m3 = st.columns(3)
        m1.metric("File Size", f"{file_size_mb:.2f} MB")
        m2.metric("Total Rows Detected", f"{len(df):,}")
        m3.metric("Columns Detected", f"{len(uploaded_columns)}")
        st.write("") # Quick spacing

        if len(uploaded_columns) < len(expected_columns):
            st.error(f"❌ Insufficient Data: Your file only contains {len(uploaded_columns)} columns, but the {industry} dashboard requires at least {len(expected_columns)} distinct columns.")
            return

        if not missing_columns:
            st.success("✅ Perfect Match! We recognized all your columns.")
            if st.button("🚀 Process & Upload Data", type="primary"):
                process_and_upload(df, expected_columns, company_id, industry, uploaded_file.name)
        else:
            st.warning(f"⚠️ We found {len(missing_columns)} unrecognized columns. Let's map them below.")
            with st.form("mapping_form"):
                st.markdown("#### Map Your Columns")
                mapping_dict = {}
                for expected_col in expected_columns:
                    default_index = uploaded_columns.index(expected_col) if expected_col in uploaded_columns else 0
                    mapping_dict[expected_col] = st.selectbox(
                        f"Which column is **{expected_col}**?",
                        options=uploaded_columns, index=default_index,
                        help=COLUMN_DESCRIPTIONS[industry][expected_col] 
                    )
                
                submitted = st.form_submit_button("Confirm Mapping & Upload", type="primary")
                if submitted:
                    rename_map = {mapping_dict[k]: k for k in mapping_dict}
                    mapped_df = df.rename(columns=rename_map)
                    process_and_upload(mapped_df, expected_columns, company_id, industry, uploaded_file.name)