from assistant.voice.low_latency import prepare_low_latency_chunks

def test_first_chunk_one_sentence_then_pairs():
    assert prepare_low_latency_chunks(
        ["One. Two.", "Three. Four.", "Five."]
    ) == ["One.", "Two. Three.", "Four. Five."]
