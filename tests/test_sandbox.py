import unittest
import os
import shutil
import tempfile
from src.sandbox import run_tests_in_sandbox

class TestSandbox(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_sandbox_passing_test(self):
        test_file = os.path.join(self.test_dir, "test_sample.py")
        with open(test_file, "w") as f:
            f.write("""import unittest
class SampleTest(unittest.TestCase):
    def test_pass(self):
        self.assertTrue(True)
""")
        passed, log = run_tests_in_sandbox(self.test_dir)
        self.assertTrue(passed)
        self.assertIn("OK", log)

    def test_sandbox_failing_test(self):
        test_file = os.path.join(self.test_dir, "test_sample.py")
        with open(test_file, "w") as f:
            f.write("""import unittest
class SampleTest(unittest.TestCase):
    def test_fail(self):
        self.assertTrue(False)
""")
        passed, log = run_tests_in_sandbox(self.test_dir)
        self.assertFalse(passed)
        self.assertIn("FAIL", log)

if __name__ == '__main__':
    unittest.main()
