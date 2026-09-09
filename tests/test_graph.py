import unittest
import os
import shutil
import tempfile
from src.state import AgentState
from src.graph import build_issue_resolver_graph

class TestGraphWorkflow(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        
        # Setup buggy calculator repository
        calc_path = os.path.join(self.test_dir, "calculator.py")
        with open(calc_path, "w") as f:
            f.write("""def add(a, b):
    return a + b

def divide(a, b):
    return a / b
""")

        test_path = os.path.join(self.test_dir, "test_calculator.py")
        with open(test_path, "w") as f:
            f.write("""import unittest
from calculator import divide

class TestCalc(unittest.TestCase):
    def test_divide_zero(self):
        self.assertIsNone(divide(10, 0))

if __name__ == '__main__':
    unittest.main()
""")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_full_graph_execution(self):
        app = build_issue_resolver_graph()
        
        initial_state: AgentState = {
            "issue_url": "https://github.com/example/repo/issues/101",
            "issue_title": "Fix division by zero in calculator",
            "issue_body": "divide(10, 0) throws ZeroDivisionError instead of returning None",
            "repo_path": self.test_dir,
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
        
        final_state = app.invoke(initial_state)
        
        self.assertTrue(final_state["tests_passed"])
        self.assertEqual(final_state["status"], "resolved")
        self.assertEqual(final_state["branch_name"], "fix/issue-auto-resolver")

if __name__ == '__main__':
    unittest.main()
