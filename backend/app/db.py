import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from app.core.config import settings


def db_path() -> Path:
    path = Path(settings.database_path)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[2] / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            create table if not exists knowledge_chunks (
                id integer primary key autoincrement,
                role text not null,
                source text not null,
                title text not null,
                text text not null,
                embedding text not null,
                created_at text default current_timestamp
            );

            create table if not exists sessions (
                id text primary key,
                role text not null,
                resume_text text not null,
                profile_json text not null,
                status text not null,
                created_at text default current_timestamp,
                updated_at text default current_timestamp
            );

            create table if not exists interactions (
                id integer primary key autoincrement,
                session_id text not null,
                question text not null,
                answer text,
                context_json text not null,
                feedback_json text,
                created_at text default current_timestamp,
                answered_at text,
                foreign key(session_id) references sessions(id)
            );
            """
        )


def row_to_dict(row: sqlite3.Row) -> dict:
    data = dict(row)
    for key in ("profile_json", "context_json", "feedback_json"):
        if key in data and data[key]:
            data[key.replace("_json", "")] = json.loads(data.pop(key))
    return data

