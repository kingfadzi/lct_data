# Script 2: treelib_render.py
# Reads CSV, builds hierarchy using treelib with recursive insertion,
# and writes a Markdown representation of the tree to a .md file,
# including key metadata.

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


def build_children_map(df):
    children = {}
    for row in df.itertuples():
        pid = row.parent if pd.notna(row.parent) else 'Business Services'
        children.setdefault(pid, []).append(row.id)
    return children


def build_meta_map(df):
    meta = {}
    for row in df.itertuples():
        meta[row.id] = {tag: getattr(row, col) for col, tag in METADATA_FIELDS if pd.notna(getattr(row, col))}
        # include name separately
        meta[row.id]['name'] = row.name
    return meta


def add_nodes_recursively(tree, children_map, meta_map, parent_id):
    for child_id in children_map.get(parent_id, []):
        m = meta_map.get(child_id, {})
        name = m.get('name', child_id)
        tag = name  # plain tag; full label constructed in render
        tree.create_node(tag=tag, identifier=child_id, parent=parent_id, data=m)
        add_nodes_recursively(tree, children_map, meta_map, child_id)


def build_tree(df):
    tree = Tree()
    # synthetic root
    root_id = 'Business Services'
    tree.create_node(tag=root_id, identifier=root_id, data={})
    children_map = build_children_map(df)
    meta_map = build_meta_map(df)
    # recursively add all nodes
    add_nodes_recursively(tree, children_map, meta_map, root_id)
    return tree


def render_markdown(tree, out_file):
    lines = []

    def recurse(node_id, prefix, is_last):
        node = tree.get_node(node_id)
        branch = '└── ' if is_last else '├── '
        line = prefix + (branch if prefix else '')
        # Tag render with metadata
        if node_id == tree.root:
            label = node.tag
        else:
            m = node.data or {}
            # Determine type
            if not tree.children(node_id):
                ent_type = 'Service_Instance'
                keys = ['Instance', 'InstID', 'Env', 'Type']
            elif tree.parent(node_id).identifier == tree.root:
                ent_type = 'Business_Service'
                keys = ['LCP', 'Backlog', 'Service']
            else:
                ent_type = 'App'
                keys = ['AppID', 'AppName', 'LCP', 'Backlog']
            base = f"{ent_type}: {node.tag}({node_id})"
            parts = []
            if ent_type == 'App':
                parts.append(f"AppID: {node_id}")
                parts.append(f"AppName: {node.tag}")
            for key in keys:
                if key in m:
                    parts.append(f"{key}: {m[key]}")
            label = base + (' [' + '; '.join(parts) + ']' if parts else '')
        lines.append(line + label)
        children = tree.children(node_id)
        for idx, c in enumerate(children):
            new_prefix = prefix + ('    ' if is_last else '│   ')
            recurse(c.identifier, new_prefix, idx == len(children)-1)

    recurse(tree.root, '', True)
    with open(out_file, 'w') as f:
        f.write('```text\n')
        f.write('\n'.join(lines))
        f.write('\n```\n')
    print(f"[treelib_render] Markdown tree written to {out_file}")


def main():
    parser = argparse.ArgumentParser(description="Render tree from CSV via treelib")
    parser.add_argument("--input", default="tree_edges.csv", help="CSV from generate_dataset.py")
    parser.add_argument("--output", default="tree.md", help="Output Markdown file")
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    tree = build_tree(df)
    render_markdown(tree, args.output)

if __name__ == '__main__':
    main()