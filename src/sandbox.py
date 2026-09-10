import subprocess
import sys
import os
from typing import Tuple

def run_tests_in_sandbox(repo_path: str, test_cmd: str = None) -> Tuple[bool, str]:
    """
    Runs tests inside the given repo_path in an isolated process.
    Returns (success_boolean, combined_stdout_stderr_output).
    """
    abs_repo_path = os.path.abspath(repo_path)
    if not os.path.exists(abs_repo_path):
        return False, f"Repository path does not exist: {abs_repo_path}"
    
    if test_cmd is None:
        if os.path.exists(os.path.join(abs_repo_path, "package.json")):
            test_cmd = "npm test"
        else:
            test_cmd = f"{sys.executable} -m unittest discover"
        
    try:
        result = subprocess.run(
            test_cmd,
            shell=True,
            cwd=abs_repo_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=60
        )
        passed = (result.returncode == 0)
        return passed, result.stdout
    except subprocess.TimeoutExpired:
        return False, "Test execution timed out after 60 seconds."
    except Exception as e:
        return False, f"Failed to execute tests: {str(e)}"
