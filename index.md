| From Entity              | To Entity            | Relationship Name | Cardinality | Notes                                              |
| ------------------------ | -------------------- | ----------------- | ----------- | -------------------------------------------------- |
| **Team**                 | Jira Project         | owns              | 1 --> \*    | A team owns multiple Jira projects                 |
| **Team**                 | Git Repo             | owns              | 1 --> \*    | A team owns multiple repositories                  |
| **Team**                 | Business Application | owns              | 1 --> \*    | A team owns multiple apps                          |
| **Jira Project**         | Git Repo             | uses              | 1 --> \*    | A project uses multiple repos                      |
| **Jira Project**         | Business Application | delivers          | 1 --> 1     | A project delivers one app                         |
| **Jira Project**         | Risk Stories (IDs)   | tracks            | 1 --> \*    | Risk stories are Jira issue keys stored in a field |
| **Git Repo**             | Business Application | supports          | \* --> 1    | Many repos support one app                         |
| **Business Application** | Application Service  | realized\_by      | 1 --> \*    | An app is realized by services                     |
| **Application Service**  | Business Application | realizes          | \* --> 1    | Each service maps to one app                       |
| **Lean Control Product** | Business Application | governs           | 1 --> \*    | One LCP governs many apps                          |
