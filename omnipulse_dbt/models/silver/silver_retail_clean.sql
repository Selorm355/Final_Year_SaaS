-- models/silver/silver_retail_clean.sql

WITH raw_retail AS (
    -- 1. Read directly from the Bronze table mapped in sources.yml
    SELECT * FROM {{ source('raw_data', 'bronze_retail_data') }}
),

stripped_data AS (
    -- 2. Extract and strip all non-numeric junk characters first
    SELECT 
        company_id,
        "Date",
        "Receipt_ID",
        "Item_Name",
        -- Remove currency symbols, letters, spaces. Change comma to decimal.
        REGEXP_REPLACE(REPLACE(CAST("Unit_Cost" AS VARCHAR), ',', '.'), '[^0-9.-]', '', 'g') AS clean_cost,
        REGEXP_REPLACE(REPLACE(CAST("Unit_Price" AS VARCHAR), ',', '.'), '[^0-9.-]', '', 'g') AS clean_price,
        REGEXP_REPLACE(CAST("Quantity" AS VARCHAR), '[^0-9.-]', '', 'g') AS clean_qty
    FROM raw_retail
),

cleaned_retail AS (
    -- 3. Safely Cast Data Types and Calculate Profit
    SELECT
        company_id,
        
        -- THE BULLETPROOF DATE PARSER (V4 - Eager-Evaluation Immune)
        CASE 
            -- Catch completely null/empty
            WHEN "Date" IS NULL OR "Date" IN ('', 'NaN', 'INVALID_DATE') THEN NULL
            
            -- Catch logically impossible calendar dates
            WHEN "Date" IN ('2025-02-30', '0000-00-00', '2025/13/45') THEN NULL
            WHEN "Date" LIKE '%-02-30%' OR "Date" LIKE '%/02/30%' THEN NULL
            
            -- Format 1: YYYY-MM-DD
            WHEN "Date" ~ '^[0-9]{4}[-/.][0-9]{2}[-/.][0-9]{2}$' THEN 
                TO_DATE(
                    CASE WHEN "Date" ~ '^[0-9]{4}[-/.][0-9]{2}[-/.][0-9]{2}$' 
                         THEN REPLACE(REPLACE("Date", '.', '-'), '/', '-') 
                         ELSE '2000-01-01' END, 
                    'YYYY-MM-DD'
                )
            
            -- Format 2: MM-DD-YYYY (Day > 12)
            WHEN "Date" ~ '^[0-9]{2}[-/.](1[3-9]|2[0-9]|3[01])[-/.][0-9]{4}$' THEN 
                TO_DATE(
                    CASE WHEN "Date" ~ '^[0-9]{2}[-/.](1[3-9]|2[0-9]|3[01])[-/.][0-9]{4}$'
                         THEN REPLACE(REPLACE("Date", '.', '-'), '/', '-')
                         ELSE '01-01-2000' END,
                    'MM-DD-YYYY'
                )
                
            -- Format 3: DD-MM-YYYY (Day > 12)
            WHEN "Date" ~ '^(1[3-9]|2[0-9]|3[01])[-/.][0-9]{2}[-/.][0-9]{4}$' THEN 
                TO_DATE(
                    CASE WHEN "Date" ~ '^(1[3-9]|2[0-9]|3[01])[-/.][0-9]{2}[-/.][0-9]{4}$'
                         THEN REPLACE(REPLACE("Date", '.', '-'), '/', '-')
                         ELSE '01-01-2000' END,
                    'DD-MM-YYYY'
                )
                
            -- Format 4: Ambiguous DD-MM-YYYY
            WHEN "Date" ~ '^[0-9]{2}[-/.][0-9]{2}[-/.][0-9]{4}$' THEN 
                TO_DATE(
                    CASE WHEN "Date" ~ '^[0-9]{2}[-/.][0-9]{2}[-/.][0-9]{4}$'
                         THEN REPLACE(REPLACE("Date", '.', '-'), '/', '-')
                         ELSE '01-01-2000' END,
                    'DD-MM-YYYY'
                )
                
            -- Format 5: DD Mon YYYY (e.g. 11 May 2026)
            WHEN "Date" ~ '^[0-9]{2} [A-Za-z]{3} [0-9]{4}$' THEN
                TO_DATE(
                    CASE WHEN "Date" ~ '^[0-9]{2} [A-Za-z]{3} [0-9]{4}$' 
                         THEN "Date" 
                         ELSE '01 Jan 2000' END,
                    'DD Mon YYYY'
                )
                
            -- Format 6: Mon DD, YYYY (e.g. Aug 21, 2025)
            WHEN "Date" ~ '^[A-Za-z]{3} [0-9]{1,2}, [0-9]{4}$' THEN
                TO_DATE(
                    CASE WHEN "Date" ~ '^[A-Za-z]{3} [0-9]{1,2}, [0-9]{4}$' 
                         THEN REPLACE("Date", ',', '') 
                         ELSE 'Jan 01 2000' END,
                    'Mon DD YYYY'
                )
                
            ELSE NULL
        END AS transaction_date,
        
        CAST("Receipt_ID" AS VARCHAR) AS receipt_id,
        CAST("Item_Name" AS VARCHAR) AS item_name,
        
        -- Fixed Numeric parsing
        CAST(CAST(NULLIF(clean_qty, '') AS NUMERIC) AS INTEGER) AS quantity,
        CAST(NULLIF(clean_cost, '') AS DECIMAL(10, 2)) AS unit_cost_ghs,
        CAST(NULLIF(clean_price, '') AS DECIMAL(10, 2)) AS unit_price_ghs,
        
        -- Calculate Total Profit
        CAST(
            (CAST(NULLIF(clean_price, '') AS DECIMAL(10, 2)) - CAST(NULLIF(clean_cost, '') AS DECIMAL(10, 2))) 
            * CAST(CAST(NULLIF(clean_qty, '') AS NUMERIC) AS INTEGER) 
        AS DECIMAL(10, 2)) AS total_profit_ghs
        
    FROM stripped_data
    
    WHERE "Receipt_ID" IS NOT NULL 
      AND CAST(CAST(NULLIF(clean_qty, '') AS NUMERIC) AS INTEGER) > 0
)

-- 5. Deduplicate 
SELECT DISTINCT *
FROM cleaned_retail