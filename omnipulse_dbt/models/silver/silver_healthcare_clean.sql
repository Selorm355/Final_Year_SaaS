{{ config(materialized='table', tags=['healthcare']) }}

{% if table_exists('bronze', 'bronze_healthcare_data') %}

WITH raw_healthcare AS (
    SELECT * FROM {{ source('raw_data', 'bronze_healthcare_data') }}
),

-- PHASE 1: THE WASH CYCLE 
text_cleaning AS (
    SELECT
        company_id,
        
        SUBSTRING(TRIM("Date") FROM 1 FOR 10) AS raw_date,
        
        UPPER(TRIM("Patient_ID")) AS patient_id_clean,
        INITCAP(TRIM("Diagnosis")) AS diagnosis_clean,
        INITCAP(TRIM("Treatment_Type")) AS treatment_clean,
        
        NULLIF(
            REGEXP_REPLACE(TRIM("Consultation_Fee"), '[^0-9\.]', '', 'g'), 
        '') AS fee_str

    FROM raw_healthcare
),

-- PHASE 2: TYPE CASTING
type_casting AS (
    SELECT
        company_id,
        
        CASE 
            WHEN raw_date IS NULL OR raw_date = '' THEN NULL
            WHEN raw_date LIKE '202%-%' THEN CAST(raw_date AS DATE)
            WHEN raw_date LIKE '202%.%' THEN TO_DATE(raw_date, 'YYYY.MM.DD')
            WHEN raw_date LIKE '202%/%' THEN TO_DATE(raw_date, 'YYYY/MM/DD')
            WHEN raw_date LIKE '% %' THEN TO_DATE(raw_date, 'Mon DD, YYYY')
            WHEN raw_date LIKE '%/%/%' THEN 
                CASE 
                    WHEN SPLIT_PART(raw_date, '/', 2)::INT > 12 THEN TO_DATE(raw_date, 'MM/DD/YYYY')
                    WHEN SPLIT_PART(raw_date, '/', 1)::INT > 12 THEN TO_DATE(raw_date, 'DD/MM/YYYY')
                    ELSE TO_DATE(raw_date, 'DD/MM/YYYY')
                END
            ELSE CAST(raw_date AS DATE)
        END AS visit_date,
        
        patient_id_clean AS patient_id,
        diagnosis_clean AS diagnosis,
        treatment_clean AS treatment_type,
        
        -- UPDATED ALIAS HERE
        CAST(fee_str AS DECIMAL(10, 2)) AS consultation_fee_ghs
        
    FROM text_cleaning
)

-- PHASE 3: THE GATEKEEPER
SELECT DISTINCT * 
FROM type_casting
WHERE patient_id IS NOT NULL 
  AND consultation_fee_ghs >= 0  -- UPDATED FILTER HERE
  AND EXTRACT(YEAR FROM visit_date) > 2000

{% else %}

-- Bronze table not loaded yet 
SELECT
    NULL::VARCHAR       AS company_id,
    NULL::DATE          AS visit_date,
    NULL::VARCHAR       AS patient_id,
    NULL::VARCHAR       AS diagnosis,
    NULL::VARCHAR       AS treatment_type,
    NULL::DECIMAL(10,2) AS consultation_fee_ghs -- UPDATED ALIAS HERE
WHERE 1 = 0

{% endif %}