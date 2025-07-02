# treelib_render_simple.py
# Simple script to read id/parent/name from CSV and render hierarchy using treelib,
# then write the ASCII tree into a Markdown file with proper wrapping.

#!/usr/bin/env python3
import argparse
import pandas as pd
from treelib import Tree
import io


def render_tree(csv_path, markdown_path):
    # Read CSV with columns: id, parent, name
    df = pd.read_csv(csv_path, dtype=str).fillna('')

    # Build the tree
    tree = Tree()
    root_id = 'Business Services'
    tree.create_node(tag='Business Services', identifier=root_id)

    for _, row in df.iterrows():
        node_id = row['id']
        parent_id = row['parent'] or root_id
        tag = f"{row['name']} ({node_id})"
        # Ensure parent exists
        if not tree.contains(parent_id):
            tree.create_node(tag=parent_id, identifier=parent_id, parent=root_id)
        # Add node
        if not tree.contains(node_id):
            tree.create_node(tag=tag, identifier=node_id, parent=parent_id)

    # Display to console
    tree.show()

    # Capture ASCII tree into Markdown
    buf = io.StringIO()
    tree.show(file=buf)
    ascii_tree = buf.getvalue()

    # Write to Markdown file
    with open(markdown_path, 'w') as f:
        f.write('```text\n')
        f.write(ascii_tree)
        f.write('\n```\n')
    print(f"Markdown tree written to {markdown_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Render basic hierarchy via treelib and export to Markdown"
    )
    parser.add_argument(
        "--input", required=True,
        help="CSV file path with id,parent,name columns"
    )
    parser.add_argument(
        "--output", default="tree.md",
        help="Output Markdown file path"
    )
    args = parser.parse_args()
    render_tree(args.input, args.output)


if __name__ == '__main__':
    main()