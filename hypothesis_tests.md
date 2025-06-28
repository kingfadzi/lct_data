Here’s a cleaner view: a compact summary table, followed by each full SQL experiment below it. This keeps the table readable while still giving you all the detail.

| Hypothesis                                                                                                                                            | Expected Outcome                                                                       | Interpretation                                                                                              |
| ----------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| **H1:** A Lean Control Product always maps to exactly one Application Service instance.                                                               | Every product has `inst_count = 1`.                                                    | All = 1 supports H1; any 0 or > 1 flags anomalies.                                                          |
| **H2:** No single Lean Control Product can govern more than one Business Application.                                                                 | Every product has `app_count = 1`.                                                     | All = 1 supports H2; any 0 or > 1 flags violations.                                                         |
| **H3:** Every Jira Project tracks risk stories for exactly one Lean Control Product.                                                                  | Every backlog has `prod_count = 1`.                                                    | All = 1 supports H3; any 0 or > 1 flags orphans or overlaps.                                                |
| **H4:** Some Business Applications are governed by multiple Lean Control Products.                                                                    | Some apps show `prod_count > 1`.                                                       | > 1 confirms H4; zero or one are also informative (apps missing products or single-product apps).           |
| **H5:** No Lean Control Product applies controls to more than one Application Service instance.                                                       | No products returned by the “> 1 instances” query.                                     | Zero rows supports H5; any rows flag products tied to multiple instances.                                   |
| **H6:** For any Business Application deployed into *N* environments, there are *N* Lean Control Products—and each is tracked in its own Jira Project. | No apps returned by the “mismatch” query (instance\_count = lcp\_count = jira\_count). | Zero rows supports H6; any rows reveal counting mismatches across deployments, products, and Jira tracking. |

---

### Full SQL Experiments

#### H1: One LCP → One App Service

```sql
SELECT
  p.lean_control_service_id,
  COUNT(DISTINCT si.it_service_instance) AS inst_count
FROM public.lean_control_application AS p
LEFT JOIN public.vwsfitserviceinstance AS si
  ON p.servicenow_app_id = si.correlation_id
GROUP BY p.lean_control_service_id
ORDER BY inst_count DESC;
```

#### H2: LCP → One Business Application

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

#### H3: Jira → One LCP

```sql
SELECT
  b.jira_backlog_id,
  COUNT(p.lean_control_service_id) AS prod_count
FROM public.lean_control_product_backlog_details AS b
LEFT JOIN public.lean_control_application AS p
  ON b.lct_product_id = p.lean_control_service_id
GROUP BY b.jira_backlog_id
ORDER BY prod_count DESC;
```

#### H4: App → Multiple LCPs

```sql
SELECT
  ba.business_application_id AS itba,
  COUNT(p.lean_control_service_id) AS prod_count
FROM public.businessapplication AS ba
LEFT JOIN public.vnsfitserviceinstance AS si
  ON ba.business_application_sys_id = si.business_application_sysid
LEFT JOIN public.lean_contzol_application AS p
  ON si.correlation_id = p.servicenow_app_id
GROUP BY ba.business_application_id
ORDER BY prod_count DESC;
```

#### H5: LCP → ≤1 App Service

```sql
SELECT
  p.lean_control_service_id,
  COUNT(DISTINCT si.it_service_instance) AS inst_count
FROM public.lean_control_application AS p
JOIN public.vwsfitserviceinstance AS si
  ON p.servicenow_app_id = si.correlation_id
GROUP BY p.lean_control_service_id
HAVING COUNT(DISTINCT si.it_service_instance) > 1;
```

#### H6: N Environments → N LCPs & N Jira

```sql
SELECT
  ba.business_application_id AS itba,
  COUNT(DISTINCT si.it_service_instance) AS instance_count,
  COUNT(DISTINCT p.lean_control_service_id)      AS lcp_count,
  COUNT(DISTINCT b.jira_backlog_id)               AS jira_count
FROM public.businessapplication AS ba
LEFT JOIN public.vwsfitserviceinstance AS si
  ON ba.business_application_id = si.business_application_sysid
LEFT JOIN public.lean_control_application AS p
  ON si.correlation_id = p.servicenow_app_id
LEFT JOIN public.lean_control_product_backlog_details AS b
  ON p.lean_control_service_id = b.lct_product_id
GROUP BY ba.business_application_id
HAVING
  COUNT(DISTINCT si.it_service_instance) <> COUNT(DISTINCT p.lean_control_service_id)
  OR COUNT(DISTINCT p.lean_control_service_id) <> COUNT(DISTINCT b.jira_backlog_id);
```

```sql
SELECT
  inst_count,
  app_count,
  COUNT(*) AS lcp_count
FROM (
  SELECT
    p.lean_control_service_id,
    COUNT(DISTINCT si.it_service_instance)    AS inst_count,
    COUNT(DISTINCT ba.correlation_id)          AS app_count
  FROM public.lean_control_application AS p
  LEFT JOIN public.vwsfitserviceinstance AS si
    ON p.servicenow_app_id = si.correlation_id
  LEFT JOIN public.businessapplication AS ba
    ON si.business_application_sysid = ba.business_application_sys_id
  GROUP BY p.lean_control_service_id
) AS sub
GROUP BY inst_count, app_count
ORDER BY inst_count, app_count;

```