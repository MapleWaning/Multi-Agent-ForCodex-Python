"""把每个 Artifact 的正文写入 architect/artifacts。"""
from pathlib import Path

from multi_agent.exceptions import OrchestratorError
from multi_agent.models.plan import Plan
from multi_agent.util.paths import place_file, run_directory


def write_artifacts(project_root: str, run_id: str, plan: Plan) -> list[Path]:
    directory = run_directory(project_root, run_id) / "architect" / "artifacts"
    paths = []
    for artifact in plan.artifacts:
        if not artifact.filename.endswith(".md") or artifact.filename == ".md":
            raise OrchestratorError(f"产物文件名 {artifact.filename} 必须是 Markdown 文件名")
        path = place_file(directory, artifact.filename)
        path.write_text(artifact.content, encoding="utf-8")
        paths.append(path)
    return paths
