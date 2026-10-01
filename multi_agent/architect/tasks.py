"""按固定模板把每个 Task 写成给 Worker 读取的 tasks/<task_id>.md。"""
from pathlib import Path

from multi_agent.models.plan import Plan, PlanTask
from multi_agent.util.paths import path_component, place_file, run_directory


def write_tasks(project_root: str, run_id: str, plan: Plan) -> list[Path]:
    directory = run_directory(project_root, run_id) / "tasks"
    paths = []
    for task in plan.tasks:
        path_component(task.id, "任务编号")
        path = place_file(directory, f"{task.id}.md")
        path.write_text(_task_markdown(task), encoding="utf-8")
        paths.append(path)
    return paths


def _task_markdown(task: PlanTask) -> str:
    return (
        f"# {task.title}\n"
        "\n"
        f"Task: {task.id}\n"
        "\n"
        "## Objective\n"
        "\n"
        f"{task.objective}\n"
        "\n"
        "## Instructions\n"
        "\n"
        f"{task.instructions}\n"
        "\n"
        "## Dependencies\n"
        "\n"
        f"{_items(task.dependencies)}\n"
        "\n"
        "## Inputs\n"
        "\n"
        f"{_items(task.inputs)}\n"
        "\n"
        "## Expected Outputs\n"
        "\n"
        f"{_items(task.expected_outputs)}\n"
        "\n"
        "## Acceptance Criteria\n"
        "\n"
        f"{_items(task.acceptance_criteria)}\n"
    )


def _items(items: list[str]) -> str:
    if not items:
        return "- 无"
    return "\n".join(f"- {item}" for item in items)
