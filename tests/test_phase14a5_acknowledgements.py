from assistant.voice.acknowledgements import ACK_FILES, acknowledgement_path, available_acknowledgements

def test_contract():
    assert "on_it" in ACK_FILES
    assert "checking" in ACK_FILES
    assert "working" in ACK_FILES

def test_path():
    path = acknowledgement_path("on_it")
    assert path.name == "on_it.wav"
    assert path.parent.name == "voice_cache"
    assert path.parent.parent.name == "runtime"

def test_available_type():
    assert isinstance(available_acknowledgements(), list)
