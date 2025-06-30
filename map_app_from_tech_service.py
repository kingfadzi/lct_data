#!/usr/bin/env python3

import os
import argparse
import psycopg2
import psycopg2.extras
import yaml
import json
import sys


def load_config(path):
    """Load YAML configuration from the given file path."""
    with open(path, 'r') as f:
        return yaml.safe_load(f)


def get_db_connection(cfg):
    """Establish a database connection using parameters from config dict."""
    db_cfg = cfg.get('database', {})
    return psycopg2.connect(
        host=db_cfg.get('host', os.getenv('DB_HOST', 'localhost')),
        port=db_cfg.get('port', os.getenv('DB_PORT', '5432')),
        dbname=db_cfg.get('name', os.getenv('DB_NAME', 'scratchpad')),
        user=db_cfg.get('user', os.getenv('DB_USER', 'postgres')),
        password=db_cfg.get('password', os.getenv('DB_PASSWORD', ''))
    )


def query_lcp(conn, base_query, where_clauses, values):
    """Execute dynamically constructed SQL query."""
    sql = base_query
    if where_clauses:
        sql += " WHERE " + " AND ".join(where_clauses)

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, values)
        return cur.fetchall()


def main():
    parser = argparse.ArgumentParser(
        description="Query Lean Control Products with dynamic filters from YAML config."
    )
    parser.add_argument(
        '--config', '-c',
        default='config.yaml',
        help='Path to YAML config file (default: config.yaml).'
    )
    parser.add_argument(
        '--tech_service_id',
        help='Filter by Technical Service ID.'
    )
    parser.add_argument(
        '--itba',
        help='Filter by ITBA.'
    )

    args = parser.parse_args()

    # Load config and base query
    try:
        cfg = load_config(args.config)
        sql_cfg = cfg.get('sql', {})
        base_query = sql_cfg.get('base_query', '').strip()
        if not base_query:
            parser.error("Config file must define 'sql.base_query'.")
    except FileNotFoundError:
        parser.error(f"Config file not found: {args.config}")
    except yaml.YAMLError as e:
        parser.error(f"Error parsing config YAML: {e}")

    # Collect filters
    filters = []
    values = []
    mappings = {
        'tech_service_id': 'service_instance.correlation_id',
        'itba': 'business_app.correlation_id'
    }

    for arg_name, column in mappings.items():
        val = getattr(args, arg_name)
        if val is not None:
            filters.append(f"{column} = %s")
            values.append(val)

    if not filters:
        parser.error("At least one filter must be specified: --tech_service_id or --itba.")

    # Execute query
    try:
        conn = get_db_connection(cfg)
        try:
            results = query_lcp(conn, base_query, filters, values)
            print(json.dumps(results, default=str, indent=2))
        finally:
            conn.close()
    except Exception as e:
        print(json.dumps({'error': str(e)}, indent=2))
        sys.exit(1)

if __name__ == '__main__':
    main()
