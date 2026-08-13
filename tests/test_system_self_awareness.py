from assistant.system.self_awareness import (
    get_capability_status,
    get_self_awareness,
    get_version,
)


def test_version_awareness():
    result = (
        get_version()
    )

    assert result.success is True
    assert result.topic == "version"
    assert "1.0.0" in result.summary
    assert result.source == "manifest"


def test_identity_awareness():
    result = (
        get_self_awareness(
            "identity"
        )
    )

    assert result.success is True
    assert result.data["name"] == "E.V.I.E."
    assert result.data["current_phase"] == 15


def test_capability_truth():
    result = (
        get_capability_status(
            "computer control"
        )
    )

    assert result.success is True
    assert result.data["supported"] is True


def test_future_capability_truth():
    result = (
        get_capability_status(
            "multi device"
        )
    )

    assert result.success is True
    assert result.data["supported"] is False


def test_unknown_capability_fails_closed():
    result = (
        get_capability_status(
            "teleportation"
        )
    )

    assert result.success is False


def test_unknown_topic_fails_closed():
    result = (
        get_self_awareness(
            "something invented"
        )
    )

    assert result.success is False


def test_capabilities_are_manifest_backed():
    result = (
        get_self_awareness(
            "capabilities"
        )
    )

    assert result.success is True
    assert "memory" in result.data["capabilities"]
    assert "multi_device" not in result.data["capabilities"]


def test_limitations_are_available():
    result = (
        get_self_awareness(
            "limitations"
        )
    )

    assert result.success is True
    assert isinstance(
        result.data["limitations"],
        list,
    )
