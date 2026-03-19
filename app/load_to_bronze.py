import os
import io
import boto3
import pandas as pd
import subprocess  # <-- NEW: The library that lets Python run terminal commands
import uuid  # <-- NEW: Built-in library to generate random unique IDs
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

MINIO_BUCKET = "omnipulse-raw-data"

s3 = boto3.client(
    's3',
    endpoint_url='http://minio:9000',
    aws_access_key_id=os.environ.get("MINIO_ROOT_USER"),
    aws_secret_access_key=os.environ.get("MINIO_ROOT_PASSWORD")
)

pg_user = os.environ.get("POSTGRES_USER")
pg_pass = os.environ.get("POSTGRES_PASSWORD")
pg_db = os.environ.get("POSTGRES_DB")

engine = create_engine(f"postgresql://{pg_user}:{pg_pass}@db:5432/{pg_db}")

def process_minio_to_bronze():
    print("🔍 Scanning MinIO Data Lake for new uploads...")
    
    try:
        response = s3.list_objects_v2(Bucket=MINIO_BUCKET)
        
        if 'Contents' not in response:
            print("✅ No new files found. Bronze layer is fully up to date.")
            return

        for obj in response['Contents']:
            filename = obj['Key']
            print(f"\n📥 Extracting: {filename}")
            
            parts = filename.split('_')
            if len(parts) < 2:
                print(f"⚠️ Skipping {filename}: Unrecognized naming convention.")
                continue
                
            industry = parts[1].lower() 
            table_name = f"bronze_{industry}_data"
            
            csv_obj = s3.get_object(Bucket=MINIO_BUCKET, Key=filename)
            df = pd.read_csv(io.BytesIO(csv_obj['Body'].read()))
            
            print(f"🚀 Loading {len(df)} rows into Postgres -> bronze.{table_name}...")
            
            # --- THIS IS THE CHANGE ---
            df.to_sql(
                name=table_name,
                con=engine,
                schema='bronze',
                if_exists='replace', # <-- CHANGED FROM 'append' TO FLUSH THE TABLE
                index=False
            )
            
            s3.delete_object(Bucket=MINIO_BUCKET, Key=filename)
            print(f"🧹 Success! Deleted {filename} from MinIO raw bucket.")

        print("\n🎉 ELT Extraction Complete! All data is securely in the PostgreSQL Bronze layer.")
        
        # --- THE AUTOMATED DBT TRIGGER ---
        print("\n🤖 Triggering dbt to calculate Silver and Gold layers...")
        
        dbt_command = [
            "dbt", "run", 
            "--project-dir", "omnipulse_dbt", 
            "--profiles-dir", "omnipulse_dbt"
        ]
        
        result = subprocess.run(dbt_command, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✨ dbt transformation successful! The Gold layer is ready for the dashboard.")
        else:
            error_code = f"ERR-{str(uuid.uuid4())[:6].upper()}"
            
            print("\n" + "="*50)
            print(f"❌ DBT TRANSFORMATION FAILED (Support Code: {error_code}):")
            print(result.stderr) 
            print("="*50 + "\n")
            
            # --- TEMPORARY DEBUGGING OVERRIDE (Kept exactly as you requested) ---
            raise Exception(f"DEBUGGING DBT ERROR:\n{result.stdout}\n{result.stderr}")
            
    except Exception as e:
        print(f"🚨 Pipeline Error: {e}")
        raise e  

if __name__ == "__main__":
    process_minio_to_bronze()