-- models/gold/gold_hospitality_metrics.sql

WITH clean_hospitality AS (
    SELECT * FROM {{ ref('silver_hospitality_clean') }}
)

SELECT
    company_id,
    check_in_date,
    
    -- Volume Metrics
    COUNT(DISTINCT booking_id) AS total_bookings,
    SUM(nights_stayed) AS total_nights_stayed,
    
    -- Financial Metrics
    SUM(total_paid) AS total_daily_revenue,
    
    -- ADR (Average Daily Rate) = Total Revenue / Total Nights
    CASE 
        WHEN SUM(nights_stayed) = 0 THEN 0 
        ELSE SUM(total_paid) / SUM(nights_stayed) 
    END AS average_daily_rate,

    -- ALOS (Average Length of Stay) = Total Nights / Total Bookings
    CASE 
        WHEN COUNT(DISTINCT booking_id) = 0 THEN 0 
        ELSE SUM(nights_stayed) / COUNT(DISTINCT booking_id) 
    END AS average_length_of_stay

FROM clean_hospitality
GROUP BY 
    company_id, 
    check_in_date