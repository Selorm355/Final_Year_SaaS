{{ config(materialized='table', tags=['hospitality']) }}

{% if table_exists('bronze', 'bronze_hospitality_data') %}

WITH raw_hospitality AS (
    SELECT * FROM {{ source('raw_data', 'bronze_hospitality_data') }}
),

-- PHASE 1: THE WASH CYCLE 
-- Clean and standardize text strings before attempting any mathematical casts
text_cleaning AS (
    SELECT
        company_id,
        
        -- Isolate the date part, stripping off any rogue timestamps (00:00:00)
        SUBSTRING(TRIM("Date") FROM 1 FOR 10) AS raw_date,
        
        -- Standardize text casing and remove trailing spaces
        UPPER(TRIM("Booking_ID")) AS booking_id_clean,
        INITCAP(TRIM("Room_Type")) AS room_type_clean,
        
        -- Translate string words to numbers, then use Regex to strip all letters/spaces
        NULLIF(
            REGEXP_REPLACE(
                REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(LOWER(TRIM("Nights_Stayed")), 
                'one', '1'), 'two', '2'), 'three', '3'), 'four', '4'), 'five', '5'),
            '[^0-9]', '', 'g'), 
        '') AS nights_stayed_str,
        
        -- Use Regex to strip all currency symbols (GH₵, $, £) keeping only digits and decimals
        NULLIF(
            REGEXP_REPLACE(TRIM("Total_Paid"), '[^0-9\.]', '', 'g'), 
        '') AS total_paid_str

    FROM raw_hospitality
),

-- PHASE 2: TYPE CASTING
type_casting AS (
    SELECT
        company_id,
        
        -- Advanced date parsing to handle chaotic CSV formats
        CASE 
            WHEN raw_date IS NULL OR raw_date = '' THEN NULL
            -- Format: YYYY-MM-DD
            WHEN raw_date LIKE '202%-%' THEN CAST(raw_date AS DATE)
            -- Format: YYYY/MM/DD
            WHEN raw_date LIKE '202%/%' THEN TO_DATE(raw_date, 'YYYY/MM/DD')
            -- Format: Mon DD, YYYY (e.g., Mar 05, 2026)
            WHEN raw_date LIKE '% %' THEN TO_DATE(raw_date, 'Mon DD, YYYY')
            -- Format: MM/DD/YYYY vs DD/MM/YYYY
            WHEN raw_date LIKE '%/%/%' THEN 
                CASE 
                    -- If the middle number is > 12, it MUST be MM/DD/YYYY (e.g., 11/23/2025)
                    WHEN SPLIT_PART(raw_date, '/', 2)::INT > 12 THEN TO_DATE(raw_date, 'MM/DD/YYYY')
                    -- If the first number is > 12, it MUST be DD/MM/YYYY (e.g., 23/11/2025)
                    WHEN SPLIT_PART(raw_date, '/', 1)::INT > 12 THEN TO_DATE(raw_date, 'DD/MM/YYYY')
                    -- Default fallback for ambiguous dates (e.g., 05/06/2025)
                    ELSE TO_DATE(raw_date, 'DD/MM/YYYY')
                END
            ELSE CAST(raw_date AS DATE)
        END AS check_in_date,
        
        booking_id_clean AS booking_id,
        room_type_clean AS room_type,
        
        CAST(nights_stayed_str AS INTEGER) AS nights_stayed,
        CAST(total_paid_str AS DECIMAL(10, 2)) AS total_paid_ghs
        
    FROM text_cleaning
)
-- PHASE 3: THE GATEKEEPER
-- Apply the mathematical filters safely on the newly casted columns and ban ancient dates
SELECT DISTINCT * 
FROM type_casting
WHERE booking_id IS NOT NULL 
  AND nights_stayed > 0
  AND EXTRACT(YEAR FROM check_in_date) > 2000

{% else %}

-- Bronze table not loaded yet — return empty shell so pipeline doesn't crash
SELECT
    NULL::VARCHAR       AS company_id,
    NULL::DATE          AS check_in_date,
    NULL::VARCHAR       AS booking_id,
    NULL::VARCHAR       AS room_type,
    NULL::INTEGER       AS nights_stayed,
    NULL::DECIMAL(10,2) AS total_paid_ghs
WHERE 1 = 0

{% endif %}