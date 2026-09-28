"""只负责某个 run 目录下四个文件的读写。

task.json、state.json、events.jsonl、result.json。
不决定状态怎么变迁，也不启动 Worker。
"""
from multi_agent.models import Task, TaskResult, RunState
from dataclasses import asdict
from pathlib import Path
import json


def get_run_dir(run_id: str) -> Path:
    run_dir = Path(".multi_agent")/"run"/ run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir

def save_task(task: Task):
    data = asdict(task)
    run_dir = get_run_dir(task.run_id)
    task_path = run_dir/"task.json"
    with open(task_path,encoding="utf-8", mode="w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def save_state(state: RunState):
    data = asdict(state)
    run_dir = get_run_dir(state.run_id)
    state_path = run_dir/"state.json"
    with open(state_path,encoding="utf-8", mode="w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
def save_event(run_id: str,event: dict):
    path = get_run_dir(run_id)/"events.jsonl"
    line = json.dumps(event, ensure_ascii=False)
    with open(path,encoding="utf-8", mode="a") as f:
        f.write(line + "\n")

def save_result(result: TaskResult):
    data = asdict(result)
    run_dir = get_run_dir(result.run_id)
    result_path = run_dir/"result.json"
    with open(result_path,encoding="utf-8", mode="w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)