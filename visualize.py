#!/usr/bin/env python3
import os
import sys
import json
import argparse
import re
from rich import print
from rich.tree import Tree
from rich.console import Console

# ——— Visualization Helpers ———

def add_service_nodes(tree: Tree, services: list):
    """
    Add business services, their apps, and instances as nodes in the tree.
    """
    for svc in services:
        svc_name = svc.get('it_business_service')
        lean = svc.get('lean_control_service_id')
        jira = svc.get('jira_backlog_id')
        svc_label = f"[bold]Service[/bold] {svc_name} (LCP {lean}, Jira {jira})"
        svc_node = tree.add(svc_label)

        for app in svc.get('apps', []):
            app_id = app.get('app_id')
            app_name = app.get('app_name')
            app_node = svc_node.add(f"[bold]{app_name}[/bold] (AppID {app_id})")

            # Service instances for this app
            for inst in app.get('service_instances', []):
                name = inst['it_service_instance']
                iid = inst['instance_id']
                env = inst['environment']
                ityp = inst['install_type']
                app_node.add(f"{name} ({iid}) · {env} · {ityp}")

            # Child apps under this app
            for child in app.get('children', []):
                child_id = child.get('app_id')
                child_name = child.get('app_name')
                child_node = app_node.add(f"[bold]{child_name}[/bold] (AppID {child_id})")

                for inst in child.get('service_instances', []):
                    name = inst['it_service_instance']
                    iid = inst['instance_id']
                    env = inst['environment']
                    ityp = inst['install_type']
                    child_node.add(f"{name} ({iid}) · {env} · {ityp}")

# ——— Main ———

def main():
    parser = argparse.ArgumentParser(
        description="Visualize JSON hierarchy of services → apps → instances"
    )
    parser.add_argument(
        'input_file',
        help='Path to the JSON file containing the service/app/instance hierarchy'
    )
    args = parser.parse_args()

    # Load JSON data
    with open(args.input_file, 'r') as f:
        services = json.load(f)

    # Build tree
    tree = Tree("Business Services Hierarchy")
    add_service_nodes(tree, services)

    # Print to console
    console = Console()
    console.print(tree)

    # Capture tree output including ANSI
    with console.capture() as capture:
        console.print(tree)
    tree_str = capture.get()

    # Strip ANSI escape sequences
    clean_tree = re.sub(r'\x1b\[[0-9;]*m', '', tree_str)

    # Write to markdown file
    base = os.path.splitext(args.input_file)[0]
    md_path = f"{base}.md"
    with open(md_path, 'w') as md:
        md.write('```text\n')
        md.write(clean_tree)
        md.write('```\n')

    print(f"Wrote Markdown to {md_path}")

if __name__ == "__main__":
    main()