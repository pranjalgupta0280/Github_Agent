# 🤖 Smart GitHub Issue Resolver AI Agent

An autonomous AI-powered agentic system that ingests GitHub issue URLs, inspects repository codebases, diagnoses bug root causes, generates precise code patches using LLMs, verifies fixes in an isolated sandbox, and automatically opens GitHub Pull Requests.

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

## ✨ Features

- **Autonomous Issue Ingestion**: Parses GitHub URLs and extracts titles, descriptions, and test logs using PyGithub API.
- **Intelligent File Targeting**: Scans repository tree and matches faulty modules using exact filename heuristics and LLM context analysis.
- **AI Code Patching**: Generates complete, functional bug fixes using Gemini and Groq model fallbacks.
- **Isolated Sandbox Verification**: Executes unit tests locally to confirm fix validity before pushing code.
- **Automated PR Creation**: Automatically manages git branches (`fix/issue-#`), commits fixes, pushes to remote, and creates GitHub Pull Requests.

---

## 🏗️ Architecture Overview

```
[GitHub Issue URL] ──► [Fetch & Parse Issue] ──► [Inspect Repository Tree]
                                                        │
                                                        ▼
[Pull Request Created] ◄── [Git Push & PR Node] ◄── [Verify Tests Sandbox] ◄── [LLM Patch Generator]
```

Detailed architectural flowcharts are documented in [`architecture_flowchart.txt`](./architecture_flowchart.txt) and [`pr_issue_flowchart.txt`](./pr_issue_flowchart.txt).

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
