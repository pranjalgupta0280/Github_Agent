import unittest
import os
import shutil
import tempfile
from src.github_utils import inspect_repository, apply_patch_to_file

class TestGithubUtils(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_inspect_repository(self):
        file1 = os.path.join(self.test_dir, "main.py")
        with open(file1, "w") as f:
            f.write("print('hello')")
            
        res = inspect_repository(self.test_dir)
        self.assertIn("main.py", res["file_tree"])
        self.assertEqual(res["files"]["main.py"], "print('hello')")

    def test_apply_patch_to_file(self):
        success = apply_patch_to_file(self.test_dir, "calculator.py", "def add(a, b): return a + b")
        self.assertTrue(success)
        
        calc_path = os.path.join(self.test_dir, "calculator.py")
        with open(calc_path, "r") as f:
            content = f.read()
        self.assertEqual(content, "def add(a, b): return a + b")

if __name__ == '__main__':
    unittest.main()
