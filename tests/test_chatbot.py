import json

import pytest

import chatbot
import db
import llm


class FakeStore:
    """Remplace db.get_customer : renvoie la fiche client programmée."""

    def __init__(self, customer=None):
        self.customer = customer or {}

    def get_customer(self, session_id):
        return dict(self.customer)


@pytest.fixture(autouse=True)
def empty_sessions():
    chatbot._sessions.clear()
    yield
    chatbot._sessions.clear()


@pytest.fixture()
def store(monkeypatch):
    fake = FakeStore()
    monkeypatch.setattr(db, "get_customer", fake.get_customer)
    return fake


FALLBACK_REPLY = "Désolé, je n'ai pas pu répondre. Pouvez-vous reformuler votre demande ?"


def fake_llm(monkeypatch, reply="Voici un coffret.", exc=None):
    """Remplace llm.chat et renvoie la liste des appels reçus."""
    calls = []

    def chat(model, messages, max_tokens=1500, temperature=None):
        calls.append({"model": model, "messages": messages, "max_tokens": max_tokens})
        if exc is not None:
            raise exc
        if max_tokens == 5:
            return "OUI", {}
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
    assert "- Tranche d'âge" not in context
    assert context.splitlines()[-1].startswith("Appelle le client par son prénom")


def test_customer_context_with_all_fields():
    context = chatbot.customer_context(
        {
            "name": "Léa",
            "email": "lea@example.com",
            "allergies": "noisettes",
            "children_ages": "7-10 ans",
        }
    )

    assert "- Email : lea@example.com" in context
    assert "- Tranche d'âge des enfants : 7-10 ans" in context


def test_system_prompt_contains_the_catalogue():
    assert "Maison Delcourt" in chatbot.SYSTEM_PROMPT
    assert "coffret" in chatbot.SYSTEM_PROMPT
    assert chatbot.SYSTEM_PROMPT.endswith(json.dumps(chatbot.CATALOG, ensure_ascii=False))


def test_handle_chat_saves_user_message_then_assistant_reply(store, monkeypatch):
    calls = fake_llm(monkeypatch, reply="Voici un coffret.")

    assert chatbot.handle_chat("s1", "Un coffret pour un enfant ?") == {
        "reply": "Voici un coffret."
    }
    assert chatbot.get_history("s1") == [
        {"role": "user", "content": "Un coffret pour un enfant ?"},
        {"role": "assistant", "content": "Voici un coffret."},
    ]
    assert len(calls) == 1
    assert calls[0]["model"] == llm.BIG_MODEL
    assert calls[0]["max_tokens"] == 1500


def test_handle_chat_sends_system_prompt_and_history_to_llm(store, monkeypatch):
    store.customer = {"name": "Léa", "allergies": "noisettes"}
    chatbot.save_message("s1", "user", "question précédente")
    chatbot.save_message("s1", "assistant", "réponse précédente")
    calls = fake_llm(monkeypatch)

    chatbot.handle_chat("s1", "et maintenant ?")

    messages = calls[-1]["messages"]
    assert messages[0]["role"] == "system"
    assert messages[0]["content"].startswith(chatbot.SYSTEM_PROMPT)
    assert "- Nom : Léa" in messages[0]["content"]
    assert "- Allergies : noisettes" in messages[0]["content"]
    assert messages[1:3] == [
        {"role": "user", "content": "question précédente"},
        {"role": "assistant", "content": "réponse précédente"},
    ]
    assert messages[3]["role"] == "user"
    assert messages[3]["content"].startswith("et maintenant ?")
    assert chatbot.REMINDER in messages[3]["content"]


def test_handle_chat_without_customer_uses_empty_context(store, monkeypatch):
    calls = fake_llm(monkeypatch)

    chatbot.handle_chat("s1", "bonjour")

    assert "Informations enregistrées sur le client : aucune." in calls[0]["messages"][0]["content"]


def test_handle_chat_falls_back_when_llm_fails(store, monkeypatch):
    fake_llm(monkeypatch, exc=RuntimeError("Ollama arrêté"))

    assert chatbot.handle_chat("s1", "Bonjour") == {"reply": FALLBACK_REPLY}
    assert chatbot.get_history("s1") == [{"role": "user", "content": "Bonjour"}]


@pytest.mark.parametrize("exc", [ZeroDivisionError("div par zéro"), ValueError("")])
def test_handle_chat_falls_back_on_any_exception(store, monkeypatch, exc):
    fake_llm(monkeypatch, exc=exc)

    assert chatbot.handle_chat("s1", "salut") == {"reply": FALLBACK_REPLY}
    assert chatbot.get_history("s1") == [{"role": "user", "content": "salut"}]


def test_clear_history_forgets_the_session():
    chatbot.save_message("s1", "user", "bonjour")

    chatbot.clear_history("s1")

    assert chatbot.get_history("s1") == []
    assert "s1" not in chatbot._sessions


def test_stale_sessions_are_forgotten_automatically():
    chatbot.save_message("s1", "user", "bonjour")
    chatbot._sessions["s1"]["ts"] -= chatbot.HISTORY_TTL + 1

    assert chatbot.get_history("s1") == []
    assert "s1" not in chatbot._sessions
