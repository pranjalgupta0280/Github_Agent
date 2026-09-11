import os
import warnings
warnings.filterwarnings("ignore")

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional

from src.state import AgentState
from src.graph import build_issue_resolver_graph
from src.github_utils import fetch_github_issue, create_pull_request, clone_github_repository

app = FastAPI(title="Smart GitHub Issue Resolver API")

# Serve static web dashboard
app.mount("/static", StaticFiles(directory="web"), name="static")

class ResolveRequest(BaseModel):
    issue_url: str
    repo_path: Optional[str] = None
    github_token: Optional[str] = None

@app.get("/")
def serve_index():
    return FileResponse("web/index.html")

@app.post("/api/resolve")
def api_resolve_issue(req: ResolveRequest):
    token = req.github_token or os.getenv("GITHUB_TOKEN")
    
    # Auto-clone repository if local_repo_path is omitted
    if not req.repo_path:
        try:
            abs_repo_path = clone_github_repository(req.issue_url, token=token)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to clone remote repository: {str(e)}")
    else:
        abs_repo_path = os.path.abspath(req.repo_path)
        if not os.path.exists(abs_repo_path):
            raise HTTPException(status_code=400, detail=f"Local repository path not found: {abs_repo_path}")

    initial_state: AgentState = {
        "issue_url": req.issue_url,
        "issue_title": title,
        "issue_body": body,
        "repo_path": abs_repo_path,
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

    # 2. Run LangGraph StateMachine
    graph = build_issue_resolver_graph()
    final_state = graph.invoke(initial_state)

    # 3. Create real GitHub Pull Request if resolved
    pr_url = None
    if final_state.get("tests_passed"):
        branch_name = final_state.get("branch_name", "fix/auto-resolver")
        patch_summary = final_state.get("patch", "Applied automated fix.")
        pr_url = create_pull_request(
            issue_url=req.issue_url,
            branch_name=branch_name,
            patch_summary=patch_summary,
            token=token
        )
        final_state["pr_url"] = pr_url

    return {
        "status": final_state["status"],
        "tests_passed": final_state["tests_passed"],
        "patch": final_state.get("patch"),
        "pr_url": final_state.get("pr_url"),
        "error_message": final_state.get("error_message")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
