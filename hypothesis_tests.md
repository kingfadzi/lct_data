# Hypothesis Tests Summary

---

## H1: Each Lean Control Product is linked to at least one service type—either one or more Application Service instances or one or more Technical Service instances—and if it’s only linked to Technical Services, it has no Application Service or Business Application mappings.
* All Lean Control Products map to either Application Services or are linked to Technical Services.
* 55% of Lean Control Products are mapped Application Services; 45% (≈ 644 Lean Control Products) are linked to Technical Services.
* Lean Control Products linked to Technical Services do not have links the Business Applications they control therefore lack visibility into the applications and business contexts they cover.

### Design Questions:
* HMW map Lean Control Products linked to Technical Services to their missing Application and Application Service contexts despite incomplete data in the system?
* HMW support accurate mapping of Lean Control Products to applications composed of multiple ITBAs and deployment environments, each with its own Application Service instance?
* HMW automate the validation and mapping of Lean Control Products to Application and Application Service records where data is already available, to ensure baseline integrity?

---

## H2: Lean Control Products vary in how many Business Applications they govern: some govern none, some exactly one, and some span multiple applications.
* 399 Lean Control Products control 0 Business Applications; 449 control exactly 1; 317 control more than 1.
* Lean Control Products mapped to 0 apps mean: No visibility onto any specific application or mean data integrity issues.
* Mapping 1 Lean Control Product to 1 Business Application is Clear and easy to manage, but will break down for multi‑component or multi‑regional apps (front end, back end, API, APAC/EU, etc.).
* Mapping 1 Lean Control Product to more than 1 app: Fits complex or regionalized applications, but keeping traceability requires extending the data model to record both the Business Application ID and the Application Service when applying controls.

### Design Questions:
* HMW evolve the data model so that 1 Lean Control Product can control multiple Business Applications and their corresponding Application Services without losing the ability to audit control coverage?

---

## H3: Every Jira Project should track exactly one Lean Control Product
* A strict one-to-one mapping between Jira backlogs and Lean Control Products ensures consistent governance.
* Of all projects, 1,221 correctly track one Lean Control Product; 122 have no Lean Control Product link; 3 track multiple Lean Control Products.
* The 125 anomalous projects break the governance model and risk untracked work or duplicated scopes.

### Design Questions:
* HMW detect and automatically correct anomalies in the Jira Project–Lean Control Product mapping to maintain data integrity?
---

## H4: Each Business Application is controlled by exactly one Lean Control Product
* Predominant 1:1 mapping: Roughly 89% (1,713) of applications follow the simple, one-to-one Lean Control Product to Application mapping model, making their control lifecycles straightforward to manage.
* The other 11% (203) mappings appear anomalous and warrant investigation.
* We also need to understand how the mapping of 1 Lean Control Product to one itba applies to larger applications made up of multiple components each with its own ITBA.

### Design Questions:
* HMW represent and control large applications composed of multiple ITBAs using a single Lean Control Product, while preserving clarity and control over each component?
---

## H5: Most Lean Control Products are actively linked to applications and environments.
* Most Lean Control Products cluster at low app and instance counts (median = 1).
* A few outliers exist (e.g. one LCP with 46 apps and 108 instances).
* The long tail of rare (inst_count, app_count) configurations indicates high variability.
* LCPs with 0 apps and 0 instances likely reflect misconfigurations—referential integrity should be checked.
* High-count outliers pose governance and audit risks; for composite or multi-regional applications, the data model may need additional metadata (e.g. component identifiers or region tags) to maintain clear traceability.

### Design Questions:
* HMW evolve the data model to support both simple 1:1 mappings and complex, multi-region or multi-component environments while preserving traceability and control clarity?
* HMW retrofit Lean Control Product outliers (e.g. LCP with 46 apps and 108 instances) by decomposing and remapping them into simpler, well-scoped units—without disrupting existing user workflows or visibility?
* HMW automate the detection of Lean Control Products with zero mappings to ensure data integrity and governance?
---

