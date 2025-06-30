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


def query_lcp(conn, cfg, lcp_id):
    """Execute SQL from config against the database for the given ID."""
    query_cfg = cfg.get('sql', {})
    sql = query_cfg.get('query', '')
    params = query_cfg.get('params', ['lcp_id'])

    # Build parameters tuple in order defined in params list
    values = tuple(lcp_id if p == 'lcp_id' else None for p in params)

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, values)
        return cur.fetchall()


def main():
    parser = argparse.ArgumentParser(
        description="Query a Lean Control Product and return JSON output based on YAML config."
    )
    parser.add_argument(
        'lcp_id',
        help='The Lean Control Product service ID to query.'
    )
    parser.add_argument(
        '--config', '-c',
        default='config.yaml',
        help='Path to YAML config file (default: config.yaml).'
    )
    args = parser.parse_args()

    try:
        cfg = load_config(args.config)
        conn = get_db_connection(cfg)
        try:
            results = query_lcp(conn, cfg, args.lcp_id)
            print(json.dumps(results, default=str))
        finally:
            conn.close()
    except Exception as e:
        print(json.dumps({'error': str(e)}))
        sys.exit(1)


if __name__ == '__main__':
    main()
