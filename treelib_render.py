# treelib_render_simple.py
# Simple script to read id/parent/name from CSV and render hierarchy using treelib

#!/usr/bin/env python3
import argparse
import pandas as pd
from treelib import Tree


def render_tree(csv_path):
    # Read CSV with columns: id, parent, name
    df = pd.read_csv(csv_path, dtype=str)
    df.fillna('', inplace=True)

    tree = Tree()
    # Create synthetic root if not present in data
    root_id = 'Business Services'
    tree.create_node(tag='Business Services', identifier=root_id)

    # Add all nodes
    for _, row in df.iterrows():
        node_id = row['id']
        parent_id = row['parent'] or root_id
        tag = f"{row['name']} ({node_id})"
        # Create node if not exists
        if not tree.contains(node_id):
            # Ensure parent exists
            if not tree.contains(parent_id):
                tree.create_node(tag=parent_id, identifier=parent_id, parent=root_id)
            tree.create_node(tag=tag, identifier=node_id, parent=parent_id)

    # Display tree to console for verification
    tree.show()


def main():
    parser = argparse.ArgumentParser(description="Render basic hierarchy via treelib")
    parser.add_argument("--input", required=True, help="CSV file path with id,parent,name columns")
    args = parser.parse_args()
    render_tree(args.input)

if __name__ == '__main__':
    main()