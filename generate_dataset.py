import argparse
import pandas as pd
from sqlalchemy import create_engine
import yaml
import os

SQL = """
WITH base AS (
  SELECT
    fia.lean_control_service_id      AS lean_control_service_id,
    lpbd.jira_backlog_id             AS jira_backlog_id,
    si.it_business_service_sysid     AS service_id,
    bs.service                       AS service_name,
    bac.correlation_id               AS app_id,
    bac.business_application_name    AS app_name,
    si.correlation_id                AS instance_id,
    si.it_service_instance          AS instance_name
  FROM public.vwsfitserviceinstance AS si
  JOIN public.lean_control_application      AS fia
    ON fia.servicenow_app_id = si.correlation_id
  JOIN public.lean_control_product_backlog_details AS lpbd
    ON lpbd.lct_product_id = fia.lean_control_service_id
  JOIN public.vwsfbusinessapplication        AS bac
    ON si.business_application_sysid = bac.business_application_sys_id
  JOIN public.vwsfitbusinessservice          AS bs
    ON si.it_business_service_sysid = bs.service_correlation_id
),
services AS (
  SELECT DISTINCT
    service_id AS id,
    service_name AS name,
    lean_control_service_id,
    jira_backlog_id
  FROM base
),
edges AS (
  -- Root
  SELECT
    NULL           AS parent,
    'Business Services' AS id,
    'Business Services' AS name,
    NULL           AS lean_control_service_id,
    NULL           AS jira_backlog_id,
    NULL           AS app_id,
    NULL           AS app_name,
    NULL           AS instance_id,
    NULL           AS instance_name
  UNION ALL
  -- Services under root
  SELECT
    'Business Services' AS parent,
    s.id                 AS id,
    s.name               AS name,
    s.lean_control_service_id,
    s.jira_backlog_id,
    NULL                 AS app_id,
    NULL                 AS app_name,
    NULL                 AS instance_id,
    NULL                 AS instance_name
  FROM services AS s
  UNION ALL
  -- Apps under service
  SELECT
    b.service_id AS parent,
    b.app_id      AS id,
    b.app_name    AS name,
    b.lean_control_service_id,
    b.jira_backlog_id,
    b.app_id      AS app_id,
    b.app_name    AS app_name,
    NULL          AS instance_id,
    NULL          AS instance_name
  FROM base AS b
  UNION ALL
  -- Instances under app
  SELECT
    b.app_id        AS parent,
    b.instance_id   AS id,
    b.instance_name AS name,
    b.lean_control_service_id,
    b.jira_backlog_id,
    b.app_id        AS app_id,
    b.app_name      AS app_name,
    b.instance_id   AS instance_id,
    b.instance_name AS instance_name
  FROM base AS b
)
SELECT
  id,
  parent,
  name,
  lean_control_service_id,
  jira_backlog_id,
  app_id,
  app_name,
  instance_id,
  instance_name
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
    conn_str = f"postgresql://{db['user']}:{db['password']}@{db['host']}:{db['port']}/{db['name']}"

    engine = create_engine(conn_str)
    df = pd.read_sql(SQL, engine)
    df.to_csv(args.output, index=False)
    print(f"[generate_dataset] Wrote {len(df)} rows to {args.output}")

if __name__ == "__main__":
    main()

# treelib_render_simple.py unchanged for structure verification
# ...
# ...
