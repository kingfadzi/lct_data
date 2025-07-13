import requests
import csv
import yaml
import os
import sys

# --- Load Config from YAML ---
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

JIRA_URL = config.get("jira_url")
JIRA_PROJECT_KEYS = config.get("jira_project_keys")

if not JIRA_PROJECT_KEYS or not isinstance(JIRA_PROJECT_KEYS, list):
    print("Error: jira_project_keys must be a non-empty list in config.yaml")
    sys.exit(1)

JIRA_API_TOKEN = os.getenv("JIRA_TOKEN")
if not JIRA_API_TOKEN:
    print("Error: JIRA_TOKEN environment variable is not set.")
    sys.exit(1)

headers = {
    "Authorization": JIRA_API_TOKEN,
    "Accept": "application/json",
    "Content-Type": "application/json"
}

for project_key in JIRA_PROJECT_KEYS:
    jql = f"project = {project_key} AND statusCategory != Done ORDER BY created DESC"
    params = {
        "jql": jql,
        "startAt": 0,
        "maxResults": 50,
        "fields": "key,summary,status,assignee,reporter,created,updated,priority,issuetype,labels"
    }
    all_issues = []
    while True:
        response = requests.get(f"{JIRA_URL}/rest/api/2/search", headers=headers, params=params, verify=False)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch issues for {project_key}: {response.status_code} {response.text}")
        data = response.json()
        issues = data.get("issues", [])
        all_issues.extend(issues)
        if params["startAt"] + params["maxResults"] >= data["total"]:
            break
        params["startAt"] += params["maxResults"]

    csv_file = f"../jira_open_issues_{project_key}.csv"
    with open(csv_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Key", "Summary", "Status", "Assignee", "Reporter",
            "Created", "Updated", "Priority", "Issue Type", "Labels"
        ])
        for issue in all_issues:
            fields = issue["fields"]
            writer.writerow([
                issue["key"],
                fields.get("summary", ""),
                fields.get("status", {}).get("name", ""),
                fields.get("assignee", {}).get("displayName", "") if fields.get("assignee") else "",
                fields.get("reporter", {}).get("displayName", "") if fields.get("reporter") else "",
                fields.get("created", ""),
                fields.get("updated", ""),
                fields.get("priority", {}).get("name", "") if fields.get("priority") else "",
                fields.get("issuetype", {}).get("name", ""),
                ", ".join(fields.get("labels", []))
            ])
    print(f"✅ Exported {len(all_issues)} issues to {csv_file}")
