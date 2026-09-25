# 🤖 Smart GitHub Issue Resolver AI Agent

An autonomous AI-powered agentic system that ingests GitHub issue URLs, inspects repository codebases, diagnoses bug root causes, generates targeted code patches using LLMs with failover logic, verifies fixes in an isolated sandbox, and automatically creates GitHub Pull Requests.

## Live Link https://github-agent-atvg.onrender.com
---

## 📸 Interface & Live Workflow

### 1. Main Dashboard & Input Form
Paste any public GitHub issue link (and optional local repo path / GitHub token) to launch the automated resolution workflow.

![Launch AI Resolver](./img/Screenshot%202026-09-13%20125841.png)

---

### 2. Live Agent Resolution Pipeline
The agent inspects repository structure, fetches issue details, pinpoints faulty source files (`backend/routes/users.js`), generates a code fix, and runs verification unit tests.

![Live Resolution Pipeline](./img/Screenshot%202026-09-13%20125913.png)

---

### 3. Verification & Automated Resolution Complete
Once verification tests pass cleanly, the agent commits changes, pushes a dedicated fix branch (`fix/issue-2`), and generates the Pull Request link.

![Resolution Complete & View PR](./img/Screenshot%202026-09-13%20125940.png)

---

### 4. Opened Pull Request on GitHub
Clicking **View Opened Pull Request** opens the newly generated PR directly on GitHub, complete with title, patch summary, and ready-to-merge state.

![Opened GitHub Pull Request](./img/Screenshot%202026-09-13%20130427.png)

---

## 🧠 System Architecture & Graph Nodes Flowchart

The system is structured as a state machine / directed graph consisting of 4 core processing nodes. State (`AgentState`) is mutated sequentially as execution flows from initial URL ingestion to final PR creation.

```
                  ┌──────────────────────────────────────────┐
                  │          [GitHub Issue URL]              │
                  └────────────────────┬─────────────────────┘
                                       │
                                       ▼
                  ┌──────────────────────────────────────────┐
                  │       Node 1: investigate_node           │
                  │  - Parse URL & Clone/Inspect Repo Tree   │
                  │  - Index source code into AgentState     │
                  └────────────────────┬─────────────────────┘
                                       │
                                       ▼
                  ┌──────────────────────────────────────────┐
                  │      Node 2: execute_patch_node          │
                  │  - Heuristic Target File Identification  │
                  │  - LLM Patch Generation (Groq/Gemini)    │
                  │  - Apply code patch to local filesystem │
                  └────────────────────┬─────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                      Node 3: verify_tests_node                           │
│  - Execute unit tests in isolated subprocess / sandbox                   │
│  - Evaluate test pass/fail status                                        │
└──────────────────────────────────────┬───────────────────────────────────┘
                                       │
                ┌──────────────────────┴──────────────────────┐
                │                                             │
      [Tests Passed]                                   [Tests Failed]
                │                                             │
                ▼                                             ▼
┌──────────────────────────────┐              ┌────────────────────────────┐
│   Node 4: resolve_node       │              │ Retry Limit Check          │
│ - Git branch & commit        │              │  retry_count < max_retries │
│ - Git push to remote         │              └──────────────┬─────────────┘
│ - GitHub PyGithub API PR     │                             │
└──────────────────────────────┘              ┌──────────────┴─────────────┐
                                              │                            │
                                           [True]                       [False]
                                              │                            │
                                              ▼                            ▼
                                    Re-trigger Node 2            Set State: Failed
                                    with Error Context           Return error output
```

---

## 🔍 Detailed Node Execution Breakdown

### 1. `investigate_node` ([`src/agent.py`](file:///c:/node/github_agent/src/agent.py#L14-L22))
* **Function**: Scans the target repository structure and populates source files into the agent state.
* **Mechanism**: 
  * If a remote GitHub URL is provided, `clone_github_repository()` clones the repo into a temporary workspace (`tempfile.mkdtemp`).
  * `inspect_repository()` uses `os.walk()` to recursively traverse the workspace, bypassing directories like `.git`, `node_modules`, `__pycache__`, and `venv`.
  * Reads source files (`.py`, `.js`, `.ts`, `.jsx`, `.tsx`) into `state["target_files"]` map and records directory tree relative paths into `state["file_tree"]`.

