"""把 Architect 的结构化输出校验成 Plan。

不写文件，也不访问 SQLite。
"""
from multi_agent.exceptions import OrchestratorError
from multi_agent.models.plan import Plan, PlanArtifact, PlanTask

_PLAN_FIELDS = {"objective", "summary", "artifacts", "tasks", "acceptance_criteria"}
_ARTIFACT_FIELDS = {"id", "filename", "description", "content"}
_TASK_FIELDS = {
    "id",
    "title",
    "objective",
    "instructions",
    "dependencies",
    "inputs",
    "expected_outputs",
    "acceptance_criteria",
}
_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}


def validate_plan(payload: dict) -> Plan:
    plan = _object(payload, "方案")
    _reject_unknown(plan, _PLAN_FIELDS, "方案")
    artifacts = [
        _artifact(item, index)
        for index, item in enumerate(_array(plan, "artifacts", "方案"), start=1)
    ]
    tasks = [
        _task(item, index)
        for index, item in enumerate(_array(plan, "tasks", "方案"), start=1)
    ]
    if not tasks:
        raise OrchestratorError("方案至少要有一个任务")
    _unique(artifacts, lambda item: (item.id.casefold(), item.id), "产物编号")
    _unique(artifacts, lambda item: (item.filename.casefold(), item.filename), "产物文件名")
    _unique(tasks, lambda item: (item.id.casefold(), item.id), "任务编号")
    task_ids = {item.id.casefold() for item in tasks}
    for task in tasks:
        for dependency in task.dependencies:
            if dependency.casefold() == task.id.casefold():
                raise OrchestratorError(f"任务 {task.id} 不能依赖自己")
            if dependency.casefold() not in task_ids:
                raise OrchestratorError(f"任务 {task.id} 依赖了不存在的任务 {dependency}")
    return Plan(
        objective=_text(plan, "objective", "方案"),
        summary=_text(plan, "summary", "方案"),
        artifacts=artifacts,
        tasks=tasks,
        acceptance_criteria=_texts(plan, "acceptance_criteria", "方案"),
    )


def _artifact(payload: object, index: int) -> PlanArtifact:
    label = f"第 {index} 个产物"
    artifact = _object(payload, label)
    _reject_unknown(artifact, _ARTIFACT_FIELDS, label)
    filename = _text(artifact, "filename", label)
    _check_filename(filename, label)
    return PlanArtifact(
        id=_identifier(_text(artifact, "id", label), label),
        filename=filename,
        description=_text(artifact, "description", label),
        content=_text(artifact, "content", label),
    )


def _task(payload: object, index: int) -> PlanTask:
    label = f"第 {index} 个任务"
    task = _object(payload, label)
    _reject_unknown(task, _TASK_FIELDS, label)
    task_id = _identifier(_text(task, "id", label), label)
    return PlanTask(
        id=task_id,
        title=_text(task, "title", label),
        objective=_text(task, "objective", label),
        instructions=_text(task, "instructions", label),
        dependencies=_texts(task, "dependencies", label),
        inputs=_texts(task, "inputs", label),
        expected_outputs=_texts(task, "expected_outputs", label),
        acceptance_criteria=_texts(task, "acceptance_criteria", label),
    )


def _object(payload: object, label: str) -> dict:
    if not isinstance(payload, dict):
        raise OrchestratorError(f"{label}必须是对象")
    return payload


def _reject_unknown(payload: dict, allowed: set[str], label: str) -> None:
    unknown = sorted(set(payload) - allowed)
    if unknown:
        names = "、".join(unknown)
        raise OrchestratorError(f"{label}含有未知字段 {names}")


def _text(payload: dict, field: str, label: str) -> str:
    if field not in payload:
        raise OrchestratorError(f"{label}缺少字段 {field}")
    value = payload[field]
    if not isinstance(value, str):
        raise OrchestratorError(f"{label}的字段 {field} 必须是字符串")
    return value


def _texts(payload: dict, field: str, label: str) -> list[str]:
    if field not in payload:
        raise OrchestratorError(f"{label}缺少字段 {field}")
    value = payload[field]
    if not isinstance(value, list):
        raise OrchestratorError(f"{label}的字段 {field} 必须是数组")
    texts = []
    for index, item in enumerate(value, start=1):
        if not isinstance(item, str):
            raise OrchestratorError(f"{label}的字段 {field} 第 {index} 项必须是字符串")
        texts.append(item)
    return texts


def _array(payload: dict, field: str, label: str) -> list:
    if field not in payload:
        raise OrchestratorError(f"{label}缺少字段 {field}")
    value = payload[field]
    if not isinstance(value, list):
        raise OrchestratorError(f"{label}的字段 {field} 必须是数组")
    return value


def _identifier(value: str, label: str) -> str:
    _check_path_component(value, f"{label}的编号")
    return value


def _check_filename(filename: str, label: str) -> None:
    _check_path_component(filename, f"{label}的文件名")
    if not filename.endswith(".md") or filename == ".md":
        raise OrchestratorError(f"{label}的文件名 {filename} 必须是 Markdown 文件名")


def _check_path_component(value: str, label: str) -> None:
    if value.strip() == "" or value != value.strip():
        raise OrchestratorError(f"{label} {value!r} 不能为空或包含首尾空白")
    if value in {".", ".."} or ".." in value:
        raise OrchestratorError(f"{label} {value} 不能包含目录")
    if any(separator in value for separator in ("/", "\\", ":")):
        raise OrchestratorError(f"{label} {value} 不能包含目录")
    if any(char in value for char in '<>"|?*') or any(ord(char) < 32 for char in value):
        raise OrchestratorError(f"{label} {value} 含有非法字符")
    if value.endswith("."):
        raise OrchestratorError(f"{label} {value} 不能以点结尾")
    stem = value.split(".", 1)[0].upper()
    if stem in _RESERVED_NAMES:
        raise OrchestratorError(f"{label} {value} 是系统保留名")


def _unique(items: list, key, label: str) -> None:
    seen = set()
    for item in items:
        identity, display = key(item)
        if identity in seen:
            raise OrchestratorError(f"{label}重复：{display}")
        seen.add(identity)
