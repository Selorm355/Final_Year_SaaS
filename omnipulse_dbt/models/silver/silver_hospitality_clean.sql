{{ config(materialized='table', tags=['hospitality']) }}

{% if table_exists('bronze', 'bronze_hospitality_data') %}

WITH raw_hospitality AS (
    SELECT * FROM {{ source('raw_data', 'bronze_hospitality_data') }}
),

cleaned_hospitality AS (
    SELECT
        company_id,
        CASE 
            WHEN "Date" LIKE '%/%' THEN TO_DATE("Date", 'DD/MM/YYYY')
            ELSE CAST("Date" AS DATE)
        END AS check_in_date,
        CAST("Booking_ID" AS VARCHAR)           AS booking_id,
        CAST("Room_Type" AS VARCHAR)            AS room_type,
        CAST("Nights_Stayed" AS INTEGER)        AS nights_stayed,
        CAST("Total_Paid" AS DECIMAL(10, 2))    AS total_paid
    FROM raw_hospitality
    WHERE "Booking_ID" IS NOT NULL 
      AND "Nights_Stayed" > 0
)

SELECT DISTINCT * FROM cleaned_hospitality

{% else %}

-- Bronze table not loaded yet — return empty shell so pipeline doesn't crash
SELECT
    NULL::VARCHAR       AS company_id,
    NULL::DATE          AS check_in_date,
    NULL::VARCHAR       AS booking_id,
    NULL::VARCHAR       AS room_type,
    NULL::INTEGER       AS nights_stayed,
    NULL::DECIMAL(10,2) AS total_paid
WHERE 1 = 0

{% endif %}