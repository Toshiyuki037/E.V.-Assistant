from assistant.voice.authoritative_reasoning import ResponseSentenceAccumulator


def test_sentence_accumulator_emits_complete_sentences():
    accumulator = ResponseSentenceAccumulator()

    assert accumulator.add("A transistor is") == []

    assert accumulator.add(
        " a switch. It controls"
    ) == [
        "A transistor is a switch."
    ]

    assert accumulator.add(
        " current."
    ) == [
        "It controls current."
    ]


def test_sentence_accumulator_flushes_tail():
    accumulator = ResponseSentenceAccumulator()

    accumulator.add(
        "Short trailing response"
    )

    assert accumulator.flush() == "Short trailing response"
