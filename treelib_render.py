#!/usr/bin/env python3
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

    # Build metadata map (drop duplicate ids to ensure unique index)
    df_meta = df.drop_duplicates(subset=['id'], keep='first')
    meta_map = df_meta.set_index('id')[['lean_control_service_id', 'jira_backlog_id']].to_dict('index')

    # Clean children_map: retain only valid parents
    valid_ids = set(df['id']) | {root_id}
    clean_map = {pid: kids[:] for pid, kids in children_map.items() if pid in valid_ids}
    extras = []
    for pid, kids in children_map.items():
        if pid not in valid_ids:
            extras.extend(kids)
    if extras:
        clean_map.setdefault(root_id, []).extend(extras)
    children_map = clean_map

    # Initialize tree with synthetic root
    tree = Tree()
    tree.create_node(tag=root_id, identifier=root_id)

    # Recursive function carrying inherited metadata
    def add_nodes(parent_id, inherited_meta):
        for child_id in children_map.get(parent_id, []):
            if child_id == root_id:
                continue
            if tree.contains(child_id):
                add_nodes(child_id, inherited_meta)
                continue
            # Build node tag with only changed metadata
            node_name = name_map.get(child_id, child_id)
            own_meta = meta_map.get(child_id, {})
            parts = []
            # Only include tag if differs from inherited
            for key, label in [('lean_control_service_id', 'LCP'), ('jira_backlog_id', 'Backlog')]:
                val = own_meta.get(key)
                if val and val != inherited_meta.get(key):
                    parts.append(f"{label}: {val}")
            tag = f"{node_name} ({child_id})"
            if parts:
                tag += ' [' + '; '.join(parts) + ']'
            # Create node
            tree.create_node(tag=tag, identifier=child_id, parent=parent_id)
            # Prepare metadata for descendants
            new_meta = inherited_meta.copy()
            for key in ['lean_control_service_id', 'jira_backlog_id']:
                val = own_meta.get(key)
                if val:
                    new_meta[key] = val
            # Recurse
            add_nodes(child_id, new_meta)

    # Start recursion with empty inherited metadata
    add_nodes(root_id, {})

    # Display tree
    tree.show()

    # Capture ASCII for Markdown
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        tree.show()
    ascii_tree = buf.getvalue()

    # Write to Markdown
    with open(markdown_path, 'w') as f:
        f.write('```text\n')
        f.write(ascii_tree)
        f.write('\n```\n')
    print(f"Markdown hierarchy written to {markdown_path}")


def main():
    parser = argparse.ArgumentParser(description="Render hierarchy via treelib with inherited metadata suppression")
    parser.add_argument("--input", required=True, help="CSV file with id,parent,name,lean_control_service_id,jira_backlog_id columns")
    parser.add_argument("--output", default="tree.md", help="Output Markdown file path")
    args = parser.parse_args()
    render_tree(args.input, args.output)

if __name__ == '__main__':
    main()