#!/usr/bin/env python3
import argparse
import yaml
import pandas as pd
from sqlalchemy import create_engine

def infer_cardinality(child_df: pd.DataFrame, fk_col: str) -> str:
    """
    Returns '1:N' if any fk value repeats in child_df[fk_col],
    else '1:1'.
    """
    total    = len(child_df)
    distinct = child_df[fk_col].nunique(dropna=False)
    return "1:N" if total > distinct else "1:1"

def load_db_url(config_path: str) -> str:

    with open(config_path, 'r') as f:
        cfg = yaml.safe_load(f)
    db = cfg.get('database', {})
    return "postgresql://{user}:{pwd}@{host}:{port}/{name}".format(
        user=db['user'],
        pwd=db['password'],
        host=db['host'],
        port=db['port'],
        name=db['name']
    )

def main():
    parser = argparse.ArgumentParser(
        description="Infer FK cardinality driven by YAML configs."
    )
    parser.add_argument(
        "-c", "--config", default="config.yaml",
        help="Path to YAML file with database connection info (default: config.yaml)"
    )
    args = parser.parse_args()

    # 1) Build DB URL from config.yaml or provided file
    db_url = load_db_url(args.config)

    # 2) Load relationships list from relationships.yaml
    with open("relationships.yaml", 'r') as f:
        rel_cfg = yaml.safe_load(f)
    relations = rel_cfg.get('relationships', [])
    if not relations:
        raise SystemExit("No relationships found in relationships.yaml.")

    # 3) Connect to your DB
    engine = create_engine(db_url)

    # 4) Loop and infer
    results = []
    for rel in relations:
        child_tbl = rel['child_table']
        fk_col    = rel['fk_col']
        parent_tbl= rel['parent_table']
        pk_col    = rel.get('pk_col', 'id')

        # only pull the FK column for speed
        df_child = pd.read_sql_table(
            table_name=child_tbl,
            con=engine,
            columns=[fk_col]
        )
        card = infer_cardinality(df_child, fk_col)
        results.append({
            "child_table":  child_tbl,
            "fk_col":       fk_col,
            "parent_table": parent_tbl,
            "pk_col":       pk_col,
            "cardinality":  card
        })

    # 5) Present results
    df_res = pd.DataFrame(results)
    print(df_res.to_markdown(index=False))

if __name__ == "__main__":
    main()