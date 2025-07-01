#!/usr/bin/env python3
import sys, json
from rich import print
from rich.tree import Tree

def add_nodes(tree: Tree, apps: list, service_id=None, jira_backlog_id=None):
    for app in apps:
        # carry down the LCP ID and Jira ID
        sid  = app.get('lean_control_service_id', service_id)
        jira = app.get('jira_backlog_id', jira_backlog_id)
        aid  = app.get('app_id')

        # show app node with all three IDs
        node = tree.add(
            f"[bold]{app['app_name']}[/bold] "
            f"(LCP `{sid}`, Jira `{jira}`, AppID `{aid}`)"
        )

        # list each service instance, surfacing id in parentheses
        for inst in app.get('service_instances', []):
            name = inst['it_service_instance']
            iid  = inst['instance_id']
            env  = inst['environment']
            ityp = inst['install_type']
            node.add(f"{name} (`{iid}`) · {env} · {ityp}")

        # recurse into children
        if app.get('children'):
            add_nodes(node, app['children'], service_id=sid, jira_backlog_id=jira)

if __name__ == "__main__":
    data = json.load(sys.stdin)
    tree = Tree("Business App Hierarchy")
    add_nodes(tree, data)
    print(tree)