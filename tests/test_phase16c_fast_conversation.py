from assistant.performance.conversation_fastpath import handle_fast_conversation

def test_social_fast_path():
    assert handle_fast_conversation("Thank you.").handled is True
    assert handle_fast_conversation("EV, good afternoon.").handled is True
    assert handle_fast_conversation("What is a transistor?").handled is False