## H1: Each Lean Control Product is linked to at least one service type—either one or more Application Service instances or one or more Technical Service instances—and if it’s only linked to Technical Services, it has no Application Service or Business Application mappings.

**Cardinality Table:**

| From Entity          | To Entity                    | Relationship Name | Cardinality | Notes                                                                | Example                        |
| -------------------- | ---------------------------- |-------------------| ----------- | -------------------------------------------------------------------- | ------------------------------ |
| Lean Control Product | Application Service Instance | governs           | 0 → *      | Products may have zero or many application mappings (tech‑only case) | LCP‑001 → ASI‑100, ASI‑101     |
| Lean Control Product | Technical Service Instance   | governs   | 0 → *      | Products may have zero or many technical mappings (app‑only case)    | LCP‑002 → TechSvc‑A, TechSvc‑B |

**Objective:**  
Confirm that every Lean Control Product has at least one associated service instance (application or technical), and that any product with only technical mappings has zero application or business‑application links.

**Observations:**  
* 55% of Lean Control Products map to Application Services; 45% are Technical Service.
* Lean Control Products mapped Technical Service have no Application Service or Business Application links.

**Implications:**  
* Lean Control Products mapped to Technical Service have no visibility into the actual applications or environments they govern.

---

## H2: Lean Control Products vary in how many Business Applications they govern: some govern none, some exactly one, and some span multiple applications.

**Cardinality Table:**

| From Entity           | To Entity            | Relationship Name | Cardinality | Notes                                                        | Example Records                          |
|-----------------------|----------------------|-------------------|-------------|--------------------------------------------------------------|------------------------------------------|
| Lean Control Product  | Business Application | governs           | 1 → *       | A product may cover risk controls across multiple business apps. | LCSERV-202 → ITBA-005, ITBA-007          |

**Objective:**  
Measure and report the number of Lean Control Products in each category—0 apps, 1 app, and >1 apps—to reveal visibility gaps and complexity implications.

**Observations:**  
* 399 Lean Control Products have no Business Application mappings.
* 449 map to exactly one Business Application.
* 317 map to more than one Business Application.


**Implications:**  
* 0 apps: No visibility onto any specific application.
* 1 app: Clear and easy to manage, but will break down for multi‑component or multi‑regional apps (front end, back end, API, APAC/EU, etc.).
* 1+ apps: Fits complex or regionalized applications, but keeping traceability requires extending the data model to record both the Business Application ID and the Application Service when applying controls.

---

## H3: Every Jira Project tracks exactly one Lean Control Product.

**Cardinality Table:**

| From Entity   | To Entity            | Relationship Name | Cardinality | Notes                                                   | Example Records        |
|---------------|----------------------|-------------------|-------------|---------------------------------------------------------|------------------------|
| Jira Project  | Lean Control Product | tracks            | 1 → 1       | Each backlog of risk stories corresponds to one product. | JB-2100 → LCSERV-101   |

**Objective:**  
Ensure each Jira backlog maps to a single control product.


**Observations:**  
* 122 Jira projects have no linked Lean Control Product.
* 1,221 projects map to exactly 1 Lean Control Product.
* 3 projects map to more than 1 Lean Control Product.

**Implications:**  
* Projects with 0 or >1 LCPs deviate from the expected 1:1 mapping and must be investigated to understand why they exist.
* Overall consistency is high, but these anomalies highlight areas for data‑quality review.
---

## H4: Each Business Application is governed by exactly one Lean Control Product.

**Cardinality Table:**

| From Entity          | To Entity             | Relationship Name | Cardinality | Notes                                               | Example Records                          |
|----------------------|-----------------------|-------------------|-------------|-----------------------------------------------------|------------------------------------------|
| Business Application | Lean Control Product  | governed_by       | 1 → 1       | Each application maps to exactly one control product. |  |

**Objective:**  
* How many applications have a single Lean Control Product mapping
* How many have multiple Lean Control Product mappings



**Observations:**  
* 1 LCP: 1,713 Business Applications are governed by exactly one Lean Control Product.
* 1+ LCPs: 203 Business Applications are governed by multiple Lean Control Products.


