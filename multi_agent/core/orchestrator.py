"""串联一次 Run。

create_run 负责 Architect 规划，停在 WAITING_APPROVAL。
worker_run 在审批通过后按任务文件顺序调用 Worker。
"""
import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

from multi_agent.agents.codex_runner import run_codex
from multi_agent.architect.artifacts import write_artifacts
from multi_agent.architect.environment import write_environment
from multi_agent.architect.plan_json import write_plan_json
from multi_agent.architect.tasks import write_tasks
from multi_agent.architect.validate import validate_plan
from multi_agent.exceptions import OrchestratorError, WorkerProviderError
from multi_agent.models import CodexEvent, Execution, OrchestrationEvent, Run, Task, WorkerProfile
from multi_agent.models.profile import ApprovalPolicy
from multi_agent.models.states import (
    ExecutionStatus,
    OrchestrationEvent as OrchestrationEventType,
    RunStatus,
    TaskStatus,
    WorkerStatus,
    ensure_transition,
)
from multi_agent.storage.executions import save_execution, save_result, save_state
from multi_agent.storage.models import get_model_by_id
from multi_agent.storage.orchestration_events import save_orchestration_event
from multi_agent.storage.providers import get_provider
from multi_agent.storage.runs import get_run, save_run, update_run_status
from multi_agent.storage.tasks import list_tasks, save_task_record, update_task_status
from multi_agent.storage.workers import get_worker_by_status
from multi_agent.util.paths import list_task_files, run_directory
from multi_agent.worker.context import save_context
from multi_agent.worker.executor_prompt import build_executor_prompt


def create_run(
    prompt: str,
    project_root: str,
    worker_profile: WorkerProfile,
    schema: bool = False,
    schema_file: Path | None = None,
    dev_env: str = "",
) -> tuple[Run, str]:
    created_at = datetime.now().isoformat()
    run_id = str(uuid.uuid4())
    run = Run(
        id=run_id,
        project_root=project_root,
        prompt=prompt,
        created_at=created_at,
        updated_at=created_at,
    )
    architect_task = Task(
        id=f"{run_id}:architect",
        run_id=run_id,
        sequence=1,
        task_type="ARCHITECT",
        created_at=created_at,
        updated_at=created_at,
        status=TaskStatus.RUNNING,
    )
    execution = Execution(
        id=f"{run_id}:execution",
        task_id=architect_task.id,
        sandbox=str(worker_profile.sandbox),
        model=worker_profile.model,
        reasoning_effort=str(worker_profile.reasoning_effort),
        created_at=created_at,
        updated_at=created_at,
        context_window=worker_profile.context_window,
        tool_output_token_limit=worker_profile.tool_output_token_limit,
        status=ExecutionStatus.RUNNING,
    )
    try:
        run = save_run(run)
        _record(run_id, OrchestrationEventType.RUN_CREATED, "启动")
        run = _transition_run(run, RunStatus.ARCHITECT_RUNNING)
        save_task_record(architect_task)
        save_execution(execution)
        _record(run_id, OrchestrationEventType.ARCHITECT_STARTED, "Architect 启动")
        try:
            exit_code, events, stderr = run_codex(
                prompt, project_root, worker_profile, schema, schema_file
            )
        except WorkerProviderError:
            _fail(run, architect_task, execution, 1, "")
            raise
        summary = _agent_message(events)
        if exit_code != 0:
            return _fail(run, architect_task, execution, exit_code, stderr), summary
        execution.status = ExecutionStatus.COMPLETED
        execution.exit_code = exit_code
        execution.summary = summary
        execution.updated_at = datetime.now().isoformat()
        save_state(execution)
        save_result(execution)
        try:
            plan = validate_plan(json.loads(summary))
            plan_path = write_plan_json(project_root, run_id, plan)
            write_artifacts(project_root, run_id, plan)
            task_paths = write_tasks(project_root, run_id, plan)
            _record(run_id, OrchestrationEventType.ARCHITECT_COMPLETED, "Architect 完成")
            _record(run_id, OrchestrationEventType.PLAN_READY, "方案已生成")
        except (json.JSONDecodeError, OrchestratorError) as error:
            _fail(run, architect_task, execution, exit_code, summary)
            raise OrchestratorError(str(error)) from error
        architect_task.status = TaskStatus.COMPLETED
        architect_task.updated_at = datetime.now().isoformat()
        update_task_status(architect_task)
        allocated_at = architect_task.updated_at
        for index, (plan_task, path) in enumerate(zip(plan.tasks, task_paths), start=2):
            save_task_record(
                Task(
                    id=f"{run_id}:{plan_task.id}",
                    run_id=run_id,
                    sequence=index,
                    task_type="WORKER",
                    created_at=allocated_at,
                    updated_at=allocated_at,
                    status=TaskStatus.PENDING,
                    content_path=str(path),
                )
            )
        write_environment(project_root, run_id, dev_env)
        run.plan_path = str(plan_path)
        run = _transition_run(run, RunStatus.WAITING_APPROVAL)
        _record(run_id, OrchestrationEventType.WAITING_APPROVAL, "等待审批")
        return run, summary
    except sqlite3.Error as error:
        raise OrchestratorError(str(error)) from error


