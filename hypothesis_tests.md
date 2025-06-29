# Hypothesis Tests Summary

---

## H1: Each Lean Control Product is linked to at least one service type—either one or more Application Service instances or one or more Technical Service instances—and if it’s only linked to Technical Services, it has no Application Service or Business Application mappings.

**Cardinality Table:**

| From Entity          | To Entity                    | Relationship Name | Cardinality | Notes                                                                | Example                        |
| -------------------- | ---------------------------- |-------------------| ----------- | -------------------------------------------------------------------- | ------------------------------ |
| Lean Control Product | Application Service Instance | governs           | 0 → *      | Products may have zero or many application mappings (tech‑only case) | LCP‑001 → ASI‑100, ASI‑101     |
| Lean Control Product | Technical Service Instance   | governs   | 0 → *      | Products may have zero or many technical mappings (app‑only case)    | LCP‑002 → TechSvc‑A, TechSvc‑B |

**Objective:**  
Confirm that every Lean Control Product has at least one associated service instance (application or technical), and that any product with only technical mappings has zero application or business‑application links.

**Experiment SQL:**
```sql
SELECT
  p.lean_control_service_id,
  COUNT(DISTINCT si.it_service_instance) AS instance_count,
  STRING_AGG(DISTINCT si.it_service_instance, ', ') AS service_instances
FROM public.lean_control_application AS p
LEFT JOIN public.vwsfitserviceinstance AS si
  ON p.servicenow_app_id = si.correlation_id
GROUP BY p.lean_control_service_id
ORDER BY inst_count DESC;
```
```sql
WITH instance_counts AS (
  SELECT
    p.lean_control_service_id,
    COUNT(DISTINCT si.it_service_instance) AS instance_count
  FROM public.lean_control_application AS p
  LEFT JOIN public.vwsfitserviceinstance AS si
    ON p.servicenow_app_id = si.correlation_id
  GROUP BY p.lean_control_service_id
)
SELECT
  CASE
    WHEN instance_count = 0 THEN '0'
    WHEN instance_count = 1 THEN '1'
    ELSE '>1'
  END AS instance_category,
  COUNT(*) AS product_count
FROM instance_counts
GROUP BY instance_category
ORDER BY instance_category;

```
```sql
SELECT
  p.lean_control_service_id
FROM public.lean_control_application AS p
LEFT JOIN public.vwsfitserviceinstance AS si
  ON p.servicenow_app_id = si.correlation_id
WHERE si.it_service_instance IS NULL;

```
```sql
SELECT
  service_type,
  COUNT(DISTINCT lean_control_service_id)   AS lcp_count,
  COUNT(DISTINCT ITBA)                      AS itba_count,
  COUNT(DISTINCT service_instance)          AS instance_count
FROM (
  SELECT
    lean_app.lean_control_service_id,
    CASE
      WHEN business_service.category = 'Technical Service' THEN 'Technical Service'
      WHEN business_service.category IS NULL OR business_service.category = '' THEN 'Application Service'
      ELSE business_service.category
    END AS service_type,
    business_app.correlation_id               AS ITBA,
    service_instance.it_service_instance     AS service_instance
  FROM public.lean_control_application     AS lean_app
  LEFT JOIN public.vwsfitserviceinstance   AS service_instance
    ON lean_app.servicenow_app_id = service_instance.correlation_id
  LEFT JOIN public.vwsfitbusinessservice   AS business_service
    ON lean_app.servicenow_app_id = business_service.service_correlation_id
  LEFT JOIN public.vwsfbusinessapplication AS business_app
    ON service_instance.business_application_sysid = business_app.business_application_sys_id
) AS sub
GROUP BY service_type
ORDER BY instance_count DESC;
```

**Observations:**  
* 55% of Lean Control Products map to Application Services; 45% are Technical Service.
* Technical Service only Lean Control Products have no Application Service or Business Application links.

**Implications:**  
* Lean Control Products mapped to Technical Service‑only have no visibility into the actual applications or environments they govern.

---

## H2: Some Lean Control Products govern multiple Business Applications.

**Cardinality Table:**

| From Entity           | To Entity            | Relationship Name | Cardinality | Notes                                                        | Example Records                          |
|-----------------------|----------------------|-------------------|-------------|--------------------------------------------------------------|------------------------------------------|
| Lean Control Product  | Business Application | governs           | 1 → *       | A product may cover risk controls across multiple business apps. | LCSERV-202 → ITBA-005, ITBA-007          |

**Objective:**  
Identify control products that span multiple business applications.

