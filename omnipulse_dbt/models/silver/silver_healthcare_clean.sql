{{ config(materialized='table', tags=['healthcare']) }}

{% if table_exists('bronze', 'bronze_healthcare_data') %}

WITH raw_healthcare AS (
    SELECT * FROM {{ source('raw_data', 'bronze_healthcare_data') }}
),

cleaned_healthcare AS (
    SELECT
        company_id,
        CASE 
            WHEN "Date" LIKE '%/%' THEN TO_DATE("Date", 'DD/MM/YYYY')
            ELSE CAST("Date" AS DATE)
        END AS visit_date,
        CAST("Patient_ID" AS VARCHAR)       AS patient_id,
        CAST("Diagnosis" AS VARCHAR)        AS diagnosis,
        CAST("Treatment_Type" AS VARCHAR)   AS treatment_type,
        
        -- Renamed to reflect Ghana Cedis and enforce decimal places
        CAST("Consultation_Fee" AS DECIMAL(10, 2)) AS consultation_fee_ghs
        
    FROM raw_healthcare
    WHERE "Patient_ID" IS NOT NULL 
      AND "Consultation_Fee" >= 0
)

SELECT DISTINCT * FROM cleaned_healthcare

{% else %}

-- Bronze table not loaded yet — return empty shell so pipeline doesn't crash
SELECT
    NULL::VARCHAR       AS company_id,
    NULL::DATE          AS visit_date,
    NULL::VARCHAR       AS patient_id,
    NULL::VARCHAR       AS diagnosis,
    NULL::VARCHAR       AS treatment_type,
    NULL::DECIMAL(10,2) AS consultation_fee_ghs
WHERE 1 = 0

{% endif %}