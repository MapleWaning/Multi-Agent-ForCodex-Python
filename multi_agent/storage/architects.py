"""读写 architects。"""
from multi_agent.models import Architect
from multi_agent.models.profile import ApprovalPolicy, ReasoningEffort, Sandbox
from multi_agent.storage.sqlite_store import _entities, _entity, connect

_CONVERTERS = {
    "reasoning_effort": ReasoningEffort,
    "sandbox": Sandbox,
    "approval_policy": ApprovalPolicy,
}


def save_architect(architect: Architect) -> Architect:
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO architects (
                model, reasoning_effort, sandbox, forced_login_method, approval_policy
            ) VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(model) DO UPDATE SET
                reasoning_effort = excluded.reasoning_effort,
                sandbox = excluded.sandbox,
                forced_login_method = excluded.forced_login_method,
                approval_policy = excluded.approval_policy
            """,
            (
                architect.model,
                architect.reasoning_effort,
                architect.sandbox,
                architect.forced_login_method,
                architect.approval_policy,
            ),
        )
        return _entity(
            Architect,
            connection.execute(
                "SELECT * FROM architects WHERE model = ?",
                (architect.model,),
            ).fetchone(),
            _CONVERTERS,
        )


def list_architects() -> list[Architect]:
    with connect() as connection:
        return _entities(
            Architect,
            connection.execute("SELECT * FROM architects ORDER BY id").fetchall(),
            _CONVERTERS,
        )


def get_architect(architect_id: int) -> Architect | None:
    with connect() as connection:
        return _entity(
            Architect,
            connection.execute("SELECT * FROM architects WHERE id = ?", (architect_id,)).fetchone(),
            _CONVERTERS,
        )
