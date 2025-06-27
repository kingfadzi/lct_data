-- 1) Replace the entire contents of the base CTE with your virtual‑dataset SQL (including all joins/filters).
WITH base AS (
    /* PASTE YOUR VIRTUAL DATASET’S SQL HERE, for example:
    SELECT
      p.product_id,
      p.service_type,
      p.app_id,
      s.app_service_id
    FROM products p
    JOIN app_services s
      ON p.app_id = s.app_id
    WHERE …your filters…
    */
    /* ↓ your SQL goes here ↓ */
),

-- 2) Collapse each product into two flags: has_application, has_technical
     flags AS (
         SELECT
             product_id,
             MAX(CASE WHEN service_type = 'Application Service' THEN 1 ELSE 0 END) AS has_application,
             MAX(CASE WHEN service_type = 'Technical Service'   THEN 1 ELSE 0 END) AS has_technical
         FROM base
         GROUP BY product_id
     ),

-- 3) Bucket products into exactly three categories
     buckets AS (
         SELECT
             CASE
                 WHEN has_application = 1 AND has_technical = 0 THEN 'Application Service only'
                 WHEN has_application = 0 AND has_technical = 1 THEN 'Technical Service only'
                 WHEN has_application = 1 AND has_technical = 1 THEN 'Both Application & Technical'
                 END AS category
         FROM flags
     )

-- 4) Count how many products fall into each category
SELECT
    category,
    COUNT(*) AS cnt
FROM buckets
GROUP BY category
ORDER BY
    CASE category
        WHEN 'Application Service only'     THEN 1
        WHEN 'Technical Service only'       THEN 2
        WHEN 'Both Application & Technical' THEN 3
        END;
