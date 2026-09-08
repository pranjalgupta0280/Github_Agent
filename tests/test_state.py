import unittest
from src.state import AgentState

class TestAgentState(unittest.TestCase):
    def test_agent_state_initialization(self):
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
        
        self.assertEqual(state["issue_title"], "Fix division by zero bug")
        self.assertEqual(state["retry_count"], 0)
        self.assertFalse(state["tests_passed"])

if __name__ == '__main__':
    unittest.main()
