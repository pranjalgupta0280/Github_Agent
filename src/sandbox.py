import os
import sys
import subprocess
from typing import Tuple

def run_tests_in_sandbox(repo_path: str, test_cmd: str = None) -> Tuple[bool, str]:
    """
    Runs tests inside the repo_path in an isolated non-interactive process.
    Returns (success_boolean, combined_stdout_stderr_output).
    """
    abs_repo_path = os.path.abspath(repo_path)
    if not os.path.exists(abs_repo_path):
        return False, f"Repository path does not exist: {abs_repo_path}"

    custom_env = os.environ.copy()
    custom_env["CI"] = "true"  # Force Jest, Vitest, and npm to run non-interactively

    if test_cmd is None:
        pkg_json_dir = None
        for root, dirs, files in os.walk(abs_repo_path):
            # Prune directories in-place to prevent recursive walk into build outputs
            dirs[:] = [d for d in dirs if d not in ("node_modules", ".git", "dist", "build")]
            if "package.json" in files:
                pkg_json_dir = root
                break

        if pkg_json_dir:
            abs_repo_path = pkg_json_dir
            # Force Jest/npm to exit after a single test run without watch prompt
            test_cmd = "npm test -- --watchAll=false --passWithNoTests"
        else:
            # Detect whether the Python project uses pytest or standard unittest
            has_pytest = any(
                os.path.exists(os.path.join(abs_repo_path, config))
                for config in ["pytest.ini", "setup.cfg", "conftest.py", "pyproject.toml"]
            )
            if has_pytest:
                test_cmd = f"{sys.executable} -m pytest"
            else:
                test_cmd = f"{sys.executable} -m unittest discover"

    try:
        result = subprocess.run(
            test_cmd,
            shell=True,
            cwd=abs_repo_path,
            env=custom_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=120
        )
        passed = (result.returncode == 0)
        return passed, result.stdout
    except subprocess.TimeoutExpired:
        return False, "Test execution timed out after 120 seconds."
    except Exception as e:
        return False, f"Failed to execute tests: {str(e)}"