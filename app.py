import os
import uuid
from typing import Dict, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.github_utils import clone_github_repository, fetch_github_issue
from src.graph import build_issue_resolver_graph
from src.state import AgentState

app = FastAPI(title="Smart GitHub Issue Resolver API")
if os.path.exists("web"):
    app.mount("/static", StaticFiles(directory="web"), name="static")

tasks_db: Dict[str, dict] = {}

class ResolveRequest(BaseModel):
    issue_url: str
    repo_path: Optional[str] = None
    github_token: Optional[str] = None

def run_agent_job(task_id: str, req: ResolveRequest) -> None:
    token = req.github_token or os.getenv("GITHUB_TOKEN")
    tasks_db[task_id]["status"] = "in_progress"
    try:
        if req.repo_path:
            abs_repo_path = os.path.abspath(req.repo_path)
            if not os.path.exists(abs_repo_path):
                raise FileNotFoundError(f"Local repo path not found: {abs_repo_path}")
        else:
            abs_repo_path = clone_github_repository(req.issue_url, token=token)

        repo_name, title, body = fetch_github_issue(req.issue_url, token=token)
        initial_state: AgentState = {
            "issue_url": req.issue_url, "issue_title": title, "issue_body": body,
            "repo_path": abs_repo_path, "repo_name": repo_name, "github_token": token,
            "file_tree": [], "target_files": {}, "patch": None, "modified_files": {},
            "test_logs": "", "tests_passed": False, "retry_count": 0, "max_retries": 3,
            "status": "investigating", "branch_name": None, "pr_url": None, "error_message": None,
        }
        final_state = build_issue_resolver_graph().invoke(initial_state)
        modified_files = final_state.get("modified_files") or {}
        target_files = modified_files or final_state.get("target_files") or {}
        target_file = next(iter(target_files), None)
        tasks_db[task_id] = {
            "task_id": task_id, "status": final_state["status"],
            "issue_title": final_state.get("issue_title"), "issue_body": final_state.get("issue_body"),
            "target_file": target_file,
            "target_content": target_files.get(target_file) if target_file else None,
            "tests_passed": final_state["tests_passed"], "patch": final_state.get("patch"),
            "pr_url": final_state.get("pr_url"),
            "error_message": final_state.get("error_message") or (
                (final_state.get("test_logs") or "")[:500] if not final_state.get("tests_passed") else None
            ),
        }
    except Exception as exc:
        tasks_db[task_id] = {
            "task_id": task_id, "status": "failed", "tests_passed": False, "error_message": str(exc),
        }

@app.get("/")
def serve_index():
    if os.path.exists("web/index.html"):
        return FileResponse("web/index.html")
    return {"message": "Smart GitHub Issue Resolver API is running."}

@app.post("/api/resolve", status_code=202)
def api_resolve_issue(req: ResolveRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    tasks_db[task_id] = {"task_id": task_id, "status": "queued", "issue_url": req.issue_url}
    background_tasks.add_task(run_agent_job, task_id, req)
    return {"task_id": task_id, "status": "queued", "check_status_url": f"/api/status/{task_id}"}

@app.get("/api/status/{task_id}")
def get_task_status(task_id: str):
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task ID not found")
    return tasks_db[task_id]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
