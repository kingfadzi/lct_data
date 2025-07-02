import argparse
import pandas as pd
from treelib import Tree
import io
import contextlib


def build_children_map(df, root_id='Business Services'):
    children = {}
    for _, row in df.iterrows():
        parent = row['parent'] if row['parent'] else root_id
        children.setdefault(parent, []).append(row['id'])
    return children


def render_tree(csv_path, markdown_path):
    # Load CSV
    df = pd.read_csv(csv_path, dtype=str).fillna('')
    root_id = 'Business Services'

    # Build parent->children map and name lookup
    children_map = build_children_map(df, root_id)
    name_map = df.set_index('id')['name'].to_dict()

    # Initialize tree with synthetic root
    tree = Tree()
    tree.create_node(tag=root_id, identifier=root_id)

    # Recursively add nodes
    def add_nodes(parent_id):
        for child_id in children_map.get(parent_id, []):
            if child_id == root_id:
                continue
            if tree.contains(child_id):
                add_nodes(child_id)
                continue
            node_name = name_map.get(child_id, child_id)
            tag = f"{node_name} ({child_id})"
            tree.create_node(tag=tag, identifier=child_id, parent=parent_id)
            add_nodes(child_id)

    add_nodes(root_id)

    # Print to console
    tree.show()

    # Capture ASCII output
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        tree.show()
    ascii_tree = buf.getvalue()

    # Write to Markdown file
    with open(markdown_path, 'w') as f:
        f.write("```text\n")
        f.write(ascii_tree)
        f.write("\n```\n")

    print(f"Markdown hierarchy written to {markdown_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Render hierarchy via treelib to Markdown"
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