### 2. `execute_patch_node` ([`src/agent.py`](file:///c:/node/github_agent/src/agent.py#L25-L190))
* **Function**: Identifies the single faulty source file and invokes LLM models to generate a corrected version.
* **Targeting Heuristics**:
  1. **Direct Path Match**: Checks if exact file path or base filename is explicitly mentioned in issue title/body.
  2. **Title Keyword Stem Matching**: Tokenizes issue title, removes file extensions, and compares stems against repo file names.
  3. **Body Keyword Stem Matching**: Tokenizes issue description body to find relevant source module names.
  4. **Fallback**: Selects the first non-test source file in the repository.
* **LLM Model Orchestration**:
  * **Groq API**: Tries models in sequence (`groq/compound`, `qwen/qwen3.6-27b`, `groq/compound-mini`, `openai/gpt-oss-120b`).
  * **Gemini API Fallback**: If Groq fails or is unconfigured, calls `google-genai` client using `gemini-3.6-flash` or `gemini-2.0-flash`.
* **Patch Application**: Strips markdown backticks from response, detects truncated outputs, and overwrites target file contents via `apply_patch_to_file()`.

### 3. `verify_tests_node` ([`src/agent.py`](file:///c:/node/github_agent/src/agent.py#L192-L211))
* **Function**: Executes repository unit tests in a isolated local sandbox environment (`src/sandbox.py`).
* **Execution Flow**:
  * Detects test framework dynamically (`pytest`, `unittest`, or `npm test`).
  * Runs test subprocess and captures exit code + stderr/stdout execution logs.
  * If tests pass (`exit_code == 0`), updates `state["status"] = "resolved"`.
  * If tests fail, increments `state["retry_count"]`. If `retry_count < max_retries`, loops back to Node 2 (`execute_patch_node`), passing failed test execution logs into the LLM prompt for self-correction.

