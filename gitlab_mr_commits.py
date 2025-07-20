import requests
import argparse
import yaml
from pathlib import Path
import warnings
from textwrap import fill
from datetime import datetime

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
    config.setdefault('verify_ssl', True)

    return config

def get_latest_merged_mr(project_id, private_token, base_url='https://gitlab.com/api/v4', verify_ssl=True):
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

    if not verify_ssl:
        warnings.warn("SSL verification is disabled - this is not recommended for production use!")

    response = requests.get(url, params=params, headers=headers, verify=verify_ssl)
    response.raise_for_status()

    mrs = response.json()
    if not mrs:
        raise ValueError("No merged merge requests found for main branch")

    return mrs[0]

def get_commit_messages_from_mr(project_id, private_token, mr_iid, base_url='https://gitlab.com/api/v4', verify_ssl=True):
    """
    Get all commit messages from a merge request
    """
    url = f"{base_url}/projects/{project_id}/merge_requests/{mr_iid}/commits"
    headers = {'PRIVATE-TOKEN': private_token}

    response = requests.get(url, headers=headers, verify=verify_ssl)
    response.raise_for_status()

    commits = response.json()
    return [commit['message'] for commit in commits]

def format_timestamp(timestamp_str):
    """Format ISO timestamp to human-readable format"""
    if not timestamp_str:
        return "Unknown"
    dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def print_header(text, width=80, char='='):
    """Print a formatted header"""
    print(f"\n{char * width}")
    print(f"{text.center(width)}")
    print(f"{char * width}\n")

def print_section(title, content, indent=2):
    """Print a section with formatted content"""
    indent_str = ' ' * indent
    print(f"\n{title.upper()}:")
    if isinstance(content, list):
        for item in content:
            print(f"{indent_str}- {item}")
    else:
        print(f"{indent_str}{content}")

def format_commit_message(message, width=80, indent=4):
    """Format commit message with proper wrapping"""
    indent_str = ' ' * indent
    lines = message.split('\n')
    formatted_lines = []
    for line in lines:
        if line.strip():
            wrapped = fill(line, width=width-indent)
            formatted_lines.append(f"{indent_str}{wrapped}")
        else:
            formatted_lines.append("")
    return '\n'.join(formatted_lines)

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
            config['base_url'],
            config.get('verify_ssl', True)
        )

        # Get all commit messages from this MR
        commit_messages = get_commit_messages_from_mr(
            args.project_id,
            config['private_token'],
            latest_mr['iid'],
            config['base_url'],
            config.get('verify_ssl', True)
        )

        # Format and print the output
        print_header("LATEST MERGE REQUEST DETAILS")

        print_section("Project ID", args.project_id)
        print_section("Merge Request Title", latest_mr['title'])
        print_section("Merge Request IID", latest_mr['iid'])
        print_section("Merge Request URL", latest_mr['web_url'])
        print_section("Merged At", format_timestamp(latest_mr['merged_at']))
        print_section("Author", f"{latest_mr['author']['name']} ({latest_mr['author']['username']})")

        print_header("COMMIT MESSAGES", width=80, char='-')
        for i, message in enumerate(commit_messages, 1):
            print(f"\nCOMMIT #{i}:")
            print(format_commit_message(message))
            print("-" * 40)  # Separator between commits

    except Exception as e:
        print(f"\nERROR: {str(e)}")
        exit(1)

if __name__ == '__main__':
    main()