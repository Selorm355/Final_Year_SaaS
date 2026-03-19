WITH raw_healthcare AS (
    SELECT * FROM {{ source('raw_data', 'bronze_healthcare_data') }}
),

cleaned_healthcare AS (
    SELECT
        company_id,
        
        -- THE SMART PARSER: Handles both Excel's dashed format and the raw slashed format!
        CASE 
            WHEN "Date" LIKE '%/%' THEN TO_DATE("Date", 'DD/MM/YYYY')
            ELSE CAST("Date" AS DATE)
        END AS visit_date,
        
        CAST("Patient_ID" AS VARCHAR) AS patient_id,
        CAST("Diagnosis" AS VARCHAR) AS diagnosis,
        CAST("Treatment_Type" AS VARCHAR) AS treatment_type,
        CAST("Consultation_Fee" AS DECIMAL(10, 2)) AS consultation_fee
    FROM raw_healthcare
    WHERE "Patient_ID" IS NOT NULL 
      AND "Consultation_Fee" >= 0
)

SELECT DISTINCT *
FROM cleaned_healthcare