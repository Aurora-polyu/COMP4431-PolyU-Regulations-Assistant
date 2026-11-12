"""Local SQLite storage for chats, saved answers and feedback."""

import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = REPO_ROOT / "data" / "user_data.sqlite"

SCHEMA = """
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    message_id TEXT,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    chunks TEXT NOT NULL DEFAULT '[]',
    question TEXT,
    status TEXT,
    evidence_source TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX IF NOT EXISTS chat_messages_message_id
    ON chat_messages(message_id) WHERE message_id IS NOT NULL;
CREATE TABLE IF NOT EXISTS saved_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id TEXT NOT NULL UNIQUE,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    status TEXT,
    evidence_source TEXT,
    sources TEXT NOT NULL DEFAULT '[]',
    note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL CHECK (kind IN ('rating', 'report')),
    message_id TEXT NOT NULL,
    rating INTEGER,
    reason TEXT,
    comment TEXT,
    question TEXT,
    answer TEXT,
    chunk_ids TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX IF NOT EXISTS feedback_one_rating
    ON feedback(kind, message_id) WHERE kind = 'rating';
"""


def _resolve_path(db_path=None):
    if db_path:
        return Path(db_path)
    configured = os.environ.get("USER_DATA_DB")
    if configured:
        path = Path(configured)
        return path if path.is_absolute() else REPO_ROOT / path
    return DEFAULT_DB_PATH


@contextmanager
def _connection(db_path=None):
    path = _resolve_path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(SCHEMA)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(db_path=None):
    with _connection(db_path):
        pass


def create_conversation(title, db_path=None):
    with _connection(db_path) as conn:
        cursor = conn.execute("INSERT INTO conversations (title) VALUES (?)", (title,))
        return cursor.lastrowid


def append_message(conversation_id, message, db_path=None):
    with _connection(db_path) as conn:
        conn.execute(
            "INSERT INTO chat_messages "
            "(conversation_id, message_id, role, content, chunks, question, status, evidence_source) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                conversation_id,
                message.get("id"),
                message.get("role"),
                message.get("content", ""),
                json.dumps(message.get("chunks", [])),
                message.get("question"),
                message.get("status"),
                message.get("evidence_source"),
            ),
        )
        conn.execute(
            "UPDATE conversations SET updated_at = datetime('now') WHERE id = ?",
            (conversation_id,),
        )


def list_conversations(limit=15, search="", db_path=None):
    query = "SELECT id, title, created_at, updated_at FROM conversations"
    params = []
    if search:
        pattern = f"%{search}%"
        query += (" WHERE title LIKE ? OR EXISTS ("
                  "SELECT 1 FROM chat_messages "
                  "WHERE conversation_id = conversations.id AND content LIKE ?)")
        params.extend([pattern, pattern])
    query += " ORDER BY updated_at DESC, id DESC LIMIT ?"
    params.append(limit)
    with _connection(db_path) as conn:
        return [dict(row) for row in conn.execute(query, params)]


def load_conversation(conversation_id, db_path=None):
    with _connection(db_path) as conn:
        rows = conn.execute(
            "SELECT message_id, role, content, chunks, question, status, evidence_source "
            "FROM chat_messages WHERE conversation_id = ? ORDER BY id",
            (conversation_id,),
        ).fetchall()
    return [
        {
            "role": row["role"],
            "content": row["content"],
            "chunks": json.loads(row["chunks"] or "[]"),
            "id": row["message_id"],
            "question": row["question"],
            "status": row["status"],
            "evidence_source": row["evidence_source"],
        }
        for row in rows
    ]


def rename_conversation(conversation_id, title, db_path=None):
    with _connection(db_path) as conn:
        conn.execute(
            "UPDATE conversations SET title = ?, updated_at = datetime('now') WHERE id = ?",
            (title, conversation_id),
        )


def delete_conversation(conversation_id, db_path=None):
    with _connection(db_path) as conn:
        conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))


