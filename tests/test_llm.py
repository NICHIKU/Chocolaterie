import pytest

import llm


def test_normalize_usage_with_none():
    assert llm._normalize_usage(None) == (0, 0)


def test_normalize_usage_with_openai_usage_object():
    class Usage:
        prompt_tokens = 12
        completion_tokens = 7

    assert llm._normalize_usage(Usage()) == (12, 7)


def test_normalize_usage_with_partial_usage():
    class Usage:
        prompt_tokens = 3

    assert llm._normalize_usage(Usage()) == (3, 0)


def test_model_candidates_deduplicates_and_keeps_order():
    assert llm._model_candidates(llm.BIG_MODEL) == [llm.BIG_MODEL, llm.SMALL_MODEL]
    assert llm._model_candidates("autre") == ["autre", llm.BIG_MODEL, llm.SMALL_MODEL]
    assert llm._model_candidates(None) == [llm.BIG_MODEL, llm.SMALL_MODEL]


def test_format_error_falls_back_to_exception_class_name():
    assert llm._format_error(RuntimeError("")) == "RuntimeError"
    assert llm._format_error(ValueError("boom")) == "boom"


class FakeUsage:
    prompt_tokens = 21
    completion_tokens = 8


class FakeMessage:
    content = "Un coffret assorti."


class FakeChoice:
    message = FakeMessage()


class FakeResponse:
    choices = [FakeChoice()]
    usage = FakeUsage()


def make_fake_openai(monkeypatch, exc=None):
    """Remplace openai.OpenAI et renvoie la liste des appels create() effectués."""
    calls = []

    class FakeCompletions:
        def create(self, **kwargs):
            calls.append(kwargs)
            if exc is not None:
                raise exc
            return FakeResponse()

    class FakeChat:
        completions = FakeCompletions()

    class FakeClient:
        def __init__(self, **kwargs):
            self.init_kwargs = kwargs
            self.chat = FakeChat()

    monkeypatch.setattr("openai.OpenAI", FakeClient)
    return calls


def test_chat_success_returns_text_and_usage(monkeypatch):
    calls = make_fake_openai(monkeypatch)

    text, usage = llm.chat("llama3.2:3b", [{"role": "user", "content": "bonjour"}], max_tokens=42)

    assert text == "Un coffret assorti."
    assert usage == {
        "model": "llama3.2:3b",
        "prompt_tokens": 21,
        "completion_tokens": 8,
    }
    assert len(calls) == 1
    assert calls[0]["model"] == "llama3.2:3b"
    assert calls[0]["messages"] == [{"role": "user", "content": "bonjour"}]
    assert calls[0]["max_tokens"] == 42
    assert calls[0]["temperature"] == llm.DEFAULT_TEMPERATURE


def test_chat_propagates_provider_error(monkeypatch):
    make_fake_openai(monkeypatch, exc=RuntimeError("connexion refusée"))

    with pytest.raises(RuntimeError, match="connexion refusée"):
        llm.chat(llm.BIG_MODEL, [{"role": "user", "content": "bonjour"}])


def test_chat_simulated_failure(monkeypatch):
    calls = make_fake_openai(monkeypatch)
    monkeypatch.setattr(llm, "FAIL_RATE", 1.0)
    monkeypatch.setattr(llm, "RETRY_DELAY_SECONDS", 0)

    with pytest.raises(RuntimeError, match="Panne simulée"):
        llm.chat(llm.BIG_MODEL, [{"role": "user", "content": "bonjour"}])

    assert calls == []


def test_chat_no_simulated_failure_by_default(monkeypatch):
    monkeypatch.setattr(llm, "FAIL_RATE", 0.0)
    monkeypatch.setattr(llm, "EXTRA_LATENCY", 0.0)
    calls = make_fake_openai(monkeypatch)

    llm.chat(llm.BIG_MODEL, [{"role": "user", "content": "bonjour"}])

    assert len(calls) == 1
