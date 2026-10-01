"""读写 executions。"""
from multi_agent.models import Execution
from multi_agent.storage.sqlite_store import _entity, connect


def save_execution(execution: Execution) -> Execution:
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO executions (
                id, task_id, model_id, sandbox, model, reasoning_effort,
                context_window, tool_output_token_limit, status, exit_code, summary,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                execution.id,
                execution.task_id,
                execution.model_id,
                execution.sandbox,
                execution.model,
                execution.reasoning_effort,
                execution.context_window,
                execution.tool_output_token_limit,
                execution.status,
                execution.exit_code,
                execution.summary,
                execution.created_at,
                execution.updated_at,
            ),
        )
        return _entity(
            Execution,
            connection.execute("SELECT * FROM executions WHERE id = ?", (execution.id,)).fetchone(),
        )


def get_execution(execution_id: str) -> Execution | None:
    with connect() as connection:
        return _entity(
            Execution,
            connection.execute("SELECT * FROM executions WHERE id = ?", (execution_id,)).fetchone(),
        )


def get_execution_for_run(run_id: str) -> Execution | None:
    with connect() as connection:
        return _entity(
            Execution,
            connection.execute(
                """
                SELECT executions.*
                FROM executions
                JOIN tasks ON tasks.id = executions.task_id
                WHERE tasks.run_id = ?
                ORDER BY tasks.sequence, executions.created_at
                LIMIT 1
                """,
                (run_id,),
            ).fetchone(),
        )


def update_execution_status(execution: Execution) -> Execution:
    with connect() as connection:
        connection.execute(
            "UPDATE executions SET status = ?, updated_at = ? WHERE id = ?",
            (execution.status, execution.updated_at, execution.id),
        )
        return _entity(
            Execution,
            connection.execute("SELECT * FROM executions WHERE id = ?", (execution.id,)).fetchone(),
        )


def update_execution_result(execution: Execution) -> Execution:
    with connect() as connection:
        connection.execute(
            "UPDATE executions SET exit_code = ?, summary = ? WHERE id = ?",
            (execution.exit_code, execution.summary, execution.id),
        )
        return _entity(
            Execution,
            connection.execute("SELECT * FROM executions WHERE id = ?", (execution.id,)).fetchone(),
        )


def save_state(execution: Execution) -> Execution:
    return update_execution_status(execution)


def save_result(execution: Execution) -> Execution:
    return update_execution_result(execution)
