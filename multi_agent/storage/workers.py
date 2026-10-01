"""读写 workers。"""
from multi_agent.models import Worker
from multi_agent.models.states import WorkerStatus
from multi_agent.storage.sqlite_store import _entities, _entity, connect

_CONVERTERS = {"status": WorkerStatus}


def save_worker(worker: Worker) -> Worker:
    with connect() as connection:
        cursor = connection.execute(
            "INSERT INTO workers (model_id, role, status) VALUES (?, ?, ?)",
            (worker.model_id, worker.role, worker.status),
        )
        return _entity(
            Worker,
            connection.execute("SELECT * FROM workers WHERE id = ?", (cursor.lastrowid,)).fetchone(),
            _CONVERTERS,
        )


def get_worker(worker_id: int) -> Worker | None:
    with connect() as connection:
        return _entity(
            Worker,
            connection.execute("SELECT * FROM workers WHERE id = ?", (worker_id,)).fetchone(),
            _CONVERTERS,
        )


def update_worker_status(worker: Worker) -> Worker:
    with connect() as connection:
        connection.execute(
            "UPDATE workers SET status = ? WHERE id = ?",
            (worker.status, worker.id),
        )
        return _entity(
            Worker,
            connection.execute("SELECT * FROM workers WHERE id = ?", (worker.id,)).fetchone(),
            _CONVERTERS,
        )


def enable_worker(worker: Worker) -> Worker:
    worker.status = WorkerStatus.AVAILABLE
    return update_worker_status(worker)


def disable_worker(worker: Worker) -> Worker:
    worker.status = WorkerStatus.UNAVAILABLE
    return update_worker_status(worker)


def get_worker_by_status(status: WorkerStatus) -> list[Worker]:
    with connect() as connection:
        return _entities(
            Worker,
            connection.execute(
                "SELECT * FROM workers WHERE status = ? ORDER BY id",
                (status,),
            ).fetchall(),
            _CONVERTERS,
        )
