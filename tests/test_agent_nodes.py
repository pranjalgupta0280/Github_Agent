import unittest
import os
import shutil
import tempfile
from src.state import AgentState
from src.agent import investigate_node, verify_tests_node, resolve_node

class TestAgentNodes(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_investigate_node(self):
        with open(os.path.join(self.test_dir, "app.py"), "w") as f:
            f.write("print('hello')")
            
        state: AgentState = {
            "issue_url": None,
            "issue_title": "Test Issue",
            "issue_body": "Sample body",
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
        
        updated_state = investigate_node(state)
        self.assertEqual(updated_state["file_tree"], ["app.py"])
        self.assertEqual(updated_state["status"], "executing")

    def test_verify_tests_node_pass(self):
        test_file = os.path.join(self.test_dir, "test_pass.py")
        with open(test_file, "w") as f:
            f.write("""import unittest
class TestPass(unittest.TestCase):
    def test_ok(self):
        self.assertTrue(True)
""")
            
        state: AgentState = {
            "repo_path": self.test_dir,
            "tests_passed": False,
            "test_logs": "",
            "retry_count": 0,
            "max_retries": 3,
            "status": "verifying"
        }
        
        updated_state = verify_tests_node(state)
        self.assertTrue(updated_state["tests_passed"])
        self.assertEqual(updated_state["status"], "resolved")

if __name__ == '__main__':
    unittest.main()
