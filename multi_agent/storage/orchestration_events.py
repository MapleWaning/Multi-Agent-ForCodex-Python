"""读写 orchestration_events。"""
from multi_agent.models import OrchestrationEvent
from multi_agent.models.states import OrchestrationEvent as OrchestrationEventType
from multi_agent.storage.sqlite_store import _entities, _entity, connect

_CONVERTERS = {"event_type": OrchestrationEventType}


def save_orchestration_event(event: OrchestrationEvent) -> OrchestrationEvent:
    with connect() as connection:
        cursor = connection.execute(
            """
            INSERT INTO orchestration_events (run_id, event_type, payload, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (event.run_id, event.event_type, event.payload, event.created_at),
        )
        return _entity(
            OrchestrationEvent,
            connection.execute(
                "SELECT * FROM orchestration_events WHERE id = ?",
                (cursor.lastrowid,),
            ).fetchone(),
            _CONVERTERS,
        )


def get_orchestration_events(run_id: str) -> list[OrchestrationEvent]:
    with connect() as connection:
        return _entities(
            OrchestrationEvent,
            connection.execute(
                """
                SELECT * FROM orchestration_events
                WHERE run_id = ?
                ORDER BY id
                """,
                (run_id,),
            ).fetchall(),
            _CONVERTERS,
        )
