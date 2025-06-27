WITH base AS (
    -- 1) Paste your virtual‑dataset SQL here,
    --    making sure it SELECTs your grouping column "tc":
    SELECT
        product_id,
        service_type,
        app_id,
        app_service_id  AS tc    -- ← replace with your actual tc column
    -- …joins/filters/etc…
    FROM table1
             JOIN table2 ON …
    WHERE …
),

     flags AS (
         -- 2) For each product, flag whether it has each service type
         SELECT
             product_id,
             tc,
             MAX(CASE WHEN service_type = 'Application Service' THEN 1 ELSE 0 END) AS has_application,
             MAX(CASE WHEN service_type = 'Technical Service'   THEN 1 ELSE 0 END) AS has_technical
         FROM base
         GROUP BY product_id, tc
     ),

     buckets AS (
         -- 3) Assign each (product,tc) to one category
         SELECT
             product_id,
             tc,
             CASE
                 WHEN has_application = 1 AND has_technical = 0 THEN 'Application Service only'
                 WHEN has_application = 0 AND has_technical = 1 THEN 'Technical Service only'
                 WHEN has_application = 1 AND has_technical = 1 THEN 'Both Application & Technical'
                 END AS category
         FROM flags
     )

-- 4) Count per tc + category
SELECT
    tc,
    category,
    COUNT(*) AS cnt
FROM buckets
GROUP BY tc, category
ORDER BY tc,
         CASE category
             WHEN 'Application Service only'     THEN 1
             WHEN 'Technical Service only'       THEN 2
             WHEN 'Both Application & Technical' THEN 3
             END;
