import json

import pytest

import chatbot
import db
import llm


class FakeStore:
    """Remplace db : garde en mémoire ce que le chatbot lui demande."""

    def __init__(self, customer=None, history=None):
        self.customer = customer or {}
        self.history = history or []
        self.saved = []
        self.cleared = []

    def save_message(self, session_id, role, content):
        self.saved.append((session_id, role, content))

    def get_customer(self, session_id):
        return dict(self.customer)

    def get_history(self, session_id):
        return list(self.history)

    def clear_history(self, session_id):
        self.cleared.append(session_id)


@pytest.fixture()
def store(monkeypatch):
    fake = FakeStore()
    for name in ["save_message", "get_customer", "get_history", "clear_history"]:
        monkeypatch.setattr(db, name, getattr(fake, name))
    return fake


def fake_llm(monkeypatch, reply="Voici un coffret.", exc=None):
    """Remplace llm.chat et renvoie la liste des appels reçus."""
    calls = []

    def chat(model, messages, max_tokens=1500):
        calls.append({"model": model, "messages": messages, "max_tokens": max_tokens})
        if exc is not None:
            raise exc
        return reply, {}

    monkeypatch.setattr(llm, "chat", chat)
    return calls


def test_customer_context_without_any_information():
    assert chatbot.customer_context({}) == "\n\nInformations enregistrées sur le client : aucune."
    assert chatbot.customer_context({"name": "", "email": None}) == (
        "\n\nInformations enregistrées sur le client : aucune."
    )


def test_customer_context_lists_only_filled_fields():
    context = chatbot.customer_context({"name": "Léa", "allergies": "noisettes"})

    assert "- Nom : Léa" in context
    assert "- Allergies : noisettes" in context
    assert "- Email" not in context
    assert "- Âge des enfants" not in context
    assert context.splitlines()[-1].startswith("Appelle le client par son prénom")


def test_customer_context_with_all_fields():
    context = chatbot.customer_context(
        {
            "name": "Léa",
            "email": "lea@example.com",
            "allergies": "noisettes",
            "children_ages": "6 et 9 ans",
        }
    )

    assert "- Email : lea@example.com" in context
    assert "- Âge des enfants : 6 et 9 ans" in context


def test_system_prompt_contains_the_catalogue():
    assert "Maison Delcourt" in chatbot.SYSTEM_PROMPT
    assert "coffret" in chatbot.SYSTEM_PROMPT
    assert chatbot.SYSTEM_PROMPT.endswith(json.dumps(chatbot.CATALOG, ensure_ascii=False))


def test_handle_chat_saves_user_message_then_assistant_reply(store, monkeypatch):
    calls = fake_llm(monkeypatch, reply="Voici un coffret.")

    assert chatbot.handle_chat("s1", "Un coffret pour un enfant ?") == {
        "reply": "Voici un coffret."
    }
    assert store.saved == [
        ("s1", "user", "Un coffret pour un enfant ?"),
        ("s1", "assistant", "Voici un coffret."),
    ]
    assert len(calls) == 1
    assert calls[0]["model"] == llm.BIG_MODEL
    assert calls[0]["max_tokens"] == 1500


def test_handle_chat_sends_system_prompt_and_history_to_llm(store, monkeypatch):
    store.customer = {"name": "Léa", "allergies": "noisettes"}
    store.history = [
        {"role": "user", "content": "question précédente"},
        {"role": "assistant", "content": "réponse précédente"},
    ]
    calls = fake_llm(monkeypatch)

    chatbot.handle_chat("s1", "et maintenant ?")

    messages = calls[0]["messages"]
    assert messages[0]["role"] == "system"
    assert messages[0]["content"].startswith(chatbot.SYSTEM_PROMPT)
    assert "- Nom : Léa" in messages[0]["content"]
    assert "- Allergies : noisettes" in messages[0]["content"]
    assert messages[1:] == store.history


def test_handle_chat_without_customer_uses_empty_context(store, monkeypatch):
    calls = fake_llm(monkeypatch)

    chatbot.handle_chat("s1", "bonjour")

    assert "Informations enregistrées sur le client : aucune." in calls[0]["messages"][0]["content"]


def test_handle_chat_falls_back_when_llm_fails(store, monkeypatch):
    fake_llm(monkeypatch, exc=RuntimeError("Ollama arrêté"))

    assert chatbot.handle_chat("s1", "Bonjour") == {
        "reply": "Désolé, une erreur est survenue. Réessayez plus tard."
    }
    assert store.saved[0] == ("s1", "user", "Bonjour")
    assert store.saved[1][0] == "s1"
    assert store.saved[1][1] == "assistant"
    assert "erreur" in store.saved[1][2]


@pytest.mark.parametrize("exc", [ZeroDivisionError("div par zéro"), ValueError("")])
def test_handle_chat_falls_back_on_any_exception(store, monkeypatch, exc):
    fake_llm(monkeypatch, exc=exc)

    assert "erreur" in chatbot.handle_chat("s1", "salut")["reply"]
