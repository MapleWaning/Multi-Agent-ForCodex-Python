"""只放数据结构。

不启动进程，不读写文件。
"""

from dataclasses import dataclass

from multi_agent.models.profile import ApprovalPolicy, ReasoningEffort, Sandbox
from multi_agent.models.states import (
    OrchestrationEvent as OrchestrationEventType,
    RunStatus,
    TaskStatus,
    WorkerStatus,
)


@dataclass
class Run:
    id: str
    project_root: str
    prompt: str
    created_at: str
    updated_at: str
    status: RunStatus = RunStatus.CREATED
    plan_path: str | None = None


@dataclass
class Task:
    id: str
    run_id: str
    sequence: int
    task_type: str
    created_at: str
    updated_at: str
    architect_id: int | None = None
    worker_id: int | None = None
    status: TaskStatus = TaskStatus.PENDING
    content_path: str | None = None
    context_path: str | None = None


@dataclass
class Execution:
    id: str
    task_id: str
    sandbox: str
    model: str
    reasoning_effort: str
    created_at: str
    updated_at: str
    model_id: int | None = None
    context_window: int | None = None
    tool_output_token_limit: int | None = None
    status: str = "CREATED"
    exit_code: int | None = None
    summary: str | None = None


@dataclass
class Provider:
    id: str
    name: str
    base_url: str
    wire_api: str
    env_key: str


@dataclass
class Model:
    provider_id: str
    model: str
    sandbox: Sandbox
    reasoning_effort: ReasoningEffort
    id: int | None = None
    context_window: int | None = None
    tool_output_token_limit: int | None = None


@dataclass
class Architect:
    model: str
    reasoning_effort: ReasoningEffort
    sandbox: Sandbox
    forced_login_method: str
    approval_policy: ApprovalPolicy
    id: int | None = None


@dataclass
class Worker:
    model_id: int
    id: int | None = None
    role: str = "executor"
    status: WorkerStatus = WorkerStatus.UNAVAILABLE


@dataclass
class CodexEvent:
    execution_id: str
    payload: str
    created_at: str
    id: int | None = None
    event_type: str | None = None


@dataclass
class OrchestrationEvent:
    run_id: str
    event_type: OrchestrationEventType
    created_at: str
    id: int | None = None
    payload: str | None = None


@dataclass
class WorkerProfile:
    name: str
    sandbox: Sandbox
    model: str
    reasoning_effort: ReasoningEffort
    approval_policy: ApprovalPolicy
    context_window: int | None = None
    tool_output_token_limit: int | None = None
    provider_name: str | None = None
    base_url: str | None = None
    wire_api: str | None = None
    env_key: str | None = None
    forced_login_method: str | None = None
