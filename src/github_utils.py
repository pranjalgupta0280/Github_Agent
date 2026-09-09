import os
import glob
from typing import List, Dict, Tuple
from github import Github

def fetch_github_issue(issue_url: str, token: str = None) -> Tuple[str, str, str]:
    """
    Parses GitHub issue URL and fetches (repo_full_name, title, body) using PyGithub.
    Example URL: https://github.com/owner/repo/issues/1
    """
    if not token:
        token = os.getenv("GITHUB_TOKEN")
        
    parts = issue_url.rstrip("/").split("/")
    if len(parts) < 7 or parts[-2] != "issues":
        raise ValueError(f"Invalid GitHub issue URL format: {issue_url}")
        
    owner, repo_name, issue_num = parts[-4], parts[-3], int(parts[-1])
    repo_full_name = f"{owner}/{repo_name}"
    
    g = Github(token) if token else Github()
    repo = g.get_repo(repo_full_name)
    issue = repo.get_issue(number=issue_num)
    
    return repo_full_name, issue.title, issue.body or ""

def create_pull_request(repo_path: str, branch_name: str, issue_title: str, token: str = None) -> str:
    """
    Simulates / triggers PR creation using GitHub PAT token.
    """
    return f"https://github.com/example/repo/pull/new/{branch_name}"

def inspect_repository(repo_path: str) -> Dict[str, any]:
    """
    Scans repository directory and returns list of source files and file tree.
    """
    abs_path = os.path.abspath(repo_path)
    if not os.path.exists(abs_path):
        return {"file_tree": [], "files": {}}

    file_tree = []
    files_content = {}
    ignore_dirs = {'.git', '__pycache__', '.pytest_cache', 'venv', '.venv', 'node_modules'}
    
    for root, dirs, files in os.walk(abs_path):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for file in files:
            if file.endswith(('.py', '.md', '.txt', '.json', '.yaml', '.yml')):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, abs_path)
                file_tree.append(rel_path)
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        files_content[rel_path] = f.read()
                except Exception:
                    pass

    return {
        "file_tree": sorted(file_tree),
        "files": files_content
    }

def apply_patch_to_file(repo_path: str, rel_filepath: str, new_content: str) -> bool:
    """
    Writes updated file content directly to target file inside the repository.
    """
    full_path = os.path.join(os.path.abspath(repo_path), rel_filepath)
    try:
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    except Exception as e:
        print(f"Error writing patch to {full_path}: {e}")
        return False
