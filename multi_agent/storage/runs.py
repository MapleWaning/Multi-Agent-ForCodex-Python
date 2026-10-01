"""读写 runs。"""
from multi_agent.models import Run
from multi_agent.models.states import RunStatus
from multi_agent.storage.sqlite_store import _entity, connect

_CONVERTERS = {"status": RunStatus}


def save_run(run: Run) -> Run:
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO runs (id, project_root, prompt, status, plan_path, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run.id,
                run.project_root,
                run.prompt,
                run.status,
                run.plan_path,
                run.created_at,
                run.updated_at,
            ),
        )
        return _entity(
            Run,
            connection.execute("SELECT * FROM runs WHERE id = ?", (run.id,)).fetchone(),
            _CONVERTERS,
        )


def get_run(run_id: str) -> Run | None:
    with connect() as connection:
        return _entity(
            Run,
            connection.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone(),
            _CONVERTERS,
        )


def update_run_status(run: Run) -> Run:
    with connect() as connection:
        connection.execute(
            "UPDATE runs SET status = ?, plan_path = ?, updated_at = ? WHERE id = ?",
            (run.status, run.plan_path, run.updated_at, run.id),
        )
        return _entity(
            Run,
            connection.execute("SELECT * FROM runs WHERE id = ?", (run.id,)).fetchone(),
            _CONVERTERS,
        )
