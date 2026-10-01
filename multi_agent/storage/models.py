"""读写 models。"""
from multi_agent.models import Model
from multi_agent.models.profile import ReasoningEffort, Sandbox
from multi_agent.storage.sqlite_store import _entity, connect

_CONVERTERS = {"sandbox": Sandbox, "reasoning_effort": ReasoningEffort}


def save_model(model: Model) -> Model:
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO models (
                provider_id, model, sandbox, reasoning_effort,
                context_window, tool_output_token_limit
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(model) DO UPDATE SET
                provider_id = excluded.provider_id,
                sandbox = excluded.sandbox,
                reasoning_effort = excluded.reasoning_effort,
                context_window = excluded.context_window,
                tool_output_token_limit = excluded.tool_output_token_limit
            """,
            (
                model.provider_id,
                model.model,
                model.sandbox,
                model.reasoning_effort,
                model.context_window,
                model.tool_output_token_limit,
            ),
        )
        return _entity(
            Model,
            connection.execute("SELECT * FROM models WHERE model = ?", (model.model,)).fetchone(),
            _CONVERTERS,
        )


def get_model_by_id(model_id: int) -> Model | None:
    with connect() as connection:
        return _entity(
            Model,
            connection.execute("SELECT * FROM models WHERE id = ?", (model_id,)).fetchone(),
            _CONVERTERS,
        )


def get_model(model: str) -> Model | None:
    with connect() as connection:
        return _entity(
            Model,
            connection.execute("SELECT * FROM models WHERE model = ?", (model,)).fetchone(),
            _CONVERTERS,
        )
