"""Storage checks for chats, saved answers and feedback."""

import src.user_data as user_data

CHUNK = {"chunk_id": "test_1", "section": "5.C Retaking", "printed_page": 33,
         "pdf_page": 45, "text": "Complete passage."}


def db_file(tmp_path):
    return tmp_path / "user_data.sqlite"


def test_conversation_round_trip_preserves_chunks(tmp_path):
    db = db_file(tmp_path)
    chat_id = user_data.create_conversation("Retaking rules", db_path=db)
    user = {"role": "user", "content": "Can I retake?", "chunks": []}
    assistant = {"role": "assistant", "content": "Yes.", "chunks": [CHUNK], "id": "a1",
                 "question": "Can I retake?", "status": "answered", "evidence_source": "handbook"}
    user_data.append_message(chat_id, user, db_path=db)
    user_data.append_message(chat_id, assistant, db_path=db)

    messages = user_data.load_conversation(chat_id, db_path=db)
    assert len(messages) == 2
    assert messages[0]["content"] == "Can I retake?"
    assert messages[1]["chunks"] == [CHUNK]
    assert messages[1]["id"] == "a1"
    assert messages[1]["status"] == "answered"
    assert messages[1]["evidence_source"] == "handbook"

    listed = user_data.list_conversations(db_path=db)
    assert [c["id"] for c in listed] == [chat_id]
    assert listed[0]["title"] == "Retaking rules"

    user_data.rename_conversation(chat_id, "Renamed", db_path=db)
    assert user_data.list_conversations(db_path=db)[0]["title"] == "Renamed"
    user_data.delete_conversation(chat_id, db_path=db)
    assert user_data.list_conversations(db_path=db) == []
    assert user_data.load_conversation(chat_id, db_path=db) == []


def test_duplicate_save_returns_existing_id(tmp_path):
    db = db_file(tmp_path)
    first = user_data.save_answer("m1", "Q", "A", "answered", "handbook", [CHUNK], db_path=db)
    second = user_data.save_answer("m1", "Q2", "A2", "answered", "handbook", [], db_path=db)

    assert second == first
    saved = user_data.list_saved(db_path=db)
    assert len(saved) == 1
    assert saved[0]["question"] == "Q"
    assert saved[0]["sources"] == [CHUNK]
    assert user_data.is_saved("m1", db_path=db) == first
    assert user_data.is_saved("missing", db_path=db) is None


def test_rating_upsert_keeps_report_fields(tmp_path):
    db = db_file(tmp_path)
    user_data.set_rating("m1", -1, "Q", "A", ["test_1"], db_path=db)
    user_data.set_rating("m1", 1, "Q", "A", ["test_1"], db_path=db)
    assert user_data.get_rating("m1", db_path=db) == 1

    user_data.add_report("m1", "out of date", "old page", "Q", "A", ["test_1"], db_path=db)
    user_data.set_rating("m1", -1, "Q", "A", ["test_1"], db_path=db)

    feedback = user_data.list_feedback(db_path=db)
    ratings = [f for f in feedback if f["kind"] == "rating"]
    reports = [f for f in feedback if f["kind"] == "report"]
    assert len(ratings) == 1
    assert ratings[0]["rating"] == -1
    assert len(reports) == 1
    assert reports[0]["reason"] == "out of date"


def test_report_upserts_and_keeps_rating(tmp_path):
    db = db_file(tmp_path)
    user_data.set_rating("m2", 1, "Q", "A", ["test_1"], db_path=db)
    user_data.add_report("m2", "wrong fact", "page 3", "Q", "A", ["test_1", "test_2"], db_path=db)
    user_data.add_report("m2", "missing exception", "also page 4", "Q", "A", ["test_2"], db_path=db)

    feedback = user_data.list_feedback(db_path=db)
    reports = [f for f in feedback if f["kind"] == "report"]
    assert len(reports) == 1
    assert reports[0]["reason"] == "missing exception"
    assert reports[0]["chunk_ids"] == ["test_2"]
    assert user_data.get_rating("m2", db_path=db) == 1


def test_search_matches_titles_messages_and_notes(tmp_path):
    db = db_file(tmp_path)
    deferral = user_data.create_conversation("Deferral deadline", db_path=db)
    exams = user_data.create_conversation("Exam results", db_path=db)
    user_data.append_message(deferral, {"role": "user", "content": "When can I defer?"}, db_path=db)
    user_data.append_message(exams, {"role": "user", "content": "How do appeals work?"}, db_path=db)

    assert [c["id"] for c in user_data.list_conversations(search="appeals", db_path=db)] == [exams]
    assert [c["id"] for c in user_data.list_conversations(search="Deferral", db_path=db)] == [deferral]
    assert [c["id"] for c in user_data.list_conversations(db_path=db)] == [exams, deferral]

    fees = user_data.save_answer("m1", "Question one", "Answer about fees",
                                 "answered", "handbook", [], "first note", db_path=db)
    user_data.save_answer("m2", "Question two", "Answer about exams",
                          "answered", "handbook", [], "", db_path=db)
    assert [s["id"] for s in user_data.list_saved(search="fees", db_path=db)] == [fees]
    assert [s["id"] for s in user_data.list_saved(search="first note", db_path=db)] == [fees]


def test_remove_saved_and_update_note(tmp_path):
    db = db_file(tmp_path)
    first = user_data.save_answer("m1", "Q1", "A1", "answered", "handbook", [], db_path=db)
    second = user_data.save_answer("m2", "Q2", "A2", "answered", "handbook", [], "note", db_path=db)

    user_data.update_note(second, "updated", db_path=db)
    assert user_data.list_saved(db_path=db)[0]["note"] == "updated"

    user_data.remove_saved(first, db_path=db)
    assert [s["id"] for s in user_data.list_saved(db_path=db)] == [second]
    assert user_data.is_saved("m1", db_path=db) is None


def test_delete_all_clears_every_table(tmp_path):
    db = db_file(tmp_path)
    chat_id = user_data.create_conversation("Chat", db_path=db)
    user_data.append_message(chat_id, {"role": "user", "content": "Q"}, db_path=db)
    user_data.save_answer("m1", "Q", "A", "answered", "handbook", [CHUNK], db_path=db)
    user_data.set_rating("m1", 1, "Q", "A", ["test_1"], db_path=db)
    user_data.add_report("m1", "other", "", "Q", "A", [], db_path=db)

    user_data.delete_all(db_path=db)

    assert user_data.list_conversations(db_path=db) == []
    assert user_data.load_conversation(chat_id, db_path=db) == []
    assert user_data.list_saved(db_path=db) == []
    assert user_data.list_feedback(db_path=db) == []


def test_isolated_databases_and_env_fallback(tmp_path, monkeypatch):
    first = tmp_path / "first.sqlite"
    second = tmp_path / "second.sqlite"
    user_data.create_conversation("Only in first", db_path=first)
    assert [c["title"] for c in user_data.list_conversations(db_path=first)] == ["Only in first"]
    assert user_data.list_conversations(db_path=second) == []

    env_path = tmp_path / "env.sqlite"
    monkeypatch.setenv("USER_DATA_DB", str(env_path))
    user_data.create_conversation("From environment")
    assert env_path.exists()
    assert [c["title"] for c in user_data.list_conversations()] == ["From environment"]
    assert user_data.list_conversations(db_path=second) == []
