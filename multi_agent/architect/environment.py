"""把本机环境正文写入 architect/environment.md。"""
from pathlib import Path

from multi_agent.util.paths import place_file, run_directory


def write_environment(project_root: str, run_id: str, dev_env: str) -> Path:
    path = place_file(run_directory(project_root, run_id) / "architect", "environment.md")
    text = dev_env if dev_env.endswith("\n") else dev_env + "\n"
    path.write_text(text, encoding="utf-8")
    return path