**Experiment SQL:**
```sql
SELECT
  p.lean_control_service_id,
  COUNT(DISTINCT ba.correlation_id) AS app_count,
  STRING_AGG(DISTINCT ba.correlation_id::text, ', ') AS applications
FROM public.lean_control_application AS p
LEFT JOIN public.vwsfitserviceinstance AS si
  ON p.servicenow_app_id = si.correlation_id
LEFT JOIN public.vwsfbusinessapplication AS ba
  ON si.business_application_sysid = ba.business_application_sys_id
GROUP BY p.lean_control_service_id
HAVING COUNT(DISTINCT ba.correlation_id) > 1
ORDER BY app_count DESC;
```
```sql
WITH app_counts AS (
  SELECT
    p.lean_control_service_id,
    COUNT(DISTINCT ba.correlation_id) AS app_count
  FROM public.lean_control_application AS p
  LEFT JOIN public.vwsfitserviceinstance AS si
    ON p.servicenow_app_id = si.correlation_id
  LEFT JOIN public.vwsfbusinessapplication AS ba
    ON si.business_application_sysid = ba.business_application_sys_id
  GROUP BY p.lean_control_service_id
)
SELECT
  CASE
    WHEN app_count = 0 THEN '0 apps'
    WHEN app_count = 1 THEN '1 app'
    ELSE '> 1 apps'
  END AS app_mapping_category,
  COUNT(*) AS lcp_count
FROM app_counts
GROUP BY app_mapping_category
ORDER BY app_mapping_category;

```


**Observations:**  
*Placeholder for observations from the experiment.*

**Implications:**  
*Placeholder for implications based on observations.*

---

## H3: Every Jira Project tracks exactly one Lean Control Product.

**Cardinality Table:**

| From Entity   | To Entity            | Relationship Name | Cardinality | Notes                                                   | Example Records        |
|---------------|----------------------|-------------------|-------------|---------------------------------------------------------|------------------------|
| Jira Project  | Lean Control Product | tracks            | 1 → 1       | Each backlog of risk stories corresponds to one product. | JB-2100 → LCSERV-101   |

**Objective:**  
Ensure each Jira backlog maps to a single control product.

**Experiment SQL (distribution):**
```sql
SELECT
  b.jira_backlog_id,
  COUNT(DISTINCT p.lean_control_service_id) AS distinct_lcp_count
FROM public.lean_control_product_backlog_details AS b
LEFT JOIN public.lean_control_application AS p
  ON b.lct_product_id = p.lean_control_service_id
GROUP BY b.jira_backlog_id
ORDER BY distinct_lcp_count DESC;
```

**Experiment SQL (anomalies):**
```sql
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

**Observations:**  
*Placeholder for observations from the experiment.*

**Implications:**  
*Placeholder for implications based on observations.*

---

## H4: Some Business Applications are governed by multiple Lean Control Products.

**Cardinality Table:**

| From Entity          | To Entity             | Relationship Name | Cardinality | Notes                                               | Example Records                          |
|----------------------|-----------------------|-------------------|-------------|-----------------------------------------------------|------------------------------------------|
| Business Application | Lean Control Product  | governed_by       | 1 → *       | An application may require multiple control products for different risk areas. | ITBA-009 → LCSERV-310, LCSERV-311, LCSERV-312 |

**Objective:**  
Find business applications with more than one associated control product.

**Experiment SQL:**
```sql
SELECT
  ba.business_application_id AS itba,
  COUNT(p.lean_control_service_id) AS prod_count,
  STRING_AGG(p.lean_control_service_id, ', ') AS lcp_ids
FROM public.businessapplication AS ba
LEFT JOIN public.vnsfitserviceinstance AS si
  ON ba.business_application_id = si.business_application_sysid
LEFT JOIN public.lean_control_application AS p
  ON si.correlation_id = p.servicenow_app_id
GROUP BY ba.business_application_id
HAVING COUNT(p.lean_control_service_id) > 1
ORDER BY prod_count DESC;
```

**Observations:**  
*Placeholder for observations from the experiment.*

**Implications:**  
*Placeholder for implications based on observations.*

---

## H5: Most Lean Control Products are actively linked to applications and environments.

**Cardinality Table:**

| From Entity          | To Entity             | Relationship Name | Cardinality | Notes                                                       | Example Records                   |
|----------------------|-----------------------|-------------------|-------------|-------------------------------------------------------------|-----------------------------------|
| Lean Control Product | Business Application  | governs           | * → *       | Products generally must map to at least one application.    | LCSERV-101→ITBA-001, LCSERV-102→ITBA-001 |
| Lean Control Product | Application Service   | applies_to        | * → *       | Products generally must apply to at least one environment.  | LCSERV-101→Dev-Instance, LCSERV-101→Prod-Instance |

**Objective:**  
Show how control products link across both apps and environments.

**Experiment SQL:**
```sql
SELECT
  inst_count,
  app_count,
  COUNT(*) AS lcp_count
