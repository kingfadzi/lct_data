#!/usr/bin/env python3

import argparse
import json
import logging
import os
import yaml
import pandas as pd
from sqlalchemy import create_engine, text
import sqlparse

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# --- Helpers ---

def load_config(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def build_service_tree(df):
    # Assign app_id as parent_id if present, else child_id
    df = df.copy()
    df['app_id'] = df['parent_id'].combine_first(df['child_id'])
    df['app_name'] = df['parent_name'].combine_first(df['child_name'])

    def get_instances(inst_df):
        return inst_df[['instance_id', 'it_service_instance', 'environment', 'install_type']].to_dict('records')

    def get_children(app_df):
        children = app_df[app_df['parent_id'].notna()]
        if children.empty:
            return []
        return children.groupby('child_id').apply(
            lambda g: {
                'app_id': g['child_id'].iloc[0],
                'app_name': g['child_name'].iloc[0],
                'service_instances': get_instances(g)
            }
        ).tolist()

    def get_apps(svc_df):
        apps = []
        for app_id, app_df in svc_df.groupby('app_id'):
            main_instances = app_df[app_df['parent_id'].isna()]
            apps.append({
                'app_id': app_id,
                'app_name': app_df['app_name'].iloc[0],
                'service_instances': get_instances(main_instances),
                'children': get_children(app_df)
            })
        return apps

    services = df.groupby('biz_service_id').apply(
        lambda svc_df: {
            'it_business_service': svc_df['biz_service_id'].iloc[0],
            'lean_control_service_id': svc_df['lean_control_service_id'].iloc[0],
            'jira_backlog_id': svc_df['jira_backlog_id'].iloc[0],
            'apps': get_apps(svc_df)
        }
    ).tolist()

    return services

# --- Main ---

def main():
    parser = argparse.ArgumentParser(
        prog="find_by_product_id.py",
        description="Return business services with nested apps and service instances using pandas"
    )
    parser.add_argument(
        '-c', '--config', default='config.yaml',
        help='Path to YAML config (default: config.yaml)'
    )
    parser.add_argument(
        'lean_control_service_ids', nargs='*', metavar='LEAN_CONTROL_SERVICE_ID',
        help='Zero or more lean_control_service_id values; if omitted, returns all'
    )
    args = parser.parse_args()

    cfg = load_config(args.config)
    db = cfg['database']
    url = (
        f"postgresql+psycopg2://{db['user']}:{db['password']}"
        f"@{db['host']}:{db['port']}/{db['name']}"
    )
    engine = create_engine(url)

    sql = text("""
    SELECT
      si.it_business_service AS biz_service_id,
      lcp.lean_control_service_id,
      pbl.jira_backlog_id,
      parent.correlation_id   AS parent_id,
      parent.business_application_name AS parent_name,
      child.correlation_id    AS child_id,
      child.business_application_name AS child_name,
      si.correlation_id       AS instance_id,
      si.it_service_instance,
      si.environment,
      si.install_type
    FROM public.lean_control_application lcp
    JOIN public.vwsfitserviceinstance si
      ON lcp.servicenow_app_id = si.correlation_id
    JOIN public.lean_control_product_backlog_details pbl
      ON pbl.lct_product_id = lcp.lean_control_service_id
    JOIN public.vwsfbusinessapplication child
      ON si.business_application_sysid = child.business_application_sys_id
    LEFT JOIN public.vwsfbusinessapplication parent
      ON child.application_parent_correlation_id = parent.correlation_id
    """)

    params = {}
    if args.lean_control_service_ids:
        sql = text(sql.text + " WHERE lcp.lean_control_service_id = ANY(:ids) ")
        params['ids'] = args.lean_control_service_ids

    # Log SQL
    raw_sql = sql.bindparams(**params).compile(engine, compile_kwargs={"literal_binds": True})
    formatted_sql = sqlparse.format(str(raw_sql), reindent=True, keyword_case='upper')
    logger.debug("Generated SQL:\n%s", formatted_sql)

    # Load into DataFrame
    df = pd.read_sql(sql, engine, params=params)

    # Build and print nested structure
    services = build_service_tree(df)
    print(json.dumps(services, indent=2))

if __name__ == '__main__':
    main()
