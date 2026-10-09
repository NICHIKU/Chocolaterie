"""Aucune donnée utilisateur (prénom, email, allergies, tranche d'âge) ni en base, ni dans le navigateur."""

import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app as app_module

ROOT = Path(__file__).resolve().parents[1]
STORAGE_MARKERS = ["localStorage.", "sessionStorage.", "document.cookie", "indexedDB."]
PROFILE = {"name": "Léa", "email": "lea@example.com", "allergies": "noisettes", "children_ages": "7-10 ans"}


def page(name):
    return (ROOT / "static" / name).read_text(encoding="utf-8")


def tables(db_path="chocobot.db"):
    conn = sqlite3.connect(db_path)
    names = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    conn.close()
    return names


def test_chat_page_never_persists_anything_in_the_browser():
    html = page("index.html")
    for marker in STORAGE_MARKERS:
        assert marker not in html, f"{marker} ne doit pas apparaître dans index.html"
    assert "session_id" not in html
    assert "crypto.randomUUID" not in html


def test_admin_page_never_persists_anything_in_the_browser():
    html = page("admin.html")
    for marker in STORAGE_MARKERS:
        assert marker not in html, f"{marker} ne doit pas apparaître dans admin.html"


def test_profile_fields_are_sent_with_messages_only():
    html = page("index.html")
    assert "let profile = {}" in html
    assert 'post("/chat", {message: text, profile: profile})' in html
    for removed in ["/profile", "/chat/end"]:
        assert removed not in html, f"{removed} n'existe plus"


def test_chat_payload_has_no_session(monkeypatch):
    assert "session_id" not in app_module.ChatIn.model_fields

    captured = {}

    def fake_handle_chat(message, profile=None):
        captured.update(profile or {})
        return {"reply": "ok"}

    monkeypatch.setattr(app_module, "handle_chat", fake_handle_chat)

    reply = TestClient(app_module.app).post("/chat", json={"message": "bonjour", "profile": PROFILE}).json()

    assert reply == {"reply": "ok"}
    assert captured == PROFILE


def test_no_endpoint_saves_the_profile():
    client = TestClient(app_module.app)

    assert client.post("/profile", json=PROFILE).status_code == 404
    assert client.post("/chat/end", json={"session_id": "s1"}).status_code == 404


def test_the_database_holds_no_user_data():
    assert tables() & {"customers", "messages"} == set()
