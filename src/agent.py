import os
import re
import time
from dotenv import load_dotenv
from google import genai

from src.state import AgentState
from src.github_utils import inspect_repository, apply_patch_to_file, create_pull_request
from src.sandbox import run_tests_in_sandbox

load_dotenv()


def investigate_node(state: AgentState) -> AgentState:
    """
    Node 1: Scans repository file tree and populates target files in AgentState.
    """
    repo_info = inspect_repository(state["repo_path"])
    state["file_tree"] = repo_info["file_tree"]
    state["target_files"] = repo_info["files"]
    state["status"] = "executing"
    return state


def execute_patch_node(state: AgentState) -> AgentState:
    """
    Node 2: Generates a targeted patch using Gemini and applies it.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        state["status"] = "failed"
        state["error_message"] = "Missing GEMINI_API_KEY environment variable."
        return state

    target_file = None
    target_content = ""

    title_words = [w.lower() for w in state.get("issue_title", "").replace(".", " ").replace("_", " ").split()]
    body_words = [w.lower() for w in state.get("issue_body", "").replace(".", " ").replace("_", " ").split()]

    # 1. Match basename stem in title
    for filename, content in state["target_files"].items():
        if any(skip in filename for skip in ["node_modules", "dist", ".git"]) or filename.startswith("test_") or filename.endswith(".test.js"):
            continue

        base_stem = os.path.basename(filename).lower()
        for ext in [".jsx", ".tsx", ".js", ".ts", ".py"]:
            if base_stem.endswith(ext):
                base_stem = base_stem[:-len(ext)]
                break

        if any(base_stem == word or base_stem in word for word in title_words):
            target_file = filename
            target_content = content
            break

    # 2. Match basename stem in issue body
    if not target_file:
        for filename, content in state["target_files"].items():
            if any(skip in filename for skip in ["node_modules", "dist", ".git"]) or filename.startswith("test_") or filename.endswith(".test.js"):
                continue
            base_stem = os.path.basename(filename).lower()
            if any(word in base_stem for word in body_words if len(word) > 3):
                target_file = filename
                target_content = content
                break

    # 3. Fallback: first non-test source file
    if not target_file:
        for filename, content in state["target_files"].items():
            if filename.endswith((".py", ".js", ".ts", ".jsx", ".tsx")):
                if not filename.startswith("test_") and not filename.endswith(".test.js") and not any(k in filename for k in ["node_modules", "dist", ".git"]):
                    target_file = filename
                    target_content = content
                    break

    if not target_file:
        state["status"] = "failed"
        state["error_message"] = "Could not identify an appropriate target file to modify."
        return state

    prompt = (
        f"You are an expert autonomous software engineer.\n"
        f"Fix the bug in the provided codebase file so all unit tests pass cleanly.\n\n"
        f"Issue Title: {state.get('issue_title', '')}\n"
        f"Issue Description: {state.get('issue_body', '')}\n\n"
        f"Test Failure Output / Errors:\n"
        f"{state.get('test_logs', '')}\n\n"
        f"Target File: {target_file}\n"
        f"Current File Content:\n"
        f"```\n{target_content}\n```\n\n"
        f"Instructions:\n"
        f"1. Return ONLY the complete updated source code for the file.\n"
        f"2. Wrap your code inside triple backtick code fences: ```python ... ``` (or matching language).\n"
        f"3. Do not include conversational explanations, notes, or introductions.\n"
    )

    fixed_code = None
    client = genai.Client(api_key=api_key)
    models_to_try = ["gemini-2.5-flash", "gemini-1.5-flash"]

    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            raw_text = response.text.strip() if response.text else ""

            match = re.search(r"```(?:[a-zA-Z0-9_\-]+)?\n(.*?)```", raw_text, re.DOTALL)
            if match:
                fixed_code = match.group(1).strip()
            else:
                fixed_code = raw_text

            if fixed_code:
                break
        except Exception as e:
            if "429" in str(e):
                time.sleep(5)
            print(f"[Warning] Model {model_name} invocation failed: {e}")

    if not fixed_code:
        state["status"] = "failed"
        state["error_message"] = "LLM failed to generate a patch for the target file."
        return state

    apply_patch_to_file(state["repo_path"], target_file, fixed_code)
    state["target_files"][target_file] = fixed_code

    if state.get("modified_files") is None:
        state["modified_files"] = {}
    state["modified_files"][target_file] = fixed_code
    state["patch"] = f"Applied patch to {target_file}"
    state["status"] = "verifying"

    return state


def verify_tests_node(state: AgentState) -> AgentState:
    """
    Node 3: Runs unit tests inside the sandbox environment.
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


def resolve_node(state: AgentState) -> AgentState:
    """
    Node 4: Pushes changes and creates a Pull Request when tests pass.
    """
    if state.get("tests_passed"):
        branch_name = f"fix/auto-resolver-{int(time.time())}"
        state["branch_name"] = branch_name

        try:
            pr_url = create_pull_request(
                issue_url=state["issue_url"],
                branch_name=branch_name,
                patch_summary=state.get("patch", "Automated patch applied to resolve issue."),
                token=state.get("github_token") or os.getenv("GITHUB_TOKEN")
            )
            state["pr_url"] = pr_url
            state["status"] = "resolved"
        except Exception as e:
            state["error_message"] = f"Tests passed, but failed to create PR: {str(e)}"
    return state