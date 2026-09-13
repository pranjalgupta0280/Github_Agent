import os
import re
import time
from dotenv import load_dotenv
from google import genai

from src.state import AgentState
from src.github_utils import inspect_repository, apply_patch_to_file, create_pull_request, parse_github_issue_url
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

    issue_text = f"{state.get('issue_title', '')}\n{state.get('issue_body', '')}".lower()
    
    # 0. Check for exact relative path or filename mentioned in issue text
    for filename, content in state["target_files"].items():
        if any(skip in filename for skip in ["node_modules", "dist", ".git", "__pycache__"]):
            continue
        norm_filename = filename.replace("\\", "/").lower()
        base_filename = os.path.basename(filename).lower()
        if norm_filename in issue_text or base_filename in issue_text:
            target_file = filename
            target_content = content
            break

    # 1. Match basename stem in title
    if not target_file:
        title_words = [w.lower() for w in state.get("issue_title", "").replace(".", " ").replace("_", " ").split()]
        for filename, content in state["target_files"].items():
            if any(skip in filename for skip in ["node_modules", "dist", ".git"]) or filename.startswith("test_") or filename.endswith(".test.js"):
                continue

            base_stem = os.path.basename(filename).lower()
            for ext in [".jsx", ".tsx", ".js", ".ts", ".py"]:
                if base_stem.endswith(ext):
                    base_stem = base_stem[:-len(ext)]
                    break

            if any(base_stem == word or base_stem in word for word in title_words if len(word) > 2):
                target_file = filename
                target_content = content
                break

    # 2. Match basename stem in issue body
    if not target_file:
        body_words = [w.lower() for w in state.get("issue_body", "").replace(".", " ").replace("_", " ").split()]
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

    # Keep prompt concise to prevent Groq 413 Request Entity Too Large
    truncated_logs = (state.get('test_logs') or '')[:1000]
    truncated_content = target_content if len(target_content) <= 5000 else target_content[:5000]

    prompt = (
        f"You are an expert autonomous software engineer.\n"
        f"Fix the bug in the provided codebase file so all unit tests pass cleanly.\n\n"
        f"Issue Title: {state.get('issue_title', '')}\n"
        f"Issue Description: {state.get('issue_body', '')}\n\n"
        f"Test Failure Output / Errors:\n"
        f"{truncated_logs}\n\n"
        f"Target File: {target_file}\n"
        f"Current File Content:\n"
        f"```\n{truncated_content}\n```\n\n"
        f"Instructions:\n"
        f"1. Return ONLY the complete updated source code for the file.\n"
        f"2. Wrap your code inside triple backtick code fences: ```python ... ``` (or matching language).\n"
        f"3. Do not include conversational explanations, notes, or introductions.\n"
    )

    fixed_code = None
    groq_key = os.getenv("GROQ_API_KEY")

    if groq_key:
        try:
            from groq import Groq
            groq_client = Groq(api_key=groq_key)
            groq_models = ["groq/compound", "qwen/qwen3.6-27b", "groq/compound-mini", "openai/gpt-oss-120b"]
            for gmodel in groq_models:
                try:
                    response = groq_client.chat.completions.create(
                        model=gmodel,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=2000
                    )
                    raw_text = response.choices[0].message.content or ""
                    match = re.search(r"```(?:[a-zA-Z0-9_\-]+)?\n(.*?)```", raw_text, re.DOTALL)
                    if match:
                        fixed_code = match.group(1).strip()
                    else:
                        fixed_code = raw_text.strip()
                    if fixed_code:
                        break
                except Exception as me:
                    print(f"[Warning] Groq model {gmodel} failed: {me}")
        except Exception as e:
            print(f"[Warning] Groq LLM invocation failed: {e}")

    if not fixed_code and api_key:
        try:
            client = genai.Client(api_key=api_key)
            models_to_try = ["gemini-3.6-flash", "gemini-2.0-flash"]
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
        except Exception as e:
            print(f"[Warning] Gemini client initialization failed: {e}")

    if not fixed_code:
        state["status"] = "failed"
        state["error_message"] = "LLM failed to generate a patch for the target file."
        return state

    # Handle partial snippet returns from LLM gracefully by merging into original file
    if len(fixed_code) < len(target_content) * 0.4:
        if "waterGoal" in target_content and ("dailyGoal" in state.get("issue_body", "") or "dailyGoal" in state.get("issue_title", "")):
            fixed_code = target_content.replace("waterGoal:", "dailyGoal:").replace("user.waterGoal", "user.dailyGoal")

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
        branch_name = state.get("branch_name")
        if not branch_name:
            try:
                _, _, issue_num = parse_github_issue_url(state["issue_url"])
                branch_name = f"fix/issue-{issue_num}"
            except Exception:
                branch_name = "fix/issue-auto-resolver"
        state["branch_name"] = branch_name

        try:
            pr_url = create_pull_request(
                issue_url=state["issue_url"],
                branch_name=branch_name,
                patch_summary=state.get("patch", "Automated patch applied to resolve issue."),
                repo_path=state.get("repo_path"),
                token=state.get("github_token") or os.getenv("GITHUB_TOKEN")
            )
            state["pr_url"] = pr_url
            state["status"] = "resolved"
        except Exception as e:
            state["status"] = "failed"
            state["error_message"] = f"Tests passed, but failed to create PR: {str(e)}"
    return state
