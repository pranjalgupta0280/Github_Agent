import os
import sys
from src.state import AgentState
from src.graph import build_issue_resolver_graph

def main():
    repo_path = os.path.abspath("./example_repo")
    print(f"🚀 Starting Smart GitHub Issue Resolver on target repo: {repo_path}\n")

    initial_state: AgentState = {
        "issue_url": "https://github.com/example/demo/issues/1",
        "issue_title": "Fix division by zero bug in calculator.py",
        "issue_body": "divide(10, 0) raises ZeroDivisionError, expected to return None safely.",
        "repo_path": repo_path,
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
    
    print("🔄 Running LangGraph State Machine...")
    final_state = app.invoke(initial_state)

    print("\n" + "="*50)
    print("📊 FINAL RESOLUTION SUMMARY")
    print("="*50)
    print(f"Status:       {final_state['status'].upper()}")
    print(f"Tests Passed: {final_state['tests_passed']}")
    print(f"Branch Name:  {final_state.get('branch_name')}")
    print(f"Patch Info:   {final_state.get('patch')}")
    print("="*50)

if __name__ == "__main__":
    main()
