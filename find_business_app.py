#!/usr/bin/env python3

import os
import argparse
import yaml
import psycopg2
import psycopg2.extras
import json
import sys

def load_config(path):

    with open(path, 'r') as f:
        return yaml.safe_load(f)

def get_db_connection(cfg):
    db = cfg.get('database', {})
    return psycopg2.connect(
        host=db.get('host',     os.getenv('DB_HOST',     'localhost')),
        port=db.get('port',     os.getenv('DB_PORT',     '5432')),
        dbname=db.get('name',   os.getenv('DB_NAME',     'scratchpad')),
        user=db.get('user',     os.getenv('DB_USER',     'postgres')),
        password=db.get('password', os.getenv('DB_PASSWORD', ''))
    )

def main():
    parser = argparse.ArgumentParser(
        description="Find Business Application(s) by technical-service correlation_id"
    )
    parser.add_argument(
        '-c','--config',
        default='config.yaml',
        help='Path to YAML config (default: config.yaml)'
    )
    parser.add_argument(
        '--service_correlation_id',
        required=True,
        help='Value for business_service.service_correlation_id to filter on'
    )
    args = parser.parse_args()

    # Load DB config
    try:
        cfg = load_config(args.config)
    except Exception as e:
        parser.error(f"Failed to load {args.config}: {e}")

    # Parameter list
    params = [args.service_correlation_id]

    # Build SQL with the two joins you specified
    sql_lines = [
        "SELECT",
        "  ba.*",
        "FROM public.vwsfitbusinessservice AS bs",
        "JOIN public.vwsfitserviceinstance AS si",
        "  ON bs.it_business_service_sysid = si.it_business_service_sysid",
        "JOIN public.vwsfbusinessapplication AS ba",
        "  ON si.business_application_sysid = ba.business_application_sys_id",
        "WHERE bs.service_correlation_id = %s"
    ]
    full_sql = "\n".join(sql_lines)

    # Debug: print SQL and params
    print("=== Generated SQL ===\n")
    print(full_sql, "\n")
    print("=== Parameters ===")
    print(params, "\n")

    try:
        conn = get_db_connection(cfg)
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(full_sql, params)
            rows = cur.fetchall()
        conn.close()
        print(json.dumps(rows, default=str, indent=2))
    except Exception as e:
        sys.stderr.write(f"ERROR: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
