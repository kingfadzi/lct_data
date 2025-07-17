import requests
import csv
import yaml
import os
import sys
from datetime import datetime, timedelta
import urllib3

# --- Ignore self-signed cert warnings ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Load Config from YAML ---
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

JIRA_URL = config.get("jira_url", "").strip()
JIRA_PROJECT_KEYS = config.get("jira_project_keys")

if not JIRA_PROJECT_KEYS or not isinstance(JIRA_PROJECT_KEYS, list):
    print("Error: jira_project_keys must be a non-empty list in config.yaml")
    sys.exit(1)

JIRA_API_TOKEN = os.getenv("JIRA_TOKEN")
if not JIRA_API_TOKEN:
    print("Error: JIRA_TOKEN environment variable is not set.")
    sys.exit(1)

headers = {
    "Authorization": f"Bearer {JIRA_API_TOKEN}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

for project_key in JIRA_PROJECT_KEYS:
    project_key = project_key.strip()

    # Calculate date range for the last 12 months
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    # JQL query
    jql = (
        f"project = {project_key} "
        f"AND statusCategory != Done "
        f"AND created >= \"{start_date_str}\" "
        f"AND created <= \"{end_date_str}\" "
        f"ORDER BY created DESC"
    )

    params = {
        "jql": jql,
        "startAt": 0,
        "maxResults": 50,
        "fields": "key,summary,description,status,assignee,reporter,created,updated,priority,issuetype,labels"
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
            "Key", "Summary", "Description", "Status", "Assignee", "Reporter",
            "Created", "Updated", "Priority", "Issue Type", "Labels"
        ])
        for issue in all_issues:
            fields = issue["fields"]
            description = fields.get("description", "")
            if isinstance(description, dict):
                description = description.get("content", "")  # Some Jira servers return rich text structure
            elif description is None:
                description = ""
            writer.writerow([
                issue["key"],
                fields.get("summary", ""),
                description,
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
