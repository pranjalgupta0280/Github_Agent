from typing import TypedDict, List, Dict, Optional, Any

class AgentState(TypedDict):
    """
    State tracking object for the LangGraph Smart GitHub Issue Resolver graph.
    """
    # Issue metadata
    issue_url: Optional[str]
    issue_title: str
    issue_body: str
    
    # Workspace details
    repo_path: str
    file_tree: List[str]
    target_files: Dict[str, str]  # filepath -> content
    
    # Execution & Verification state
    patch: Optional[str]           # Generated patch/diff or code changes
    modified_files: Dict[str, str] # filepath -> updated content
    test_logs: str                 # Captured stdout/stderr from pytest/unittest
    tests_passed: bool
    retry_count: int
    max_retries: int
    
    # Final status
    status: str                    # 'investigating', 'executing', 'verifying', 'resolved', 'failed'
    branch_name: Optional[str]
    pr_url: Optional[str]
    error_message: Optional[str]
