#!/usr/bin/env python3
import sys, json
from rich import print
from rich.tree import Tree

def add_nodes(tree: Tree, apps: list, service_id=None):
    for app in apps:
        # use the app’s own service_id if it has one, otherwise inherit
        sid = app.get('lean_control_service_id', service_id)
        node = tree.add(f"[bold]{app['app_name']}[/bold] (LCP ID={sid})")
        # show service instances
        for inst in app.get('service_instances', []):
            node.add(f"{inst['it_service_instance']} · {inst['environment']} · {inst['install_type']}")
        # recurse into children, passing down sid
        if app.get('children'):
            add_nodes(node, app['children'], service_id=sid)

if __name__ == "__main__":
    data = json.load(sys.stdin)
    tree = Tree("Business App Hierarchy")
    add_nodes(tree, data)
    print(tree)