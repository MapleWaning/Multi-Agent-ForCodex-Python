"""串联一次 Run 的确定顺序。

创建 run、保存任务、标记 RUNNING、调用 Runner、追加事件、
按退出码标记 COMPLETED 或 FAILED、保存 result，并把摘要交回 CLI。

不判断方案好不好，也不检查 Worker 改得对不对。
"""
from multi_agent.models import RunState, Task, TaskResult, WorkerProfile
from multi_agent.state import RunStatus
from multi_agent.storage import save_event, save_task, save_state,save_result
from datetime import datetime
import uuid 
from multi_agent.runner import run_codex

def create_run(prompt: str, project_root: str, worker_profile: WorkerProfile) -> TaskResult:
    run_id = str(uuid.uuid4())
    task = Task(
        run_id=run_id,
        prompt=prompt,
        profile=worker_profile,
        project_root=project_root,
        created_at=datetime.now().isoformat(),
    )
    save_task(task)
    save_state(RunState(run_id=run_id, status=RunStatus.RUNNING, updated_at=datetime.now().isoformat()))
    exit_code, events, stderr = run_codex(prompt, project_root, worker_profile)
    summary = ""
    for event in events:
        save_event(run_id, event)
        if event.get("type") != "item.completed":
            continue
        item = event.get("item") or {}
        if item.get("type") == "agent_message" and item.get("text"):
            summary += item["text"]
    if exit_code == 0:
        save_state(RunState(run_id=run_id, status=RunStatus.COMPLETED, updated_at=datetime.now().isoformat()))
        result = TaskResult(run_id=run_id, status=RunStatus.COMPLETED, exit_code=exit_code, summary=summary)
        save_result(result)
    else:
        save_state(RunState(run_id=run_id, status=RunStatus.FAILED, updated_at=datetime.now().isoformat()))
        result = TaskResult(run_id=run_id, status=RunStatus.FAILED, exit_code=exit_code, summary=stderr)
        save_result(result)
    return result