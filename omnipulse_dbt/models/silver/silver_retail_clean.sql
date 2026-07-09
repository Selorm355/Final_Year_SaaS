-- models/silver/silver_retail_clean.sql

WITH raw_retail AS (
    -- 1. Read directly from the Bronze table mapped in sources.yml
    SELECT * FROM {{ source('raw_data', 'bronze_retail_data') }}
),

cleaned_retail AS (
    -- 2. Clean, Cast Data Types, and Calculate Profit
    SELECT
        company_id,
        
        -- THE SMART PARSER: Handles both Excel's dashed format and raw slashed format
        CASE 
            WHEN "Date" LIKE '%/%' THEN TO_DATE("Date", 'DD/MM/YYYY')
            ELSE CAST("Date" AS DATE)
        END AS transaction_date,
        
        CAST("Receipt_ID" AS VARCHAR) AS receipt_id,
        CAST("Item_Name" AS VARCHAR) AS item_name,
        CAST("Quantity" AS INTEGER) AS quantity,
        
        -- Rename to GHS and enforce decimal places
        CAST("Unit_Cost" AS DECIMAL(10, 2)) AS unit_cost_ghs,
        CAST("Unit_Price" AS DECIMAL(10, 2)) AS unit_price_ghs,
        
        -- Calculate Total Profit per line item ( (Price - Cost) * Quantity )
        CAST((("Unit_Price" - "Unit_Cost") * "Quantity") AS DECIMAL(10, 2)) AS total_profit_ghs
        
    FROM raw_retail
    -- 3. Filter out junk rows
    WHERE "Receipt_ID" IS NOT NULL 
      AND "Quantity" > 0
)

-- 4. Deduplicate 
SELECT DISTINCT *
FROM cleaned_retail