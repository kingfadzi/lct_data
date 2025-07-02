# Script 2: anytree_render.py
# This script reads the CSV produced above, builds the hierarchy using anytree,
# and writes a Markdown representation of the tree to a .md file,
# labeling nodes by entity type and including key metadata.

#!/usr/bin/env python3
import argparse
import pandas as pd
from anytree import Node, RenderTree


def build_anytree(df):
    # Build parent -> children mapping
    children = {}
    for row in df.itertuples():
        children.setdefault(row.parent, []).append(row.id)

    # Collect metadata rows, deduplicated by id
    meta_df = df.drop_duplicates(subset=['id'], keep='first').set_index('id')
    meta = meta_df.to_dict('index')

    # Create Node objects with placeholder names
    nodes = {node_id: Node(meta[node_id]['name'], id=node_id) for node_id in meta}

    # Attach parent-child relationships
    for node_id, node in nodes.items():
        parent_id = df.loc[df['id'] == node_id, 'parent'].iloc[0]
        if pd.notna(parent_id) and parent_id in nodes:
            node.parent = nodes[parent_id]

    # Return root nodes
    return nodes, meta, [node for node in nodes.values() if node.is_root]


def render_to_md(nodes, meta, roots, out_file):
    lines = []
    for root in roots:
        for prefix, _, node in RenderTree(root):
            # Determine entity type label prefix
            if node.is_root:
                ent_label = node.name
            else:
                parent = node.parent
                if parent.is_root:
                    ent_type = 'Business_Service'
                elif node.children:
                    ent_type = 'App'
                else:
                    ent_type = 'Service_Instance'
                ent_label = f"{ent_type}: {node.name}({node.id})"

                # Append metadata
                m = meta.get(node.id, {})
                parts = []
                for col, tag in [
                    ('lean_control_service_id', 'LCP'),
                    ('jira_backlog_id', 'Backlog'),
                    ('it_business_service', 'Service'),
                    ('it_service_instance', 'Instance'),
                    ('environment', 'Env'),
                    ('install_type', 'Type'),
                ]:
                    val = m.get(col)
                    if pd.notna(val):
                        parts.append(f"{tag}: {val}")
                if parts:
                    ent_label += ' [' + '; '.join(parts) + ']'

            lines.append(f"{prefix}{ent_label}")

    # Wrap the tree in a fenced code block for Markdown
    with open(out_file, 'w') as f:
        f.write("```text\n")
        f.write("\n".join(lines))
        f.write("\n```\n")
    print(f"[anytree_render] Markdown tree written to {out_file}")


def main():
    parser = argparse.ArgumentParser(description="Render tree from CSV via anytree")
    parser.add_argument("--input", default="tree_edges.csv",
                        help="Input CSV file path from generate_dataset.py")
    parser.add_argument("--output", default="tree.md",
                        help="Output Markdown file path")
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    nodes, meta, roots = build_anytree(df)
    render_to_md(nodes, meta, roots, args.output)

if __name__ == '__main__':
    main()
