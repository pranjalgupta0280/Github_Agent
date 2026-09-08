import os
from src.state import AgentState
from src.github_utils import inspect_repository, apply_patch_to_file
from src.sandbox import run_tests_in_sandbox

def investigate_node(state: AgentState) -> AgentState:
    """
    Node 1: Scans repository file tree and populates target files in AgentState.
    """
    repo_info = inspect_repository(state["repo_path"])
    state["file_tree"] = repo_info["file_tree"]
    state["target_files"] = repo_info["files"]
    state["status"] = "executing"
    return state

def verify_tests_node(state: AgentState) -> AgentState:
    """
    Node 3: Runs sandbox unit tests against current repository state.
    """
    passed, logs = run_tests_in_sandbox(state["repo_path"])
    state["tests_passed"] = passed
    state["test_logs"] = logs
    
    if passed:
        state["status"] = "resolved"
    else:
        state["retry_count"] += 1
        if state["retry_count"] >= state["max_retries"]:
            state["status"] = "failed"
            state["error_message"] = f"Max retries ({state['max_retries']}) reached without passing tests."
        else:
            state["status"] = "executing"
            
    return state

def execute_patch_node(state: AgentState) -> AgentState:
    """
    Node 2: Generates patch/fix based on target files and error logs, then applies it.
    """
    # Simple deterministic rule-based fix for zero-division bug in calculator demo
    # (Can be extended with LLM prompt call when API key is present)
    for filename, content in state["target_files"].items():
        if "calculator.py" in filename and "def divide(" in content:
            fixed_content = """def add(a, b):
    return a + b

def divide(a, b):
    if b == 0:
        return None
    return a / b
"""
            apply_patch_to_file(state["repo_path"], filename, fixed_content)
            state["target_files"][filename] = fixed_content
            state["patch"] = f"Applied fix to {filename} for ZeroDivisionError"
            break
            
    state["status"] = "verifying"
    return state

def resolve_node(state: AgentState) -> AgentState:
    """
    Node 4: Finalizes resolution when tests pass.
    """
    if state["tests_passed"]:
        state["status"] = "resolved"
        state["branch_name"] = "fix/issue-auto-resolver"
    return state

