
from assistant.voice.runtime_state import (
    VoiceRuntimeMode,
    VoiceRuntimeState,
)


def test_runtime_modes():
    state = VoiceRuntimeState()

    assert state.mode == VoiceRuntimeMode.ACTIVE

    state.set_mode(
        VoiceRuntimeMode.STANDBY
    )

    assert state.mode == VoiceRuntimeMode.STANDBY
