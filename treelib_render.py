# Script 2: treelib_render.py
# This script reads the CSV produced by generate_dataset.py,
# builds the hierarchy using treelib, and writes a Markdown
# representation of the tree to a .md file, including key metadata.

#!/usr/bin/env python3
import argparse
import pandas as pd
from treelib import Tree, Node

METADATA_FIELDS = [
    ('lean_control_service_id', 'LCP'),
    ('jira_backlog_id', 'Backlog'),
    ('it_business_service', 'Service'),
    ('it_service_instance', 'Instance'),
    ('environment', 'Env'),
    ('install_type', 'Type')
]


def build_tree(df):
    tree = Tree()
    # Create synthetic root
    tree.create_node(tag='Business Services', identifier='Business Services', data={})

    # Track which nodes have been added
    for row in df.itertuples():
        parent = row.parent if pd.notna(row.parent) else 'Business Services'
        node_id = row.id
        # build metadata dict, inheriting not needed here, just attach own values
        meta = {}
        for col, tag in METADATA_FIELDS:
            val = getattr(row, col, None)
            if pd.notna(val):
                meta[tag] = val
        # Determine label by entity type
        if parent == 'Business Services':
            ent_type = 'Business_Service'
            name = row.name
        elif df['parent'][(df['id'] == parent)].any():
            ent_type = 'App'
            name = row.name
        else:
            ent_type = 'Service_Instance'
            name = row.name
        tag = f"{ent_type}: {name}({node_id})"
        # attach metadata tags to tag string
        if meta:
            meta_str = '; '.join(f"{k}: {v}" for k, v in meta.items())
            tag = f"{tag} [{meta_str}]"
        # create node
        try:
            tree.create_node(tag=tag, identifier=node_id, parent=parent, data=meta)
        except Exception:
            # Skip duplicates
            pass
    return tree


def render_markdown(tree, out_file):
    lines = []
    for pre, fill, node in tree.walk(render=True):
        lines.append(f"{pre}{node.tag}")
    with open(out_file, 'w') as f:
        f.write('```text\n')
        f.write('\n'.join(lines))
        f.write('\n```\n')
    print(f"[treelib_render] Markdown tree written to {out_file}")


def main():
    parser = argparse.ArgumentParser(description="Render tree from CSV via treelib")
    parser.add_argument("--input", default="tree_edges.csv",
                        help="Input CSV file path from generate_dataset.py")
    parser.add_argument("--output", default="tree.md",
                        help="Output Markdown file path")
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    tree = build_tree(df)
    render_markdown(tree, args.output)

if __name__ == '__main__':
    main()
