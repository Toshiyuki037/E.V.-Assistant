from assistant.coding.request_planner import (
    plan_coding_request,
)


def test_normal_phase13_task_not_claimed_by_self_engineering():
    request = plan_coding_request(
        (
            "Open Notepad, write "
            "\"E.V.I.E. Phase 13 complete\", "
            "save it as EVIE-Phase13-Test.txt "
            "on my Desktop, close Notepad, "
            "open File Explorer, and verify "
            "that the file exists."
        )
    )

    assert request.handled is False


def test_evie_name_does_not_imply_repository():
    request = plan_coding_request(
        "Write E.V.I.E. into Notepad."
    )

    assert request.handled is False


def test_test_in_filename_does_not_trigger_self_engineering():
    request = plan_coding_request(
        "Open EVIE-Phase13-Test.txt."
    )

    assert request.handled is False


def test_verify_file_does_not_trigger_self_engineering():
    request = plan_coding_request(
        "Verify that EVIE-Phase13-Test.txt exists."
    )

    assert request.handled is False


def test_explicit_repository_fix_is_self_engineering():
    request = plan_coding_request(
        "Fix your repository routing logic."
    )

    assert request.handled is True
    assert request.action == "plan_change"


def test_explicit_code_diagnosis_is_self_engineering():
    request = plan_coding_request(
        "Diagnose your own code and propose a fix."
    )

    assert request.handled is True
    assert request.action == "plan_change"


def test_assistant_word_alone_does_not_trigger_self_engineering():
    request = plan_coding_request(
        "Create a file called assistant-notes.txt."
    )

    assert request.handled is False