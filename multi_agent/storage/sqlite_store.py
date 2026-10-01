"""打开 SQLite，并建好表。

不读写某一张具体的表。
"""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from multi_agent.storage.table import TableSQL


def initialize(connection: sqlite3.Connection) -> None:
    connection.executescript(TableSQL)


@contextmanager
def connect(db_path: Path | None = None):
    path = db_path or Path(".multi_agent") / "multi_agent.db"
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        initialize(connection)
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _row(row: sqlite3.Row | None) -> dict | None:
    if row is None:
        return None
    return dict(row)


def _entity(cls, row: sqlite3.Row | None, converters: dict | None = None):
    data = _row(row)
    if data is None:
        return None
    for key, convert in (converters or {}).items():
        if data.get(key) is not None:
            data[key] = convert(data[key])
    names = cls.__dataclass_fields__
    return cls(**{key: data[key] for key in names if key in data})


def _entities(cls, rows: list[sqlite3.Row], converters: dict | None = None) -> list:
    return [_entity(cls, row, converters) for row in rows]