### 4. `resolve_node` ([`src/agent.py`](file:///c:/node/github_agent/src/agent.py#L213-L240))
* **Function**: Publishes code changes to GitHub and opens a Pull Request.
* **Detailed Flow**: Calls `create_pull_request()` in [`src/github_utils.py`](file:///c:/node/github_agent/src/github_utils.py#L64-L121).

---

## 🛠️ Deep-Dive: How Pull Requests (PRs) Are Generated

The PR generation pipeline requires careful git state management to prevent dirty tree conflicts or empty diff errors.

### Git Branching & Commit Workflow
1. **Dynamic Branch Creation**: Formats branch name as `fix/issue-{issue_number}` (e.g., `fix/issue-2`).
2. **Clean Branch Switching**: Executes `local_repo.git.checkout('-B', branch_name)`. 
   * *Why `-B`?* Using `-b` fails if the branch already exists from a previous run. Using standard `checkout` without `-B` can overwrite local dirty edits. `-B` forces creation or reset of the branch at `HEAD` **while preserving local working directory edits**.
3. **Staging & Dirty State Check**: Runs `local_repo.git.add('-A')` and verifies `not local_repo.is_dirty(untracked_files=True)`. If no files were modified, it aborts to prevent empty PR creation.
4. **Local Commit**: Executes `local_repo.git.commit('-m', 'Fix: Auto-resolved #N')`.
5. **Remote URL & Authentication Injection**: Formats authenticated Git remote URL:
   ```text
   https://x-access-token:{GITHUB_TOKEN}@github.com/{owner}/{repo}.git
   ```
   Updates origin URL via `local_repo.remote("origin").set_url(remote_url)` and pushes branch via `local_repo.git.push('--set-upstream', 'origin', branch_name)`.

### GitHub PyGithub API PR Creation
1. Initializes PyGithub client: `Github(auth=Auth.Token(token))`.
2. Inspects remote open PRs (`repo.get_pulls(state="open")`) to check if a PR for `branch_name` already exists. If found, returns its HTML URL directly.
3. Invokes `repo.create_pull()`:
   * **`title`**: `"Fix: Auto-resolved #<issue_num>"`
   * **`body`**: Formatted summary detailing patch context and verification status.
   * **`head`**: `branch_name` (`fix/issue-2`)
   * **`base`**: Default target branch (`main` / `master`).
4. Returns the generated GitHub Pull Request URL (e.g., `https://github.com/owner/repo/pull/2`).

---

## 💡 Technical Interview Q&A (Preparation Guide)

### Q1: How does the system handle multi-user GitHub tokens securely?
**Answer**: The FastAPI server accepts an optional GitHub Personal Access Token (PAT) directly from the user's web form input. If provided, that token is passed down into Git clone/push operations and PyGithub API calls, creating the PR under the user's account. If omitted, it cleanly falls back to the server's environment `GITHUB_TOKEN`. Tokens are never stored permanently on disk.

### Q2: How does the agent identify which file to modify without parsing the whole project into the LLM context?
**Answer**: To keep context tight and prevent context length errors (e.g., Groq 413 payload limits), we use a 4-tier heuristic cascade:
1. Regex match for explicit filenames mentioned in issue title/body.
2. Word stem matching between tokenized issue titles and source filenames.
3. Word stem matching against issue description bodies.
4. Fallback selection of the primary non-test source file.
This filters out noisy files (`node_modules`, test suites, lockfiles) and feeds only the target file content (up to 5,000 characters) into the prompt.

### Q3: What happens if the LLM generates a patch that breaks unit tests?
**Answer**: The system features an autonomous feedback retry loop governed by `verify_tests_node`:
1. The patch is applied and unit tests are executed in `src/sandbox.py`.
2. If tests fail, the exit code is non-zero and test error logs (stderr/stdout) are captured.
3. `retry_count` is incremented. If `retry_count < max_retries`, the state machine loops back to `execute_patch_node`.
4. The failed test output is appended to the LLM prompt, enabling the model to analyze its error and produce a corrected fix on the next iteration.

### Q4: Why did PR creation fail initially, and how was the Git flow fixed?
**Answer**: Originally, `checkout('-b', branch_name)` was used after modifying files. If the branch already existed, Git threw an error and fell back to standard `checkout`, which wiped out local uncommitted edits. When `git push` ran, the remote branch was clean, causing GitHub API `create_pull()` to crash with `422 Unprocessable Entity (No commits)`. 
We fixed this by switching to `local_repo.git.checkout('-B', branch_name)` which safely creates or resets the branch while preserving working tree changes, followed by explicit dirty checks before staging and pushing.

---

## ✨ Features

- **Multi-User Token Authentication**: Accepts user GitHub PATs via web form or defaults to system `GITHUB_TOKEN`.
- **Autonomous Issue Ingestion**: Parses GitHub URLs and extracts titles, descriptions, and metadata via PyGithub.
- **Intelligent File Targeting**: Pinpoints faulty files using stem heuristics and regex issue extraction.
- **Multi-Provider LLM Resilience**: Tries Groq models first with fallback to Google Gemini (`gemini-3.6-flash`).
- **Isolated Sandbox Verification**: Runs unit tests locally to confirm fix validity before pushing code.
- **Automated PR Creation**: Manages git branch isolation (`fix/issue-#`), commits fixes, force-pushes remote branches, and opens GitHub PRs.

---

## 🚀 Quick Start

### 1. Installation
Clone the repository and install dependencies:
```bash
pip install -r requirements.txt
```

### 2. Environment Configuration
Create a `.env` file in the root directory:
```env
GITHUB_TOKEN=your_github_personal_access_token
GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key  # Optional
```

### 3. Run Web Dashboard
Launch the FastAPI server:
```bash
python app.py
```
Open your browser at `http://127.0.0.1:8000`.

### 4. Run via CLI
Alternatively, execute resolution via CLI:
```bash
python main.py
```

---

## 🧪 Testing
Run the test suite:
```bash
python -m unittest discover tests
```

