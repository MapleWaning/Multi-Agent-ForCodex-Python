"""只负责启动一次 `codex exec`，并取回退出码、stdout、stderr。

不创建 run_id，不决定 COMPLETED / FAILED，不写本地文件。
"""
import subprocess
import json

from multi_agent.models import WorkerProfile

def run_codex(prompt: str, project_root: str, worker_profile: WorkerProfile) -> tuple[int, list[dict], str]:
    command = [
    "codex", "exec",
    "--json",
    "--skip-git-repo-check",
    "--sandbox", worker_profile.sandbox,
    "-m", worker_profile.model,
    "-c", f'model_reasoning_effort="{worker_profile.reasoning_effort}"',
    "-p", worker_profile.name,
    prompt]
    completed = subprocess.run(
        command,
        capture_output=True,
        cwd=project_root,
        text=True,
        encoding="utf-8",
    )
    events = []
    for line in completed.stdout.splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
        events.append(event)
    return completed.returncode, events, completed.stderr or ""
