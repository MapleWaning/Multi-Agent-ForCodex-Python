import enum

from multi_agent.exceptions import InvalidStateError

class RunStatus(enum.StrEnum):
    CREATED = "CREATED"
    ARCHITECT_RUNNING = "ARCHITECT_RUNNING"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    APPROVED = "APPROVED"
    WORKERS_RUNNING = "WORKERS_RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class TaskStatus(enum.StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    WAITING_ACCEPTANCE = "WAITING_ACCEPTANCE"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class ExecutionStatus(enum.StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class WorkerStatus(enum.StrEnum):
    BUSY = "BUSY"
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"

class OrchestrationEvent(enum.StrEnum):
    # Run
    RUN_CREATED = "RUN_CREATED"

    # Architect
    ARCHITECT_STARTED = "ARCHITECT_STARTED"
    ARCHITECT_FAILED = "ARCHITECT_FAILED"
    ARCHITECT_COMPLETED = "ARCHITECT_COMPLETED"

    # Plan / Approval
    PLAN_READY = "PLAN_READY"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    PLAN_APPROVED = "PLAN_APPROVED"

    # Task / Worker
    TASK_STARTED = "TASK_STARTED"
    WORKER_STARTED = "WORKER_STARTED"
    WORKER_COMPLETED = "WORKER_COMPLETED"
    WORKER_FAILED = "WORKER_FAILED"
    WORKER_FALLBACK = "WORKER_FALLBACK"
    TASK_COMPLETED = "TASK_COMPLETED"
    TASK_FAILED = "TASK_FAILED"

    # Run result
    RUN_COMPLETED = "RUN_COMPLETED"
    RUN_FAILED = "RUN_FAILED"



def ensure_transition(current_status: RunStatus, target_status: RunStatus) -> None:
    if current_status == RunStatus.CREATED and target_status == RunStatus.ARCHITECT_RUNNING:
        return
    if current_status == RunStatus.ARCHITECT_RUNNING and target_status == RunStatus.WAITING_APPROVAL:
        return
    if current_status == RunStatus.ARCHITECT_RUNNING  and target_status == RunStatus.FAILED:
        return
    if current_status == RunStatus.WAITING_APPROVAL and target_status == RunStatus.APPROVED:
        return
    if current_status == RunStatus.APPROVED and target_status == RunStatus.WORKERS_RUNNING:
        return
    if current_status == RunStatus.WORKERS_RUNNING and target_status == RunStatus.COMPLETED:
        return
    if current_status == RunStatus.WORKERS_RUNNING and target_status == RunStatus.FAILED:
        return
    raise InvalidStateError(current_status.value, target_status.value)