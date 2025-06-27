WITH base AS (
    -- paste your virtual‑dataset SQL here, exactly as it appears under “View query”
    SELECT
        product_id,
        service_type,
        app_id,
        app_service_id
    -- …joins/filters/etc…
    FROM table1
             JOIN table2 ON …
    WHERE …
)
   , flags AS (
    -- collapse each product to two flags: has_application, has_technical
    SELECT
        product_id,
        MAX(CASE WHEN service_type = 'a' THEN 1 ELSE 0 END) AS has_application,
        MAX(CASE WHEN service_type = 'b' THEN 1 ELSE 0 END) AS has_technical
    FROM base
    GROUP BY product_id
)
SELECT
    CASE
        WHEN has_application = 1 AND has_technical = 0 THEN 'Application Service only'
        WHEN has_application = 0 AND has_technical = 1 THEN 'Technical Service only'
        WHEN has_application = 1 AND has_technical = 1 THEN 'Both Application & Technical'
        END AS category,
    COUNT(*) AS cnt
FROM flags
GROUP BY 1
ORDER BY
    CASE category
        WHEN 'Application Service only' THEN 1
        WHEN 'Technical Service only'     THEN 2
        WHEN 'Both Application & Technical' THEN 3
        END;
