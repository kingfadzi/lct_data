import streamlit as st

# Sample structured data
apps = [
    {
        "app_name": "User Management",
        "lean_control_service_id": "LCS-001",
        "jira_backlog_id": "JIRA-123",
        "service_name": "Customer Portal",
        "instances": [
            {
                "instance_name": "UM-Prod-01",
                "environment": "Production",
                "install_type": "Cloud",
                "children": [
                    {
                        "instance_name": "UM-Prod-01-A",
                        "environment": "Production",
                        "install_type": "Cloud",
                        "children": []
                    },
                    {
                        "instance_name": "UM-Prod-01-B",
                        "environment": "Production",
                        "install_type": "Cloud",
                        "children": []
                    }
                ]
            }
        ]
    },
    {
        "app_name": "Finance Core",
        "lean_control_service_id": "LCS-002",
        "jira_backlog_id": "JIRA-456",
        "service_name": "Billing Engine",
        "instances": [
            {
                "instance_name": "Billing-Stg-01",
                "environment": "Staging",
                "install_type": "On-Prem",
                "children": []
            }
        ]
    }
]

st.set_page_config(page_title="Recursive Tree View", layout="wide")
st.title("App-Centric Service Tree (Recursive Expandable View)")

# Recursive function to render tree
def render_instance_tree(instance, level=1):
    label = f"{'└── ' if level > 1 else ''}{instance['instance_name']} ({instance['environment']}, {instance['install_type']})"
    with st.expander(label):
        for child in instance.get("children", []):
            render_instance_tree(child, level + 1)

# Top-level loop
for app in apps:
    with st.expander(f"📦 {app['app_name']}  |  {app['service_name']}  |  {app['jira_backlog_id']}"):
        for inst in app["instances"]:
            render_instance_tree(inst)