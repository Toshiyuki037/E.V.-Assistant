
from assistant.voice.conversation_state import VoiceConversationState


def test_go_back_is_safe():
    state = VoiceConversationState()

    state.remember_prompt("Show my calendar.")
    state.remember_prompt("Send an email.")

    prompt = state.safe_go_back_prompt()

    assert "Show my calendar." in prompt
    assert "do not repeat or re-execute" in prompt.lower()


def test_frequency_learning():
    state = VoiceConversationState()

    state.remember_prompt("What's on my calendar?")
    state.remember_prompt("What's on my calendar?")

    assert state.most_frequent_requests(1)[0][1] == 2