def worker_run(run_id: str, approve: bool) -> tuple[Run, str]:
    run = get_run(run_id)
    if run is None:
        raise OrchestratorError(f"Run {run_id} 不存在")
    if run.status != RunStatus.WAITING_APPROVAL:
        raise OrchestratorError(f"Run {run_id} 当前状态是 {run.status}，不能审批")
    if not approve:
        raise OrchestratorError("审批未通过")
    try:
        dev_env, workers, assignments = _prepare_workers(run)
        _record(run.id, OrchestrationEventType.PLAN_APPROVED, "审批通过")
        run = _transition_run(run, RunStatus.APPROVED)
        run = _transition_run(run, RunStatus.WORKERS_RUNNING)
        summary = ""
        for index, (task, task_file) in enumerate(assignments):
            worker, profile = workers[index % len(workers)]
            run, summary, stopped = _execute_worker(
                run, task, task_file, worker, profile, dev_env, summary
            )
            if stopped:
                return run, summary
        _record(run.id, OrchestrationEventType.RUN_COMPLETED, "完成")
        return _transition_run(run, RunStatus.COMPLETED), summary
    except sqlite3.Error as error:
        raise OrchestratorError(str(error)) from error


def _record(run_id: str, event_type: OrchestrationEventType, message: str) -> None:
    save_orchestration_event(
        OrchestrationEvent(
            run_id=run_id,
            event_type=event_type,
            created_at=datetime.now().isoformat(),
            payload=f"工作流：{run_id} {message}",
        )
    )


def _transition_run(run: Run, target: RunStatus) -> Run:
    ensure_transition(run.status, target)
    run.status = target
    run.updated_at = datetime.now().isoformat()
    return update_run_status(run)


def _fail(
    run: Run,
    architect_task: Task,
    execution: Execution,
    exit_code: int,
    summary: str,
) -> Run:
    now = datetime.now().isoformat()
    execution.status = ExecutionStatus.FAILED
    execution.exit_code = exit_code
    execution.summary = summary
    execution.updated_at = now
    save_state(execution)
    save_result(execution)
    architect_task.status = TaskStatus.FAILED
    architect_task.updated_at = now
    update_task_status(architect_task)
    _record(run.id, OrchestrationEventType.ARCHITECT_FAILED, "Architect 失败")
    failed = _transition_run(run, RunStatus.FAILED)
    _record(run.id, OrchestrationEventType.RUN_FAILED, "失败")
    return failed


def _agent_message(events: list) -> str:
    summary = ""
    for event in events:
        if event.get("type") != "item.completed":
            continue
        item = event.get("item") or {}
        if item.get("type") == "agent_message" and item.get("text"):
            summary += item["text"]
    return summary


def _prepare_workers(run: Run) -> tuple[str, list, list]:
    environment = run_directory(run.project_root, run.id) / "architect" / "environment.md"
    if not environment.is_file():
        raise OrchestratorError(f"Run {run.id} 缺少 environment.md")
    dev_env = environment.read_text(encoding="utf-8").rstrip("\n")
    task_files = list_task_files(run.project_root, run.id)
    stored = [task for task in list_tasks(run.id) if task.task_type == "WORKER"]
    assignments = [(_task_for_file(stored, path), path) for path in task_files]
    available = get_worker_by_status(WorkerStatus.AVAILABLE)
    if assignments and not available:
        raise OrchestratorError("没有可用的 Worker")
    workers = [_worker_profile(worker) for worker in available]
    return dev_env, workers, assignments


