from src.state import AgentState

def test_agent_state_initialization():
    state: AgentState = {
        "issue_url": "https://github.com/example/repo/issues/1",
        "issue_title": "Fix division by zero bug",
        "issue_body": "Calculator throws ZeroDivisionError on divide(10, 0)",
        "repo_path": "./example_repo",
        "file_tree": ["calculator.py", "test_calculator.py"],
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
    
    assert state["issue_title"] == "Fix division by zero bug"
    assert state["retry_count"] == 0
    assert state["tests_passed"] is False
