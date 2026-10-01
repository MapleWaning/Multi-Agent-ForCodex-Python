"""把 Plan 的结构化字段写入 architect/plan.json。"""
import json
from pathlib import Path

from multi_agent.models.plan import Plan
from multi_agent.util.paths import place_file, run_directory


def write_plan_json(project_root: str, run_id: str, plan: Plan) -> Path:
    path = place_file(run_directory(project_root, run_id) / "architect", "plan.json")
    path.write_text(json.dumps(_document(plan), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _document(plan: Plan) -> dict:
    return {
        "objective": plan.objective,
        "summary": plan.summary,
        "artifacts": [
            {
                "id": artifact.id,
                "filename": artifact.filename,
                "description": artifact.description,
            }
            for artifact in plan.artifacts
        ],
        "tasks": [
            {
                "id": task.id,
                "title": task.title,
                "objective": task.objective,
                "instructions": task.instructions,
                "dependencies": task.dependencies,
                "inputs": task.inputs,
                "expected_outputs": task.expected_outputs,
                "acceptance_criteria": task.acceptance_criteria,
            }
            for task in plan.tasks
        ],
        "acceptance_criteria": plan.acceptance_criteria,
    }
