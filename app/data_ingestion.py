import streamlit as st
import pandas as pd
import io
import os
import boto3
from datetime import datetime

# --- 1. INDUSTRY TEMPLATES (The Data Contract) ---
# These dictate exactly what columns we expect from each SME type
TEMPLATES = {
    "Retail": ["Date", "Receipt_ID", "Item_Name", "Quantity", "Unit_Cost", "Unit_Price"],
    "Healthcare": ["Date", "Patient_ID", "Diagnosis", "Treatment_Type", "Consultation_Fee"],
    "Hospitality": ["Date", "Booking_ID", "Room_Type", "Nights_Stayed", "Total_Paid"]
}

# --- 2. THE MINIO DATA LAKE CONNECTOR ---
def save_to_minio(file_bytes, filename):
    """Saves the raw, untouched file into the MinIO Data Lake."""
    try:
        # We use strictly the .env variables. If they are missing, it throws a safe error.
        minio_user = os.environ["MINIO_ROOT_USER"]
        minio_password = os.environ["MINIO_ROOT_PASSWORD"]

        # Connect to the local MinIO container
        s3 = boto3.client(
            's3',
            endpoint_url='http://localhost:9000', 
            aws_access_key_id=minio_user,
            aws_secret_access_key=minio_password
        )
        
        # Ensure the bucket exists
        bucket_name = "omnipulse-raw-data"
        try:
            s3.head_bucket(Bucket=bucket_name)
        except:
            s3.create_bucket(Bucket=bucket_name)

        # Upload the file
        s3.upload_fileobj(io.BytesIO(file_bytes), bucket_name, filename)
        return True
    
    except KeyError:
        st.error("🚨 Server Configuration Error: MinIO credentials not found in .env file.")
        return False
    except Exception as e:
        st.error(f"Data Lake Error: {e}")
        return False

# --- 3. THE MAIN UI & LOGIC ---
def show_ingestion_page():
    # THE GATEKEEPER: Kick out anyone who isn't logged in
    if not st.session_state.get("logged_in"):
        st.error("🚨 Access Denied. Please log in to access the Data Ingestion portal.")
        return

    # Grab the user's secure details from the invisible baton pass
    company_id = st.session_state["company_id"]
    industry = st.session_state["industry"]
    company_name = st.session_state["company_name"]

    st.title("📥 Data Ingestion Portal")
    st.write(f"Welcome, **{company_name}**. Upload your daily or monthly records here.")
    
    # --- TEMPLATE DOWNLOADER ---
    st.markdown("### 1. Download Your Template")
    st.info(f"To ensure your {industry} dashboard generates correctly, your data must match this exact format.")
    
    # Generate an empty CSV with the correct headers for their industry
    template_df = pd.DataFrame(columns=TEMPLATES[industry])
    template_csv = template_df.to_csv(index=False).encode('utf-8')
    
    st.download_button(
        label=f"⬇️ Download {industry} Data Template (.csv)",
        data=template_csv,
        file_name=f"{industry}_template.csv",
        mime="text/csv",
    )
    
    st.divider()

    # --- THE DROPZONE ---
    st.markdown("### 2. Upload Your Data")
    # Accept both CSV and Excel for great UX
    uploaded_file = st.file_uploader("Drag and drop your file here", type=["csv", "xlsx"])

    if uploaded_file is not None:
        # THE SIZE BOUNCER: Enforce the 10MB (approx. 100,000 row) limit
        file_size_mb = uploaded_file.size / (1024 * 1024)
        if file_size_mb > 10.0:
            st.error(f"❌ File too large ({file_size_mb:.1f}MB). Please limit uploads to 10MB (approx. 100,000 rows).")
            return

        with st.spinner("Validating data..."):
            try:
                # Read the file based on its extension
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    # THE EXCEL GRACEFUL FAILURE
                    df = pd.read_excel(uploaded_file)

                # THE COLUMN BOUNCER: Check if they used the template
                expected_columns = TEMPLATES[industry]
                uploaded_columns = list(df.columns)

                # Check if all expected columns exist in the uploaded file
                missing_columns = [col for col in expected_columns if col not in uploaded_columns]
                
                if missing_columns:
                    st.error(f"❌ Validation Failed: Your file is missing the following required columns: **{', '.join(missing_columns)}**")
                    st.warning("Please download the template above, paste your data into it, and try again.")
                    return

                # --- MULTI-TENANT TAGGING ---
                # Append the company_id to every single row so data never mixes
                df['company_id'] = company_id
                
                st.success("✅ File format verified!")

                # --- SAVE TO DATA LAKE (MinIO) ---
                # Rename the file to include their ID and a timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                secure_filename = f"{company_id}_{industry}_{timestamp}_{uploaded_file.name}"
                
                # If they uploaded an Excel file, convert it to pure CSV text for the Data Lake
                csv_bytes = df.to_csv(index=False).encode('utf-8')
                
                lake_success = save_to_minio(csv_bytes, secure_filename)

                if lake_success:
                    st.success(f"🌊 Raw file securely backed up to Data Lake as `{secure_filename}`.")
                    
                    # FUTURE STEP: Push `df` to PostgreSQL!
                    st.info("🔄 Pipeline Step: Data is ready to be loaded into PostgreSQL Bronze Layer! (Pending DB Connection Update).")

            except Exception as e:
                # If Pandas crashes on a heavily formatted Excel file
                st.error("⚠️ We couldn't read this file. If it is an Excel file with complex formatting, please open it, click 'Save As -> CSV', and upload the new CSV file.")
                st.caption(f"Technical Error: {e}")