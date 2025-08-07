import requests
import yaml
import os
import sys
import urllib3
import argparse

# --- Ignore self-signed cert warnings ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Load Config from YAML ---
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

JIRA_URL = config.get("jira_url", "").strip()
DEFAULT_PROJECT_KEY = config.get("jira_project_key", "").strip()

JIRA_API_TOKEN = os.getenv("JIRA_TOKEN")
if not JIRA_API_TOKEN:
    print("Error: JIRA_TOKEN environment variable is not set.")
    sys.exit(1)

headers = {
    "Authorization": f"Bearer {JIRA_API_TOKEN}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# --- CLI Argument Parsing ---
parser = argparse.ArgumentParser(description="Fetch Git repositories linked to a Jira Fix Version")
parser.add_argument("--fix-version", required=True, help="Name of the Jira Fix Version (e.g. 'Payments v1.4')")
parser.add_argument("--project", default=DEFAULT_PROJECT_KEY, help="Jira project key (default from config.yaml)")
parser.add_argument("--application-type", default="gitlab", choices=["gitlab", "bitbucket"], help="Source control type")

args = parser.parse_args()
FIX_VERSION = args.fix_version.strip()
PROJECT_KEY = args.project.strip()
APPLICATION_TYPE = args.application_type.strip()


def get_issues_for_fix_version(project_key, fix_version):
    jql = f'project="{project_key}" AND fixVersion="{fix_version}"'
    issues = []
    start_at = 0
    max_results = 50

    while True:
        params = {
            "jql": jql,
            "startAt": start_at,
            "maxResults": max_results,
            "fields": "summary"
        }
        response = requests.get(f"{JIRA_URL}/rest/api/2/search", headers=headers, params=params, verify=False)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch issues: {response.status_code} {response.text}")
        data = response.json()
        issues.extend(data.get("issues", []))
        if start_at + max_results >= data.get("total", 0):
            break
        start_at += max_results

    return issues


def get_repos_from_issue(issue_id):
    KNOWN_APPLICATION_TYPES = ["gitlab", "bitbucket", "stash", "github"]
    repos = set()

    for app_type in KNOWN_APPLICATION_TYPES:
        url = f"{JIRA_URL}/rest/dev-status/1.0/issue/detail"
        params = {
            "issueId": issue_id,
            "applicationType": app_type,
            "dataType": "repository"
        }

        print(f"   🐛 DEBUG: Trying dev-status with applicationType='{app_type}'")

        response = requests.get(url, headers=headers, params=params, verify=False)

        if response.status_code == 404:
            continue  # Try next app type

        if response.status_code != 200:
            print(f"   ❌ {app_type}: Failed ({response.status_code}): {response.text}")
            continue

        try:
            data = response.json()
        except Exception as e:
            print(f"   ❌ Failed to parse JSON: {e}")
            continue

        if not data.get("detail"):
            continue  # No data, try next

        print(f"   ✅ Found data using applicationType='{app_type}'")
        print(json.dumps(data, indent=2))

        for detail in data["detail"]:
            for repo_entry in detail.get("repositories", []):
                name = repo_entry.get("name")
                if not name and repo_entry.get("url"):
                    name = repo_entry["url"].split("/")[-1].replace(".git", "")
                if name:
                    repos.add(name)

        if repos:
            break  # Exit after finding first successful result

    return repos



def main():
    print(f"🔍 Fetching issues for Fix Version: '{FIX_VERSION}' in project '{PROJECT_KEY}'...")
    issues = get_issues_for_fix_version(PROJECT_KEY, FIX_VERSION)
    print(f"Found {len(issues)} issues.")

    all_repos = set()

    for issue in issues:
        issue_key = issue["key"]
        issue_id = issue["id"]
        print(f"→ Checking linked repositories for {issue_key}...")
        repos = get_repos_from_issue(issue_id)
        if repos:
            print(f"   🔗 Found: {sorted(repos)}")
            all_repos.update(repos)
        else:
            print("   ⚠️  No repositories linked.")

    print("\n📦 Unique Repositories involved in Fix Version:")
    for repo in sorted(all_repos):
        print(f" - {repo}")

    print(f"\n✅ Done. {len(all_repos)} unique repositories found.")


if __name__ == "__main__":
    main()
