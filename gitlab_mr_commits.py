import requests
import argparse
import yaml
from pathlib import Path

def load_config(config_path='gitlab_config.yaml'):
    """
    Load configuration from YAML file
    """
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Config file {config_path} not found")

    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)

    required_keys = ['private_token']
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required config key: {key}")

    # Set defaults for optional keys
    config.setdefault('base_url', 'https://gitlab.com/api/v4')

    return config

def get_latest_merged_mr(project_id, private_token, base_url='https://gitlab.com/api/v4'):
    """
    Get the latest merge request merged into the main branch
    """
    url = f"{base_url}/projects/{project_id}/merge_requests"
    params = {
        'state': 'merged',
        'target_branch': 'main',
        'order_by': 'updated_at',
        'sort': 'desc',
        'per_page': 1
    }
    headers = {'PRIVATE-TOKEN': private_token}

    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()

    mrs = response.json()
    if not mrs:
        raise ValueError("No merged merge requests found for main branch")

    return mrs[0]

def get_commit_messages_from_mr(project_id, private_token, mr_iid, base_url='https://gitlab.com/api/v4'):
    """
    Get all commit messages from a merge request
    """
    url = f"{base_url}/projects/{project_id}/merge_requests/{mr_iid}/commits"
    headers = {'PRIVATE-TOKEN': private_token}

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    commits = response.json()
    return [commit['message'] for commit in commits]

def main():
    parser = argparse.ArgumentParser(description='Get commit messages from latest GitLab merge request')
    parser.add_argument('--project-id', required=True, help='GitLab project ID')
    parser.add_argument('--config', default='gitlab_config.yaml',
                        help='Path to YAML config file (default: gitlab_config.yaml)')

    args = parser.parse_args()

    try:
        # Load configuration from YAML file
        config = load_config(args.config)

        # Get the latest MR merged into main
        latest_mr = get_latest_merged_mr(
            args.project_id,
            config['private_token'],
            config['base_url']
        )

        mr_title = latest_mr['title']
        mr_iid = latest_mr['iid']
        merged_at = latest_mr['merged_at']

        print(f"Latest merge request merged into main:")
        print(f"Title: {mr_title}")
        print(f"IID: {mr_iid}")
        print(f"Merged at: {merged_at}")
        print("\nCommit messages:")

        # Get all commit messages from this MR
        commit_messages = get_commit_messages_from_mr(
            args.project_id,
            config['private_token'],
            mr_iid,
            config['base_url']
        )

        for i, message in enumerate(commit_messages, 1):
            print(f"\nCommit #{i}:")
            print(message)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()