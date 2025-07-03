# Current vs Future State of Entity Relationships

---

### **1. Summary of Impacts (Current Model)**

- **Control**: Many-to-many relationships make it hard to define clear ownership, apply consistent policies, and maintain auditable trails.
- **Technical**: They lead to data duplication, overly complex joins, poor performance, and difficulty enforcing data integrity at the database level.

### **2.  Key ServiceNow CMDB Entities Applied**
_The sections and hierarchies that follow are based on the ServiceNow CMDB’s canonical structure (Business Service → Business Application → Service Instance)._
- **Business Service**: Represents a logical grouping of applications and their service instances (A **Technical Service** is an IT Business Service WHERE category='Technical Service').
- **Business Application**: A software solution that provides specific business functionality, linked to one or more service instances.
- **Service Instance**: A specific deployment of an application, such as a production or staging environment.


### **3. Current → Future Entity Model**

| **Entity / Relationship** | **Current Type** | **Future Type** | **Rationale for Change** | **Control Anchor** | **Technical Purpose**                                    |
| --- | --- | --- | --- | --- |----------------------------------------------------------|
| **Lean Control Product → Business Service** | many-to-many | one-to-one | Simplify ownership: each LCP has one primary service | Policy Boundary, Compliance Scope | Groups applications under a common compliance posture    |
| **Business Service → Application** | many-to-one | one-to-many | Reflect real usage: services support multiple apps | Risk Traceability, Functional Scope | Links business risks and ownership to each app           |
| **Application → Service Instance** | one-to-many | one-to-many | No change—apps still deploy to many instances | Change Control Integration | Represents CIs linked to change requests                 |
| **Application → Jira Backlog** | many-to-many | one-to-one | Enforce one backlog per app | Risk Story (Jira) | Documents how known risks are tracked per app            |
| **Lean Control Product → Application** | many-to-many | — (removed) | Now inferred via LCP→BS→App chain | — | —                                                        |
| **Lean Control Product → Service Instance** | many-to-many | — (removed) | Traceability now via App | — | —                                                        |
| **Business Service → Service Instance** | one-to-one | — (removed) | Handled at the app level | — | —                                                        |
| **Jira Backlog → Business Service** | many-to-many | — (removed) | Backlogs belong to apps, not directly to services | — | —                                                        |
| **Lean Control Product → Jira Backlog** | one-to-one | — (removed) | Jira link moves to App level | — | —                                                        |
| **Jira Backlog → Lean Control Product** | one-to-one | — (removed) | Traceability via App | — | —                                                        |
| **Jira Backlog → Application** | many-to-many | one-to-one | Backlog ownership moves to app | Risk Story (Jira) | Documents how known risks are tracked per app (inverted) |
| **Jira Backlog → Service Instance** | many-to-many | — (removed) | Unnecessary in normalized model | — | —                                                        |

---

### **4. Benefits of the New Normalized Model**

---

- **Control**
    - **Clear Ownership**: Every control is anchored at exactly one entity (1:1 or 1:many), so no ambiguity.
    - **Consistent Policy Application**: Explicit, enforced cardinalities ensure you know exactly where each control applies.
    - **End-to-End Auditability**: A clean LCP → Service → App → Instance path produces a complete, tamper-proof trail.
    - **Standards Alignment**: Aligns with the ServiceNow CMDB hierarchy, integrates into the SDLC process, supports Agile software development teams, and accommodates microservices deployed across multiple regions.

- **Technical**
    - **Simplified Queries**: Direct join paths replace ad-hoc many-to-many hacks, speeding up reads and reports.
    - **Enforced Integrity**: Referential constraints or link-table patterns eliminate orphaned or mismatched records.
    - **Improved Performance & Scalability**: Normalization reduces duplication, shrinks data volumes, and accelerates operations.
    - **Easier Maintenance**: Predictable, clear relationships make schema evolution and downstream integrations far safer and less error-prone.


### 5. Composite Normalized View with Legacy Annotations

This section presents a **composite representation** in which all entities are arranged in a fully normalized, one-to-many hierarchy, while retaining inline annotations of the existing many-to-many mappings to illustrate their current configuration. Two views are available based on the current underlying model:

- **Service Instance View (`si_hierarchy`)**  
  Shows entities mapped directly to **Service Instances**, with legacy LCP and backlog annotations preserved.  
  [Entities currently mapped to Technical Services](./ts_hierarchy.md)

- **Technical Service View (`ts_hierarchy`)**  
  Shows entities mapped to **ServiceNow Technical Services**, likewise annotated with current many-to-many links.  
  [Entities currently mapped to Service Instances](./si_hierarchy.md)

#### Example Slice

```text
Business Service (SRVC-002) [LCP: PROD-001; Backlog: BACK-101]
└─ Business Application (ITBA-12345) [LCP: PROD-002; Backlog: BACK-101]
   └─ Service Instance (SVCINST-0001) [LCP: PROD-003; Backlog: BACK-103]
```

> **Note:** The bracketed lists reflect the existing many-to-many relationships in the current model. This overlay makes it immediately clear where redundant links, orphaned mappings, and control ambiguities exist—providing a direct contrast to the clean, normalized hierarchy that underpins the future target state.

