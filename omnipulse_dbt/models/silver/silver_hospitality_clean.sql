-- models/silver/silver_hospitality_clean.sql

WITH raw_hospitality AS (
    SELECT * FROM {{ source('raw_data', 'bronze_hospitality_data') }}
),

cleaned_hospitality AS (
    SELECT
        company_id,
        
        -- THE SMART PARSER: Handles both Excel's dashed format and raw slashed format
        CASE 
            WHEN "Date" LIKE '%/%' THEN TO_DATE("Date", 'DD/MM/YYYY')
            ELSE CAST("Date" AS DATE)
        END AS check_in_date,
        
        CAST("Booking_ID" AS VARCHAR) AS booking_id,
        CAST("Room_Type" AS VARCHAR) AS room_type,
        CAST("Nights_Stayed" AS INTEGER) AS nights_stayed,
        CAST("Total_Paid" AS DECIMAL(10, 2)) AS total_paid
    FROM raw_hospitality
    WHERE "Booking_ID" IS NOT NULL 
      AND "Nights_Stayed" > 0
)

SELECT DISTINCT *
FROM cleaned_hospitality