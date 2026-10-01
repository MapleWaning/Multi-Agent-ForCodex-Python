"""读写 providers。"""
from multi_agent.models import Provider
from multi_agent.storage.sqlite_store import _entity, connect


def save_provider(provider: Provider) -> Provider:
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO providers (id, name, base_url, wire_api, env_key)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                base_url = excluded.base_url,
                wire_api = excluded.wire_api,
                env_key = excluded.env_key
            """,
            (provider.id, provider.name, provider.base_url, provider.wire_api, provider.env_key),
        )
        return _entity(
            Provider,
            connection.execute("SELECT * FROM providers WHERE id = ?", (provider.id,)).fetchone(),
        )


def get_provider(provider_id: str) -> Provider | None:
    with connect() as connection:
        return _entity(
            Provider,
            connection.execute("SELECT * FROM providers WHERE id = ?", (provider_id,)).fetchone(),
        )
