#!/usr/bin/env python3
import argparse
import os
import yaml
import pandas as pd
from sqlalchemy import create_engine

def load_config(path: str) -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def build_conn(db: dict) -> str:
    return f"postgresql://{db['user']}:{db['password']}@{db['host']}:{db['port']}/{db['name']}"

def main():
    p = argparse.ArgumentParser(
        description="Generate hierarchy CSV from configurable base CTE"
    )
    p.add_argument(
        "--config", "-c",
        default="config.yaml",
        help="YAML config file (default: config.yaml)"
    )
    p.add_argument(
        "--base", "-b",
        required=True,
        choices=["by_si", "by_ts"],
        help="Which base CTE to use (by_si or by_ts)"
    )
    p.add_argument(
        "--output", "-o",
        help="Output CSV file path (default: <base>_hierarchy.csv)"
    )
    args = p.parse_args()

    # Determine default output if not supplied
    if not args.output:
        args.output = "si_hierarchy.csv" if args.base == "by_si" else "ts_hierarchy.csv"

    cfg    = load_config(args.config)
    engine = create_engine(build_conn(cfg["database"]))

    base_sql     = cfg["bases"][args.base]
    pipeline_sql = cfg["pipeline"]
    full_sql     = "\n".join([base_sql, pipeline_sql])

    df = pd.read_sql(full_sql, con=engine)
    df.to_csv(args.output, index=False)
    print(f"[generate_dataset] Wrote {len(df):,} rows to '{args.output}'")

if __name__ == "__main__":
    main()