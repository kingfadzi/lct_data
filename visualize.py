#!/usr/bin/env python3
import os
import sys
import json
import argparse
from rich import print
from rich.tree import Tree
from rich.console import Console


def add_nodes(tree: Tree, apps: list, service_id=None, jira_backlog_id=None):
    for app in apps:
        sid  = app.get('lean_control_service_id', service_id)
        jira = app.get('jira_backlog_id', jira_backlog_id)
        aid  = app.get('app_id')

        node = tree.add(
            f"[bold]{app['app_name']}[/bold] "
            f"(LCP `{sid}`, Jira `{jira}`, AppID `{aid}`)"
        )

        for inst in app.get('service_instances', []):
            name = inst['it_service_instance']
            iid  = inst['instance_id']
            env  = inst['environment']
            ityp = inst['install_type']
            node.add(f"{name} (`{iid}`) · {env} · {ityp}")

        if app.get('children'):
            add_nodes(node, app['children'], service_id=sid, jira_backlog_id=jira)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Render JSON tree to console and write to MD file"
    )
    parser.add_argument(
        'input_file',
        help='Path to input JSON file'
    )
    args = parser.parse_args()

    # Load JSON
    with open(args.input_file, 'r') as f:
        data = json.load(f)

    # Build tree
    tree = Tree("Business App Hierarchy")
    add_nodes(tree, data)

    # Print to console
    console = Console()
    console.print(tree)

    # Capture tree output as text
    with console.capture() as capture:
        console.print(tree)
    tree_str = capture.get()

    # Write to markdown file
    base = os.path.splitext(args.input_file)[0]
    md_path = f"{base}.md"
    with open(md_path, 'w') as md:
        md.write('```text\n')
        md.write(tree_str)
        md.write('```\n')

    print(f"Wrote Markdown to {md_path}")
