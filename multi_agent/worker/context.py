"""把一次 execution 的 CodexEvent 追加写入 tasks/context。"""
import json
from dataclasses import asdict
from pathlib import Path

from multi_agent.models import CodexEvent
from multi_agent.util.paths import place_file, run_directory


def save_context(project_root: str, run_id: str, event: CodexEvent) -> Path:
    path = place_file(
        run_directory(project_root, run_id) / "tasks" / "context",
        f"{event.execution_id}context.jsonl",
    )
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(event), ensure_ascii=False) + "\n")
    return path
