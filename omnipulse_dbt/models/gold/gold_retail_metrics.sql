-- models/gold/gold_retail_metrics.sql

WITH clean_retail AS (
    -- Read from our Silver model instead of the raw source!
    SELECT * FROM {{ ref('silver_retail_clean') }}
)

SELECT
    company_id,
    transaction_date,
    
    -- Traffic Metrics
    COUNT(DISTINCT receipt_id) AS total_transactions,
    SUM(quantity) AS total_items_sold,
    
    -- Financial Metrics
    SUM(quantity * unit_cost) AS total_cogs, -- Cost of Goods Sold
    SUM(quantity * unit_price) AS gross_revenue,
    
    -- The Money Maker: Profit
    SUM(quantity * unit_price) - SUM(quantity * unit_cost) AS gross_profit,
    
    -- Average Order Value (Revenue / Number of Transactions)
    CASE 
        WHEN COUNT(DISTINCT receipt_id) = 0 THEN 0 
        ELSE SUM(quantity * unit_price) / COUNT(DISTINCT receipt_id) 
    END AS average_order_value

FROM clean_retail
GROUP BY 
    company_id, 
    transaction_date