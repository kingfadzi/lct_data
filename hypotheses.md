# Hypotheses & Design Questions


![Service types](./service_types.png)

---

## H1: Each Lean Control Product is associated with at least one service type—either Application Service instances or Technical Service—and if linked only to Technical Services, it lacks Application Service or Business Application mappings.
* 55% of Lean Control Products are mapped Application Services; 45% (≈ 644 Lean Control Products) are linked to Technical Services.
* Lean Control Products linked to Technical Services do not have links to the Business Applications they control.

#### Related data:
* [application_services](./application_services.csv)
* [technical_services](./technical_services.csv)

### Design Considerations:
HMW (How Might We):
* HMW map Lean Control Products linked to Technical Services to their missing Application and Application Service contexts, even when the system data is incomplete?
* HMW support accurate mapping of Lean Control Products to applications composed of multiple ITBAs and deployment environments, each with its own Application Service instance?
* HMW automate the validation and mapping of Lean Control Products to Application and Application Service where data is already available, to ensure baseline integrity?

---

## H2: Lean Control Products vary in how many Business Applications they control: some control none, some exactly one, and some span multiple applications.
* 399 Lean Control Products control 0 Business Applications; 449 control exactly 1; 317 control more than 1.
* Lean Control Products mapped to 0 apps mean: No visibility onto any specific application or mean data integrity issues.
* Mapping 1 Lean Control Product to 1 Business Application is Clear and easy to manage, but will break down for multi‑component or multi‑regional apps (front end, back end, API, APAC/EU, etc.).
* Mapping 1 Lean Control Product to more than 1 app: Fits complex or regionalized applications, but keeping traceability requires extending the data model to record both the Business Application ID and the Application Service when applying controls.

#### Related data:
* [lcp_to_business_applications](./lcp_to_business_applications.csv)

### Design Questions:
HMW (How Might We):
* HMW evolve the data model so that 1 Lean Control Product can control multiple Business Applications and their corresponding Application Services without losing the ability to audit control coverage?

---

## H3: Every Jira Project tracks exactly one Lean Control Product.
* A strict one-to-one mapping between Jira backlogs and Lean Control Products ensures consistent governance.
* Of all projects, 1,221 correctly track one Lean Control Product; 122 have no Lean Control Product link; 3 track multiple Lean Control Products.
* The 125 anomalous projects break the governance model and risk untracked work or duplicated scopes.

### Design Questions:
HMW (How Might We):
* HMW detect and automatically correct anomalies in the Jira Project–Lean Control Product mapping to maintain data integrity?
---

## H4: Each Business Application is controlled by exactly one Lean Control Product
* Predominant 1:1 mapping: Roughly 89% (1,713) of applications follow the simple, one-to-one Lean Control Product to Application mapping model, making their control lifecycles straightforward to manage.
* The other 11% (203) mappings appear anomalous and warrant investigation.
* We also need to understand how the mapping of 1 Lean Control Product to one itba applies to larger applications made up of multiple components each with its own ITBA.

### Design Questions:
HMW (How Might We):
* HMW represent and control large applications composed of multiple ITBAs using a single Lean Control Product, while preserving clarity and control over each component?
---

## H5: Most Lean Control Products are actively linked to applications and environments.
* Most Lean Control Products cluster at low app and instance counts (median = 1).
* A few outliers exist (e.g. one LCP with 46 apps and 108 instances).
* The long tail of rare (inst_count, app_count) configurations indicates high variability.
* LCPs with 0 apps and 0 instances likely reflect misconfigurations—referential integrity should be checked.
* High-count outliers pose governance and audit risks; for composite or multi-regional applications, the data model may need additional metadata (e.g. component identifiers or region tags) to maintain clear traceability.

#### Related data:
* [lcp_to_business_application_service_instances](./lcp_to_business_application_service_instances.csv)

### Design Questions:
HMW (How Might We):
* HMW evolve the data model to support both simple 1:1 mappings and complex, multi-region or multi-component environments while preserving traceability and control clarity?
* HMW retrofit Lean Control Product outliers (e.g. LCP with 46 apps and 108 instances) by decomposing and remapping them into simpler, well-scoped units—without disrupting existing user workflows or visibility?
* HMW automate the detection of Lean Control Products with zero mappings to ensure data integrity and governance?
---

## So what...?

### Mapping Integrity & Completeness

- Enforce clear rules so no product is partially mapped—avoiding gaps in the key entities.
- Eliminate these specific gap cases in our data:
    - **Orphan LCPs:** 399 Lean Control Products control 0 Business Applications—no app context at all.
    - **Blind-Spot LCPs:** ~644 (45%) link only to Technical Services, lacking any Application Service or Business Application mappings.
    - **Unlinked Jira Projects:** 122 projects have no Lean Control Product association, leaving work outside the control framework.
    - **Unmapped Business Applications:** 203 Business Applications have zero or multiple Lean Control Product links, breaking the one-to-one control assumption.

### Data Model Evolution

- **Alignment with Business & ServiceNow CSDM:** Align the LCT data model with real-world service constructs and the ServiceNow Common Service Data Model for semantic consistency.

### Complexity & Outlier Management

- **Outlier Identification:** Detect Lean Control Products that control an abnormally large number of apps or instances.
- **Decomposition Targets:** Split these into component-, region-, or environment-focused Lean Control Products with clear, manageable scopes.
- **Seamless Remapping:** Migrate controls into the new Lean Control Products without disrupting existing user workflows or dashboards.