def delete_all(db_path=None):
    with _connection(db_path) as conn:
        conn.execute("DELETE FROM chat_messages")
        conn.execute("DELETE FROM conversations")
        conn.execute("DELETE FROM saved_answers")
        conn.execute("DELETE FROM feedback")


def save_answer(message_id, question, answer, status, evidence_source, sources, note="", db_path=None):
    with _connection(db_path) as conn:
        existing = conn.execute(
            "SELECT id FROM saved_answers WHERE message_id = ?", (message_id,)
        ).fetchone()
        if existing:
            return existing["id"]
        cursor = conn.execute(
            "INSERT INTO saved_answers "
            "(message_id, question, answer, status, evidence_source, sources, note) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (message_id, question, answer, status, evidence_source, json.dumps(sources), note),
        )
        return cursor.lastrowid


def is_saved(message_id, db_path=None):
    with _connection(db_path) as conn:
        row = conn.execute(
            "SELECT id FROM saved_answers WHERE message_id = ?", (message_id,)
        ).fetchone()
    return row["id"] if row else None


def list_saved(search="", db_path=None):
    query = "SELECT * FROM saved_answers"
    params = []
    if search:
        pattern = f"%{search}%"
        query += " WHERE question LIKE ? OR answer LIKE ? OR note LIKE ?"
        params = [pattern, pattern, pattern]
    query += " ORDER BY created_at DESC, id DESC"
    with _connection(db_path) as conn:
        rows = conn.execute(query, params).fetchall()
    items = []
    for row in rows:
        item = dict(row)
        item["sources"] = json.loads(item["sources"] or "[]")
        items.append(item)
    return items


def update_note(saved_id, note, db_path=None):
    with _connection(db_path) as conn:
        conn.execute("UPDATE saved_answers SET note = ? WHERE id = ?", (note, saved_id))


def remove_saved(saved_id, db_path=None):
    with _connection(db_path) as conn:
        conn.execute("DELETE FROM saved_answers WHERE id = ?", (saved_id,))


def set_rating(message_id, rating, question, answer, chunk_ids, db_path=None):
    with _connection(db_path) as conn:
        existing = conn.execute(
            "SELECT id FROM feedback WHERE kind = 'rating' AND message_id = ?",
            (message_id,),
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE feedback SET rating = ?, question = ?, answer = ?, chunk_ids = ? "
                "WHERE id = ?",
                (rating, question, answer, json.dumps(chunk_ids), existing["id"]),
            )
        else:
            conn.execute(
                "INSERT INTO feedback (kind, message_id, rating, question, answer, chunk_ids) "
                "VALUES ('rating', ?, ?, ?, ?, ?)",
                (message_id, rating, question, answer, json.dumps(chunk_ids)),
            )


def get_rating(message_id, db_path=None):
    with _connection(db_path) as conn:
        row = conn.execute(
            "SELECT rating FROM feedback WHERE kind = 'rating' AND message_id = ?",
            (message_id,),
        ).fetchone()
    return row["rating"] if row else None


def add_report(message_id, reason, comment, question, answer, chunk_ids, db_path=None):
    with _connection(db_path) as conn:
        existing = conn.execute(
            "SELECT id FROM feedback WHERE kind = 'report' AND message_id = ?",
            (message_id,),
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE feedback SET reason = ?, comment = ?, question = ?, answer = ?, "
                "chunk_ids = ? WHERE id = ?",
                (reason, comment, question, answer, json.dumps(chunk_ids), existing["id"]),
            )
        else:
            conn.execute(
                "INSERT INTO feedback (kind, message_id, reason, comment, question, answer, chunk_ids) "
                "VALUES ('report', ?, ?, ?, ?, ?, ?)",
                (message_id, reason, comment, question, answer, json.dumps(chunk_ids)),
            )


def list_feedback(db_path=None):
    with _connection(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM feedback ORDER BY created_at DESC, id DESC"
        ).fetchall()
    items = []
    for row in rows:
        item = dict(row)
        item["chunk_ids"] = json.loads(item["chunk_ids"] or "[]")
        items.append(item)
    return items
