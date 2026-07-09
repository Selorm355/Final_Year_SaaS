-- models/gold/gold_healthcare_metrics.sql

WITH clean_healthcare AS (
    SELECT * FROM {{ ref('silver_healthcare_clean') }}
)

SELECT
    company_id,
    visit_date,
    
    -- Patient Metrics
    COUNT(DISTINCT patient_id) AS total_patients_seen,
    
    -- Financial Metrics
    SUM(consultation_fee_ghs) AS total_daily_revenue,
    
    -- Average Revenue Per Patient
    CASE 
        WHEN COUNT(DISTINCT patient_id) = 0 THEN 0 
        ELSE SUM(consultation_fee_ghs) / COUNT(DISTINCT patient_id) 
    END AS avg_revenue_per_patient

FROM clean_healthcare
GROUP BY 
    company_id, 
    visit_date