FROM (
  SELECT
    p.lean_control_service_id,
    COUNT(DISTINCT si.it_service_instance) AS inst_count,
    COUNT(DISTINCT ba.correlation_id)      AS app_count
  FROM public.lean_control_application AS p
  LEFT JOIN public.vnsfitserviceinstance AS si
    ON p.servicenow_app_id = si.correlation_id
  LEFT JOIN public.businessapplication AS ba
    ON si.business_application_sysid = ba.business_application_sys_id
  GROUP BY p.lean_control_service_id
) AS sub
GROUP BY inst_count, app_count
ORDER BY inst_count, app_count;
```

**Observations:**  
*Placeholder for observations from the experiment.*

**Implications:**  
*Placeholder for implications based on observations.*

## H6: Some Lean Control Products are only linked to Technical Services and are not associated with any Business Applications or Application Services.

**Cardinality Table:**

| From Entity           | To Entity          | Relationship Name | Cardinality | Notes                                                                 | Example Records              |
|-----------------------|--------------------|-------------------|-------------|-----------------------------------------------------------------------|------------------------------|
| Lean Control Product  | Technical Service  | applies_to        | 1 → *       | These control products govern technical infrastructure, without mapping to business or app services. | LCSERV-999 → TS-010, TS-020 |

**Objective:**  
Determine whether certain Lean Control Products are strictly scoped to Technical Services, i.e., they have no associated Business Applications or Application Services.

**Experiment SQL:**
```sql
SELECT
    lean_app.lean_control_service_id,
    COUNT(DISTINCT business_service.service) AS tech_service_count,
    COUNT(DISTINCT service_instance.it_service_instance) AS app_service_count,
    COUNT(DISTINCT business_app.correlation_id) AS biz_app_count,
    STRING_AGG(DISTINCT business_service.service, ', ') AS tech_services
FROM public.lean_control_application lean_app
         LEFT JOIN public.vwsfitserviceinstance service_instance
                   ON lean_app.servicenow_app_id = service_instance.correlation_id
         LEFT JOIN public.vwsfbusinessapplication business_app                   
                   ON service_instance.business_application_sysid = business_app.business_application_sys_id
         LEFT JOIN public.vwsfitbusinessservice business_service
                   ON lean_app.servicenow_app_id = business_service.service_correlation_id
WHERE business_service.category = 'Technical Service'
GROUP BY lean_app.lean_control_service_id
HAVING
    COUNT(DISTINCT business_app.correlation_id) = 0 AND
    COUNT(DISTINCT service_instance.it_service_instance) = 0
ORDER BY tech_service_count DESC;
```

**Observations:**  
*Placeholder for observations from the experiment.*

**Implications:**  
*Placeholder for implications based on observations.*

## H7: Lean Control Products linked to Application Services are generally also associated with Business Applications.

**Cardinality Table:**

| From Entity           | To Entity            | Relationship Name | Cardinality | Notes                                                                            | Example Records                         |
|-----------------------|----------------------|-------------------|-------------|----------------------------------------------------------------------------------|------------------------------------------|
| Lean Control Product  | Application Service  | applies_to        | * → *       | LCPs may govern multiple environments.                                           | LCSERV-120 → Dev-Instance, QA-Instance   |
| Application Service   | Business Application | belongs_to        | * → 1       | Application Services typically map to one Business Application.                 | QA-Instance → ITBA-103                   |

**Objective:**  
Evaluate whether Lean Control Products that are applied to Application Services are indirectly also connected to Business Applications — via the service instance relationship.

**Experiment SQL:**
```sql
SELECT
    lean_app.lean_control_service_id,
    COUNT(DISTINCT service_instance.it_service_instance) AS app_service_count,
    COUNT(DISTINCT business_app.correlation_id) AS biz_app_count,
    STRING_AGG(DISTINCT business_app.correlation_id, ', ') AS business_apps
FROM public.lean_control_application lean_app
         LEFT JOIN public.vwsfitserviceinstance service_instance
                   ON lean_app.servicenow_app_id = service_instance.correlation_id
         LEFT JOIN public.vwsfbusinessapplication business_app
                   ON service_instance.business_application_sysid = business_app.business_application_sys_id
WHERE service_instance.it_service_instance IS NOT NULL
GROUP BY lean_app.lean_control_service_id
HAVING COUNT(DISTINCT service_instance.it_service_instance) > 0
ORDER BY biz_app_count DESC;
```
**Observations:**  
*Placeholder for observations from the experiment.*

**Implications:**  
*Placeholder for implications based on observations.*
