"""只放数据结构：任务输入、运行状态、事件、执行结果。

不启动进程，不读写文件。
"""

from dataclasses import dataclass

from multi_agent.profile import ReasoningEffort, Sandbox
from multi_agent.state import RunStatus

@dataclass
class Task:
    run_id: str
    project_root: str
    prompt: str
    profile: WorkerProfile
    created_at: str

@dataclass
class TaskResult:
    run_id: str
    status: str
    exit_code: int
    summary: str

@dataclass
class RunState:
    run_id: str
    status: RunStatus
    updated_at: str

@dataclass
class WorkerProfile:
    name: str
    sandbox: Sandbox
    model: str
    reasoning_effort: ReasoningEffort