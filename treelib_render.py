# Script 2: treelib_render.py
# This script reads the CSV produced by generate_dataset.py,
# builds the hierarchy using treelib, and writes a Markdown
# representation of the tree to a .md file, including key metadata.

#!/usr/bin/env python3
import argparse
import pandas as pd
from treelib import Tree

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
    root_id = 'Business Services'
    tree.create_node(tag='Business Services', identifier=root_id)

    # Add all nodes
    for row in df.itertuples():
        parent = row.parent if pd.notna(row.parent) else root_id
        node_id = row.id
        # Build metadata dict
        meta = {}
        for col, tag in METADATA_FIELDS:
            val = getattr(row, col, None)
            if pd.notna(val):
                meta[tag] = val
        # Determine entity label
        name = row.name
        # tag will be updated when rendering
        tree.create_node(tag=name, identifier=node_id, parent=parent, data=meta)
    return tree


def render_markdown(tree, out_file):
    lines = []
    def recurse(node_id, prefix, is_last):
        node = tree.get_node(node_id)
        # Branch characters
        branch = '└── ' if is_last else '├── '
        line = prefix + (branch if prefix else '')
        # Build label
        if node_id == tree.root:
            label = node.tag
        else:
            # Determine type
            if node.is_leaf():
                ent_type = 'Service_Instance'
                tags = ['Instance', 'InstID', 'Env', 'Type']
            elif node.bpointer == tree.root:
                ent_type = 'Business_Service'
                tags = ['LCP', 'Backlog', 'Service']
            else:
                ent_type = 'App'
                tags = ['App', 'AppID', 'LCP', 'Backlog']
            # Base label
            base = f"{ent_type}: {node.tag}({node.identifier})"
            # Metadata
            parts = []
            meta = node.data or {}
            # For App, we include AppID, AppName
            if ent_type == 'App':
                parts.append(f"AppID: {node.identifier}")
                parts.append(f"AppName: {node.tag}")
            for key in tags:
                val = meta.get(key)
                if val is not None and key not in ['AppID','AppName']:
                    parts.append(f"{key}: {val}")
            label = base + (' [' + '; '.join(parts) + ']' if parts else '')
        lines.append(line + label)
        # Recurse
        children = tree.children(node_id)
        count = len(children)
        for idx, child in enumerate(children):
            next_prefix = prefix + ('    ' if is_last else '│   ')
            recurse(child.identifier, next_prefix, idx == count-1)

    recurse(tree.root, '', True)

    # Write to file
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