**Implications:**  
* Predominant 1:1 mapping: Roughly 89% of applications follow the simple, one-to-one Lean Control Product to Application mapping model, making their control lifecycles straightforward to manage.
* These 203 mappings appear anomalous and warrant investigation.
* We also need to understand how the mapping of 1 Lean Control Product to one itba applies to larger applications made up of multiple components each with its own ITBA.
---

## H5: Most Lean Control Products are actively linked to applications and environments.

**Cardinality Table:**

| From Entity          | To Entity             | Relationship Name | Cardinality | Notes                                                       | Example Records                   |
|----------------------|-----------------------|-------------------|-------------|-------------------------------------------------------------|-----------------------------------|
| Lean Control Product | Business Application  | governs           | * → *       | Products generally must map to at least one application.    | LCSERV-101→ITBA-001, LCSERV-102→ITBA-001 |
| Lean Control Product | Application Service   | applies_to        | * → *       | Products generally must apply to at least one environment.  | LCSERV-101→Dev-Instance, LCSERV-101→Prod-Instance |

**Objective:**  
Show how control products link across both apps and environments.

**Observations:**  
* Most LCPs cluster at low app and instance counts (median = 1).
* A few outliers exist (e.g. one LCP with 46 apps and 108 instances).
* The long tail of rare (inst_count, app_count) configurations indicates high variability.

**Implications:**  
* LCPs with 0 apps and 0 instances likely reflect misconfigurations—referential integrity should be checked.
* High-count outliers pose governance and audit risks; for composite or multi-regional applications, the data model may need additional metadata (e.g. component identifiers or region tags) to maintain clear traceability.

## H6: Some Lean Control Products are only linked to Technical Services and are not associated with any Business Applications or Application Services.

**Cardinality Table:**

| From Entity           | To Entity          | Relationship Name | Cardinality | Notes                                                                 | Example Records              |
|-----------------------|--------------------|-------------------|-------------|-----------------------------------------------------------------------|------------------------------|
| Lean Control Product  | Technical Service  | applies_to        | 1 → *       | These control products govern technical infrastructure, without mapping to business or app services. | LCSERV-999 → TS-010, TS-020 |

**Objective:**  
Determine whether certain Lean Control Products are strictly scoped to Technical Services, i.e., they have no associated Business Applications or Application Services.

**Observations:**  
* All Lean Control Products that are linked to Technical Services have no associated Business Applications or Application Services.

**Implications:**  
* Lean Control Products mapped to Technical Service have no visibility into the actual applications or environments they govern.
* We need to investigate how the retrospectively identify and map the Applications and Application Services for the 644 Lean Control Products that are linked to Technical Services.

## H7: Lean Control Products linked to Application Services are generally also associated with Business Applications.

**Cardinality Table:**

| From Entity           | To Entity            | Relationship Name | Cardinality | Notes                                                                            | Example Records                         |
|-----------------------|----------------------|-------------------|-------------|----------------------------------------------------------------------------------|------------------------------------------|
| Lean Control Product  | Application Service  | applies_to        | * → *       | LCPs may govern multiple environments.                                           | LCSERV-120 → Dev-Instance, QA-Instance   |
| Application Service   | Business Application | belongs_to        | * → 1       | Application Services typically map to one Business Application.                 | QA-Instance → ITBA-103                   |

**Objective:**  
Evaluate whether Lean Control Products that are applied to Application Services are indirectly also connected to Business Applications — via the service instance relationship.

**Observations:**  
* Most LCPs with Application Service links also have Business Application mappings.
* Many govern only 1–2 Business Applications and a handful of service instances.
* A few outliers govern very large scopes (e.g., one LCP with 108 instances and 46 Business Applications; others with >35 apps and >40 instances).
* Some LCPs have service instances but 0 Business Application mappings—likely data anomalies.

**Implications:**  
*  Outliers should be decomposed by domain—review each component and deployment environment, and map them to their correct ITBAs. 
*  Since applications can span one or multiple ITBAs, an LCP must support single and multi component scenarios and multi regional deployments.




