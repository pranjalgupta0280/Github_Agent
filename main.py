import warnings
warnings.filterwarnings("ignore")
import os
import sys
from src.state import AgentState
from src.graph import build_issue_resolver_graph

from src.github_utils import fetch_github_issue

def resolve_github_issue(issue_url: str, local_repo_path: str, fallback_title: str = None, fallback_body: str = None):
    print(f"\n[GitHub] Fetching issue from GitHub: {issue_url}")
    try:
        repo_name, title, body = fetch_github_issue(issue_url)
    except Exception as e:
        print(f"[Warning] Remote fetch failed ({e}). Using local fallback issue parameters.")
        title = fallback_title or "Fix division by zero bug in calculator.py"
        body = fallback_body or "divide(10, 0) raises ZeroDivisionError, expected to return None safely."

    abs_repo_path = os.path.abspath(local_repo_path)
    print(f"[Target Repo] Local Path: {abs_repo_path}")
    print(f"[Issue Title] {title}")

    initial_state: AgentState = {
        "issue_url": issue_url,
        "issue_title": title,
        "issue_body": body,
        "repo_path": abs_repo_path,
        "file_tree": [],
        "target_files": {},
        "patch": None,
        "modified_files": {},
        "test_logs": "",
        "tests_passed": False,
        "retry_count": 0,
        "max_retries": 3,
        "status": "investigating",
        "branch_name": None,
        "pr_url": None,
        "error_message": None
    }

    app = build_issue_resolver_graph()
    final_state = app.invoke(initial_state)

    print("="*50)
    print(f"Repo Path:    {abs_repo_path}")
    print(f"Status:       {final_state['status'].upper()}")
    print(f"Tests Passed: {final_state['tests_passed']}")
    print(f"Patch Info:   {final_state.get('patch')}")
    print("="*50)
    return final_state

def main():
    issues_to_resolve = [
        {
            "issue_url": "https://github.com/pranjalgupta0280/Uber/issues/1",
            "local_repo_path": r"C:\node\Uber2",
        }
    ]

    for item in issues_to_resolve:
        resolve_github_issue(
            item["issue_url"],
            item["local_repo_path"],
            item.get("fallback_title"),
            item.get("fallback_body")
        )


if __name__ == "__main__":
    main()

