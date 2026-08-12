from assistant.telemetry.progress import ProgressEvent, ProgressReporter, progress_message_for_step

def test_emit():
    events = []
    reporter = ProgressReporter(emit=events.append, minimum_interval=0)
    assert reporter.report("Working.") is True
    assert len(events) == 1
    assert isinstance(events[0], ProgressEvent)

def test_duplicate():
    events = []
    reporter = ProgressReporter(emit=events.append, minimum_interval=0)
    assert reporter.report("Working.") is True
    assert reporter.report("Working.") is False

def test_step_messages():
    assert progress_message_for_step("Run tests", "run_python") == "I'm running that now."
    assert progress_message_for_step("Locate project", "search_filesystem") == "I'm checking the files now."