def _task_for_file(tasks: list[Task], path: Path) -> Task:
    resolved = path.resolve()
    for task in tasks:
        if task.content_path and Path(task.content_path).resolve() == resolved:
            return task
    raise OrchestratorError(f"任务文件 {path.name} 没有对应的 Task")


def _worker_profile(worker) -> tuple:
    model = get_model_by_id(worker.model_id)
    if model is None:
        raise OrchestratorError(f"Worker {worker.id} 的模型不存在")
    provider = get_provider(model.provider_id)
    if provider is None:
        raise OrchestratorError(f"模型 {model.model} 的 Provider 不存在")
    profile = WorkerProfile(
        name=provider.id,
        sandbox=model.sandbox,
        model=model.model,
        reasoning_effort=model.reasoning_effort,
        approval_policy=ApprovalPolicy.ON_REQUEST,
        context_window=model.context_window,
        tool_output_token_limit=model.tool_output_token_limit,
        provider_name=provider.name,
        base_url=provider.base_url,
        wire_api=provider.wire_api,
        env_key=provider.env_key,
    )
    return worker, profile


def _execute_worker(run, task, task_file, worker, profile, dev_env: str, summary: str):
    now = datetime.now().isoformat()
    _record(run.id, OrchestrationEventType.TASK_STARTED, f"任务 {task_file.name} 启动")
    task.status = TaskStatus.RUNNING
    task.worker_id = worker.id
    task.updated_at = now
    update_task_status(task)
    _record(run.id, OrchestrationEventType.WORKER_STARTED, f"Worker {worker.id} 启动")
    execution = Execution(
        id=str(uuid.uuid4()),
        task_id=task.id,
        sandbox=str(profile.sandbox),
        model=profile.model,
        reasoning_effort=str(profile.reasoning_effort),
        created_at=now,
        updated_at=now,
        model_id=worker.model_id,
        context_window=profile.context_window,
        tool_output_token_limit=profile.tool_output_token_limit,
        status=ExecutionStatus.RUNNING,
    )
    save_execution(execution)
    prompt = build_executor_prompt(dev_env, run.project_root, str(task_file))
    try:
        exit_code, events, stderr = run_codex(prompt, run.project_root, profile)
    except WorkerProviderError:
        _fail_worker(run, task, execution, 1, "")
        raise
    for event in events:
        save_context(
            run.project_root,
            run.id,
            CodexEvent(
                execution_id=execution.id,
                payload=json.dumps(event, ensure_ascii=False),
                created_at=datetime.now().isoformat(),
                event_type=event.get("type"),
            ),
        )
    piece = _agent_message(events)
    summary = _append_summary(summary, piece)
    if exit_code != 0:
        return _fail_worker(run, task, execution, exit_code, stderr), summary, True
    execution.status = ExecutionStatus.COMPLETED
    execution.exit_code = exit_code
    execution.summary = piece
    execution.updated_at = datetime.now().isoformat()
    save_state(execution)
    save_result(execution)
    task.status = TaskStatus.COMPLETED
    task.updated_at = execution.updated_at
    update_task_status(task)
    _record(run.id, OrchestrationEventType.WORKER_COMPLETED, f"Worker {worker.id} 完成")
    _record(run.id, OrchestrationEventType.TASK_COMPLETED, f"任务 {task_file.name} 完成")
    return run, summary, False


def _fail_worker(run: Run, task: Task, execution: Execution, exit_code: int, summary: str) -> Run:
    now = datetime.now().isoformat()
    execution.status = ExecutionStatus.FAILED
    execution.exit_code = exit_code
    execution.summary = summary
    execution.updated_at = now
    save_state(execution)
    save_result(execution)
    task.status = TaskStatus.FAILED
    task.updated_at = now
    update_task_status(task)
    _record(run.id, OrchestrationEventType.WORKER_FAILED, f"Worker {task.worker_id} 失败")
    _record(run.id, OrchestrationEventType.TASK_FAILED, "任务失败")
    failed = _transition_run(run, RunStatus.FAILED)
    _record(run.id, OrchestrationEventType.RUN_FAILED, "失败")
    return failed


def _append_summary(summary: str, piece: str) -> str:
    if not piece:
        return summary
    if not summary:
        return piece
    return f"{summary}\n{piece}"
