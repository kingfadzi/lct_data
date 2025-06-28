# Hypothesis Tests Summary

## H1: LCP → Application Service (1 → *)
**Hypothesis:** Each **Lean Control Product** maps to one or more **Application Service** instances.  
**Objective:** Identify LCPs linked to multiple instances.  
**Data Sources:**
- `public.lean_control_application` (p)
- `public.vnsfitserviceinstance` (si)
- Join: `p.servicenow_app_id = si.correlation_id`  
  **Expected Outcome:** ≥ 1 LCPs with `inst_count > 1`.  
  **Interpretation:** Any `inst_count > 1` confirms the 1 → * relationship.

```sql
SELECT
  p.lean_control_service_id,
  COUNT(DISTINCT si.it_service_instance) AS inst_count,
  STRING_AGG(DISTINCT si.it_service_instance, ', ') AS instances
FROM public.lean_control_application AS p
LEFT JOIN public.vnsfitserviceinstance AS si
  ON p.servicenow_app_id = si.correlation_id
GROUP BY p.lean_control_service_id
ORDER BY inst_count DESC;
```

## H2: LCP → Business Application (1 → *)
**Hypothesis:** Some **Lean Control Products** govern more than one **Business Application**.  
**Objective:** Surface LCPs with multiple apps.  
**Data Sources:**
- `public.lean_control_application` (p)
- `public.vnsfitserviceinstance` (si)
- `public.businessapplication` (ba)
- Joins:
    - `p.servicenow_app_id = si.correlation_id`
    - `si.business_application_sysid = ba.business_application_sys_id`  
      **Expected Outcome:** ≥ 1 LCPs with `app_count > 1`.  
      **Interpretation:** Rows here confirm true multi-app governance.

```sql
SELECT
  p.lean_control_service_id,
  COUNT(DISTINCT ba.correlation_id) AS app_count,
  STRING_AGG(DISTINCT ba.correlation_id::text, ', ') AS applications
FROM public.lean_control_application AS p
LEFT JOIN public.vwsfitserviceinstance AS si
  ON p.servicenow_app_id = si.correlation_id
LEFT JOIN public.businessapplication AS ba
  ON si.business_application_sysid = ba.business_application_sys_id
GROUP BY p.lean_control_service_id
HAVING COUNT(DISTINCT ba.correlation_id) > 1
ORDER BY app_count DESC;
```

## H3: Jira Project → LCP (1 → 1)
**Hypothesis:** Every **Jira Project** tracks exactly one **Lean Control Product**.  
**Objective:** Verify no backlogs are unlinked or linked to multiple LCPs.  
**Data Sources:**
- `public.lean_control_product_backlog_details` (b)
- `public.lean_control_application` (p)
- Join: `b.lct_product_id = p.lean_control_service_id`  
  **Expected Outcome:** All `distinct_lcp_count = 1`.  
  **Interpretation:** Deviations (`0` or `>1`) flag orphaned or ambiguous backlogs.

```sql
-- Distribution
SELECT
  b.jira_backlog_id,
  COUNT(DISTINCT p.lean_control_service_id) AS distinct_lcp_count
FROM public.lean_control_product_backlog_details AS b
LEFT JOIN public.lean_control_application AS p
  ON b.lct_product_id = p.lean_control_service_id
GROUP BY b.jira_backlog_id
ORDER BY distinct_lcp_count DESC;

-- Anomalies
SELECT
  b.jira_backlog_id,
  COUNT(DISTINCT p.lean_control_service_id) AS distinct_lcp_count,
  STRING_AGG(DISTINCT p.lean_control_service_id, ', ') AS lcp_ids
FROM public.lean_control_product_backlog_details AS b
LEFT JOIN public.lean_control_application AS p
  ON b.lct_product_id = p.lean_control_service_id
GROUP BY b.jira_backlog_id
HAVING COUNT(DISTINCT p.lean_control_service_id) <> 1
ORDER BY distinct_lcp_count DESC;
```

## H4: Business Application → LCP (1 → *)
**Hypothesis:** Some **Business Applications** are governed by multiple **Lean Control Products**.  
**Objective:** Find apps with more than one LCP.  
**Data Sources:**
- `public.businessapplication` (ba)
- `public.vnsfitserviceinstance` (si)
- `public.lean_control_application` (p)
- Joins:
    - `ba.business_application_id = si.business_application_sysid`
    - `si.correlation_id = p.servicenow_app_id`  
      **Expected Outcome:** ≥ 1 apps with `prod_count > 1`.  
      **Interpretation:** Those apps are under multi-product governance.

```sql
SELECT
  ba.business_application_id AS itba,
  COUNT(p.lean_control_service_id) AS prod_count,
  STRING_AGG(p.lean_control_service_id, ', ') AS lcp_ids
FROM public.businessapplication AS ba
LEFT JOIN public.vwsfitserviceinstance AS si
  ON ba.business_application_id = si.business_application_sysid
LEFT JOIN public.lean_control_application AS p
  ON si.correlation_id = p.servicenow_app_id
GROUP BY ba.business_application_id
HAVING COUNT(p.lean_control_service_id) > 1
ORDER BY prod_count DESC;
```
