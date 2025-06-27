WITH base AS (
  -- 1) paste your virtual‑dataset SQL here, exactly as it appears under “View query”
  SELECT
    product_id,
    service_type,
    app_id,
    app_service_id
    -- …all the joins/filters/etc.…
  FROM table1
  JOIN table2 ON …
  WHERE …
)
, combos AS (
  -- 2) narrow down to just what you need for counting
  SELECT product_id, service_type
  FROM base
)

-- 3) UNION the three buckets
SELECT
  'Service A only' AS category,
  COUNT(DISTINCT product_id) AS cnt
FROM combos
WHERE service_type = 'a'

UNION ALL

SELECT
  'Service B only' AS category,
  COUNT(DISTINCT product_id) AS cnt
FROM combos
WHERE service_type = 'b'

UNION ALL

SELECT
  'Both A & B' AS category,
  COUNT(*) AS cnt
FROM (
  SELECT product_id
  FROM combos
  WHERE service_type IN ('a','b')
  GROUP BY product_id
  HAVING COUNT(DISTINCT service_type) = 2
) t;
