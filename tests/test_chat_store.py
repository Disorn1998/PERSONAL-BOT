"""SQLite chat store including partial saves."""

from __future__ import annotations

from pathlib import Path

from persona_bot.chat_store import ChatStore


def test_thread_and_partial_message(tmp_path: Path) -> None:
    store = ChatStore(tmp_path / "chat.sqlite3")
    thread = store.create_thread(persona_id="study-buddy", title="t1")
    user = store.add_message(thread_id=thread.id, role="user", content="สวัสดี")
    assert user.role == "user"
    assistant = store.add_message(
        thread_id=thread.id, role="assistant", content="สวัสดี", partial=True
    )
    store.update_message(assistant.id, content="สวัสดี ครับ", partial=False)
    msgs = store.list_messages(thread.id)
    assert len(msgs) == 2
    assert msgs[1].content == "สวัสดี ครับ"
    assert msgs[1].partial is False
    hist = store.history_for_prompt(thread.id)
    assert hist[0]["role"] == "user"
    store.clear_thread_messages(thread.id)
    assert store.list_messages(thread.id) == []
    store.close()


def test_list_threads_filter(tmp_path: Path) -> None:
    store = ChatStore(tmp_path / "chat.sqlite3")
    store.create_thread(persona_id="a", title="1")
    store.create_thread(persona_id="b", title="2")
    assert len(store.list_threads(persona_id="a")) == 1
    store.close()
