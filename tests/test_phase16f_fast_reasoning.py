from types import SimpleNamespace

import assistant.voice.fast_reasoning as fast_reasoning


class FakeResponses:
    def create(
        self,
        **kwargs,
    ):
        assert kwargs["model"]
        assert kwargs["stream"] is True
        assert kwargs["reasoning"]["effort"] == "none"

        return [
            SimpleNamespace(
                type="response.output_text.delta",
                delta="A transistor controls electrical current. ",
            ),
            SimpleNamespace(
                type="response.output_text.delta",
                delta="It can act as a switch or amplifier.",
            ),
            SimpleNamespace(
                type="response.completed",
            ),
        ]


class FakeClient:
    responses = FakeResponses()


def test_fast_stream_emits_sentences_and_returns_full_text(
    monkeypatch,
):
    fast_reasoning._CACHE.clear()

    monkeypatch.setattr(
        fast_reasoning,
        "get_fast_client",
        lambda:
            FakeClient(),
    )

    sentences = []

    response = (
        fast_reasoning
        .stream_fast_authoritative_chat(
            "What is a transistor?",
            on_sentence=
                sentences.append,
        )
    )

    assert response == (
        "A transistor controls electrical current. "
        "It can act as a switch or amplifier."
    )

    assert sentences == [
        "A transistor controls electrical current.",
        "It can act as a switch or amplifier.",
    ]


def test_second_identical_request_uses_cache(
    monkeypatch,
):
    fast_reasoning._CACHE.clear()

    calls = {
        "count":
            0,
    }

    def get_client():
        calls[
            "count"
        ] += 1

        return FakeClient()

    monkeypatch.setattr(
        fast_reasoning,
        "get_fast_client",
        get_client,
    )

    first = (
        fast_reasoning
        .stream_fast_authoritative_chat(
            "Define a resistor.",
        )
    )

    second_sentences = []

    second = (
        fast_reasoning
        .stream_fast_authoritative_chat(
            "Define a resistor.",
            on_sentence=
                second_sentences.append,
        )
    )

    assert first == second
    assert calls["count"] == 1
    assert second_sentences
