#!/usr/bin/env python3
import argparse
import yaml
import pandas as pd
from sqlalchemy import create_engine
from collections import defaultdict
from itertools import combinations

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
    return f"postgresql://{db['user']}:{db['password']}@{db['host']}:{db['port']}/{db['name']}"

def main():
    parser = argparse.ArgumentParser(
        description="Infer FK cardinality driven by YAML configs."
    )
    parser.add_argument(
        "-c", "--config", default="config.yaml",
        help="Path to YAML file with database connection info (default: config.yaml)"
    )
    args = parser.parse_args()

    # 1) Build DB URL
    db_url = load_db_url(args.config)

    # 2) Load relationships
    with open("relationships.yaml", 'r') as f:
        rel_cfg = yaml.safe_load(f)
    relations = rel_cfg.get('relationships', [])
    if not relations:
        raise SystemExit("No relationships found in relationships.yaml.")

    # 3) Connect
    engine = create_engine(db_url)

    # 4) Infer cardinalities
    results = []
    for rel in relations:
        child_tbl = rel['child_table']
        fk_col    = rel['fk_col']
        parent_tbl= rel['parent_table']
        pk_col    = rel.get('pk_col', 'id')

        df_child = pd.read_sql_table(
            table_name=child_tbl,
            con=engine,
            columns=[fk_col]
        )
        card = infer_cardinality(df_child, fk_col)
        results.append({
            "parent_table": parent_tbl,
            "pk_col":       pk_col,
            "child_table":  child_tbl,
            "fk_col":       fk_col,
            "cardinality":  card
        })

    # 5) Generic M:N detection via join tables with ≥2 one-to-many legs
    child_to_parents = defaultdict(list)
    for r in results:
        if r["cardinality"] == "1:N":
            child_to_parents[r["child_table"]].append(r["parent_table"])

    for child_tbl, parents in child_to_parents.items():
        if len(parents) >= 2:
            for p1, p2 in combinations(parents, 2):
                print(f"Detected M:N between {p1} and {p2} via {child_tbl}")

    # 6) Print results with parent first
    df_res = pd.DataFrame(results)[[
        "parent_table",
        "pk_col",
        "child_table",
        "fk_col",
        "cardinality"
    ]]
    print(df_res.to_markdown(index=False))

if __name__ == "__main__":
    main()