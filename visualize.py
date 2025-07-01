#!/usr/bin/env python3
import os
import sys
import json
import argparse
import re
from rich import print
from rich.tree import Tree
from rich.console import Console


def add_nodes(tree: Tree, apps: list, service_id=None, jira_backlog_id=None):
    for app in apps:
        sid  = app.get('lean_control_service_id', service_id)
        jira = app.get('jira_backlog_id', jira_backlog_id)
        aid  = app.get('app_id')

        # build node label
        label = f"{app['app_name']} (LCP {sid}, Jira {jira}, AppID {aid})"
        node = tree.add(label)

        for inst in app.get('service_instances', []):
            name = inst['it_service_instance']
            iid  = inst['instance_id']
            env  = inst['environment']
            ityp = inst['install_type']
            node.add(f"{name} ({iid}) · {env} · {ityp}")

        if app.get('children'):
            add_nodes(node, app['children'], service_id=sid, jira_backlog_id=jira)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Render JSON tree to console and write ASCII tree to MD file"
    )
    parser.add_argument(
        'input_file',
        help='Path to input JSON file'
    )
    args = parser.parse_args()

    # Load JSON
    with open(args.input_file, 'r') as f:
        data = json.load(f)

    # Build and print tree to console (with ANSI styling)
    console = Console()
    tree = Tree("Business App Hierarchy")
    add_nodes(tree, data)
    console.print(tree)

    # Capture tree output
    with console.capture() as capture:
        console.print(tree)
    tree_str = capture.get()

    # Strip ANSI escape sequences for clean ASCII
    clean_tree = re.sub(r'\x1b\[[0-9;]*m', '', tree_str)

    # Write ASCII tree into fenced code block in MD
    base = os.path.splitext(args.input_file)[0]
    md_path = f"{base}.md"
    with open(md_path, 'w') as md:
        md.write('```\n')
        md.write(clean_tree)
        md.write('```\n')

    print(f"Wrote Markdown to {md_path}")
