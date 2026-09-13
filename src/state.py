from typing import TypedDict, Optional, Dict, List

class AgentState(TypedDict):
    issue_url: str
    issue_title: str
    issue_body: str
    repo_path: str
    repo_name: Optional[str]
    github_token: Optional[str]
    file_tree: List[str]
    target_files: Dict[str, str]
    patch: Optional[str]
    modified_files: Dict[str, str]
    test_logs: str
    tests_passed: bool
    retry_count: int
    max_retries: int
    status: str
    branch_name: Optional[str]
    pr_url: Optional[str]
    error_message: Optional[str]