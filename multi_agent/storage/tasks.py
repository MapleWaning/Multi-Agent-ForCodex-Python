"""读写 tasks。"""
from multi_agent.models import Execution, Run, Task
from multi_agent.models.states import TaskStatus
from multi_agent.storage.executions import save_execution
from multi_agent.storage.runs import save_run
from multi_agent.storage.sqlite_store import _entities, _entity, connect

_CONVERTERS = {"status": TaskStatus}


def save_task_record(task: Task) -> Task:
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO tasks (
                id, run_id, sequence, task_type, architect_id, worker_id,
                status, content_path, context_path, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task.id,
                task.run_id,
                task.sequence,
                task.task_type,
                task.architect_id,
                task.worker_id,
                task.status,
                task.content_path,
                task.context_path,
                task.created_at,
                task.updated_at,
            ),
        )
        return _entity(
            Task,
            connection.execute("SELECT * FROM tasks WHERE id = ?", (task.id,)).fetchone(),
            _CONVERTERS,
        )


def get_task(task_id: str) -> Task | None:
    with connect() as connection:
        return _entity(
            Task,
            connection.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone(),
            _CONVERTERS,
        )


def list_tasks(run_id: str) -> list[Task]:
    with connect() as connection:
        return _entities(
            Task,
            connection.execute(
                "SELECT * FROM tasks WHERE run_id = ? ORDER BY sequence",
                (run_id,),
            ).fetchall(),
            _CONVERTERS,
        )


def update_task_status(task: Task) -> Task:
    with connect() as connection:
        connection.execute(
            "UPDATE tasks SET status = ?, worker_id = ?, updated_at = ? WHERE id = ?",
            (task.status, task.worker_id, task.updated_at, task.id),
        )
        return _entity(
            Task,
            connection.execute("SELECT * FROM tasks WHERE id = ?", (task.id,)).fetchone(),
            _CONVERTERS,
        )


def save_task(run: Run, task: Task, execution: Execution) -> Task:
    save_run(run)
    saved = save_task_record(task)
    save_execution(execution)
    return saved
