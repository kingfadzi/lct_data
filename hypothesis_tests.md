# Hypothesis Tests Summary

---

## H1: LCP → Application Service (1 → *)

**Hypothesis:**  
Each **Lean Control Product** maps to one or more **Application Service** instances (1 → *).

**Objective:**  
Quantify how many Application Service instances each LCP is linked to.

**Data Sources & Join:**
- `public.lean_control_application` (p)
- `public.vnsfitserviceinstance` (si)
- Join on `p.servicenow_app_id = si.correlation_id`

**Experiment SQL:**
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

**Expected Outcome & Interpretation:**
- Most rows show `inst_count ≥ 1`.
- Any `inst_count = 0` indicates an LCP not deployed anywhere.
- Any `inst_count > 1` confirms 1 → * mapping.

---

## H2: LCP → Business Application (1 → *)

**Hypothesis:**  
Some **Lean Control Products** govern more than one **Business Application** (1 → *).

**Objective:**  
Identify LCPs linked to multiple Business Applications.

**Data Sources & Joins:**
- `public.lean_control_application` (p)
- `public.vnsfitserviceinstance` (si)
- `public.businessapplication` (ba)
- Joins:
    - `p.servicenow_app_id = si.correlation_id`
    - `si.business_application_sysid = ba.business_application_sys_id`

**Experiment SQL:**
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

**Expected Outcome & Interpretation:**
- Rows returned (`app_count > 1`) confirm multi-app governance.
- No rows means all LCPs link to at most one application.

---

## H3: Jira Project → LCP (1 → 1)

**Hypothesis:**  
Every **Jira Project** tracks exactly one **Lean Control Product** (1 → 1).

**Objective:**  
Verify no projects are unlinked or linked to multiple LCPs.

**Data Sources & Join:**
- `public.lean_control_product_backlog_details` (b)
- `public.lean_control_application` (p)
- Join on `b.lct_product_id = p.lean_control_service_id`

**Experiment SQL:**
```sql
-- Distribution of distinct LCPs per Jira Project
SELECT
b.jira_backlog_id,
COUNT(DISTINCT p.lean_control_service_id) AS distinct_lcp_count
FROM public.lean_control_product_backlog_details AS b
LEFT JOIN public.lean_control_application AS p
ON b.lct_product_id = p.lean_control_service_id
GROUP BY b.jira_backlog_id
ORDER BY distinct_lcp_count DESC;

-- Anomalies: projects with ≠ 1 LCP
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

**Expected Outcome & Interpretation:**
- All `distinct_lcp_count = 1` supports H3.
- Any `0` or `>1` flags orphaned or ambiguous projects.

---

## H4: Business Application → LCP (1 → *)

**Hypothesis:**  
Some **Business Applications** are governed by multiple **Lean Control Products** (1 → *).

**Objective:**  
Find applications with more than one LCP.

**Data Sources & Joins:**
- `public.businessapplication` (ba)
- `public.vwsfitserviceinstance` (si)
- `public.lean_control_application` (p)
- Joins:
    - `ba.business_application_id = si.business_application_sysid`
    - `si.correlation_id = p.servicenow_app_id`

**Experiment SQL:**
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

**Expected Outcome & Interpretation:**
- Rows with `prod_count > 1` confirm H4.
- No rows means every app has at most one LCP.  
