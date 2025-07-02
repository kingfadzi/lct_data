# generate_dataset.py
# This script connects to your database using settings from config.yaml,
# runs the SQL to build the edges dataset (using it_business_service_sysid join),
# and writes the result to a CSV for downstream consumption.

import argparse
import pandas as pd
from sqlalchemy import create_engine
import yaml
import os

SQL = """
WITH
  base AS (
    /* Use it_business_service_sysid to join business service */
    SELECT
      fia.lean_control_service_id       AS lean_control_service_id,
      lpbd.jira_backlog_id              AS jira_backlog_id,
      si.it_business_service_sysid      AS it_business_service_sysid,
      bs.service                        AS business_service_name,
      bap.correlation_id                AS parent_id,
      bap.business_application_name     AS parent_name,
      bac.correlation_id                AS child_id,
      bac.business_application_name     AS child_name,
      si.correlation_id                 AS instance_id,
      si.it_service_instance           AS it_service_instance,
      si.environment                    AS environment,
      si.install_type                   AS install_type
    FROM public.vwsfitserviceinstance AS si
    JOIN public.lean_control_application AS fia
      ON fia.servicenow_app_id = si.correlation_id
    JOIN public.lean_control_product_backlog_details AS lpbd
      ON lpbd.lct_product_id = fia.lean_control_service_id
    JOIN public.vwsfbusinessapplication AS bac
      ON si.business_application_sysid = bac.business_application_sys_id
    LEFT JOIN public.vwsfbusinessapplication AS bap
      ON bac.application_parent_correlation_id = bap.correlation_id
    JOIN public.vwsfitbusinessservice AS bs
      ON si.it_business_service_sysid = bs.service_correlation_id
  ),
  distinct_services AS (
    SELECT DISTINCT
      it_business_service_sysid     AS id,
      business_service_name         AS name,
      lean_control_service_id,
      jira_backlog_id
    FROM base
  ),
  edges AS (
    -- 0) Synthetic root
    SELECT
      NULL               AS parent,
      'Business Services' AS id,
      'Business Services' AS name,
      NULL               AS lean_control_service_id,
      NULL               AS jira_backlog_id,
      NULL               AS parent_id,
      NULL               AS parent_name,
      NULL               AS child_id,
      NULL               AS child_name,
      NULL               AS instance_id,
      NULL               AS it_business_service_sysid,
      NULL               AS it_service_instance,
      NULL               AS environment,
      NULL               AS install_type
    UNION ALL
    -- 1) Root → each Business Service
    SELECT
      'Business Services'       AS parent,
      ds.id                     AS id,
      ds.name                   AS name,
      ds.lean_control_service_id AS lean_control_service_id,
      ds.jira_backlog_id        AS jira_backlog_id,
      NULL                      AS parent_id,
      NULL                      AS parent_name,
      NULL                      AS child_id,
      NULL                      AS child_name,
      NULL                      AS instance_id,
      ds.id                     AS it_business_service_sysid,
      NULL                      AS it_service_instance,
      NULL                      AS environment,
      NULL                      AS install_type
    FROM distinct_services AS ds
    UNION ALL
    -- 2) Business Service → Parent-level Apps
    SELECT
      b.it_business_service_sysid AS parent,
      b.parent_id                AS id,
      b.parent_name              AS name,
      b.lean_control_service_id,
      b.jira_backlog_id,
      b.parent_id,
      b.parent_name,
      b.child_id,
      b.child_name,
      b.instance_id,
      b.it_business_service_sysid,
      b.it_service_instance,
      b.environment,
      b.install_type
    FROM base AS b
    WHERE b.parent_id IS NOT NULL
    UNION ALL
    -- 3) Business Service → Standalone Apps
    SELECT
      b.it_business_service_sysid AS parent,
      b.child_id                 AS id,
      b.child_name               AS name,
      b.lean_control_service_id,
      b.jira_backlog_id,
      b.parent_id,
      b.parent_name,
      b.child_id,
      b.child_name,
      b.instance_id,
      b.it_business_service_sysid,
      b.it_service_instance,
      b.environment,
      b.install_type
    FROM base AS b
    WHERE b.parent_id IS NULL
    UNION ALL
    -- 4) Parent Apps → Child Apps
    SELECT
      b.parent_id                AS parent,
      b.child_id                 AS id,
      b.child_name               AS name,
      b.lean_control_service_id,
      b.jira_backlog_id,
      b.parent_id,
      b.parent_name,
      b.child_id,
      b.child_name,
      b.instance_id,
      b.it_business_service_sysid,
      b.it_service_instance,
      b.environment,
      b.install_type
    FROM base AS b
    WHERE b.parent_id IS NOT NULL
    UNION ALL
    -- 5) Apps → Service Instances
    SELECT
      b.child_id                 AS parent,
      b.instance_id              AS id,
      b.it_service_instance      AS name,
      b.lean_control_service_id,
      b.jira_backlog_id,
      b.parent_id,
      b.parent_name,
      b.child_id,
      b.child_name,
      b.instance_id,
      b.it_business_service_sysid,
      b.it_service_instance,
      b.environment,
      b.install_type
    FROM base AS b
  )
SELECT
  id,
  parent,
  name,
  lean_control_service_id,
  jira_backlog_id,
  parent_id,
  parent_name,
  child_id,
  child_name,
  instance_id,
  it_business_service_sysid,
  it_service_instance,
  environment,
  install_type
FROM edges
ORDER BY
  CASE WHEN id = 'Business Services' THEN 0 ELSE 1 END,
  parent,
  id;
"""

def main():
    parser = argparse.ArgumentParser(description="Generate tree-edge dataset CSV")
    parser.add_argument("--config", default="config.yaml",
                        help="Path to YAML config with database credentials")
    parser.add_argument("--output", default="tree_edges.csv",
                        help="Output CSV file path")
    args = parser.parse_args()

    if not os.path.exists(args.config):
        raise FileNotFoundError(f"Config file not found: {args.config}")
    cfg = yaml.safe_load(open(args.config))
    db = cfg.get("database", {})
    user = db.get("user")
    password = db.get("password")
    host = db.get("host")
    port = db.get("port")
    name = db.get("name")
    conn_str = f"postgresql://{user}:{password}@{host}:{port}/{name}"

    engine = create_engine(conn_str)
    df = pd.read_sql(SQL, engine)
    df.to_csv(args.output, index=False)
    print(f"[generate_dataset] Wrote {len(df)} rows to {args.output}")

if __name__ == "__main__":
    main()

# treelib_render_simple.py unchanged for structure verification
# ...
