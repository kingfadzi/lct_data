# Hypotheses & Design Questions

![Service types](./service_types.png)

---

## H1: Each Lean Control Product is linked to at least one service type—either one or more Application Service instances or one or more Technical Service instances—and if it’s only linked to Technical Services, it has no Application Service or Business Application mappings.
* All Lean Control Products map to either Application Services or are linked to Technical Services.
* 55% of Lean Control Products are mapped Application Services; 45% (≈ 644 Lean Control Products) are linked to Technical Services.
* Lean Control Products linked to Technical Services do not have links the Business Applications they control therefore lack visibility into the applications and business contexts they cover.

#### Related data:
* [application_services](./application_services.csv)
* [technical_services](./technical_services.csv)

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

## H3: Every Jira Project tracks exactly one Lean Control Product.
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