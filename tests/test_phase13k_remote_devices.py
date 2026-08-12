
import pytest

import assistant.computer.remote_controller as controller
from assistant.computer.remote_auth import (
    sign_payload,
    verify_payload_signature,
)
from assistant.computer.remote_models import (
    RemoteDeviceDescriptor,
)
from assistant.computer.remote_registry import (
    get_remote_device,
    register_remote_device,
)


def test_hmac_signature_round_trip():
    payload = {
        "action": "window.focus",
        "target": "Notepad",
    }

    signature = sign_payload(
        payload,
        "test-secret",
    )

    assert verify_payload_signature(
        payload,
        signature,
        "test-secret",
    )

    assert not verify_payload_signature(
        payload,
        signature,
        "wrong-secret",
    )


def test_remote_registry_round_trip(
    tmp_path,
):
    registry = (
        tmp_path
        / "remote.json"
    )

    device = RemoteDeviceDescriptor(
        device_id="pi-node",
        name="Pi Node",
        kind="raspberry_pi",
        base_url="http://192.168.1.10:8765",
        capabilities=[
            "camera.capture",
        ],
        trusted=True,
    )

    register_remote_device(
        device,
        path=registry,
    )

    loaded = get_remote_device(
        "pi-node",
        path=registry,
    )

    assert loaded is not None
    assert loaded.name == "Pi Node"
    assert loaded.trusted is True


def test_untrusted_remote_device_cannot_execute(
    tmp_path,
):
    registry = (
        tmp_path
        / "remote.json"
    )

    register_remote_device(
        RemoteDeviceDescriptor(
            device_id="phone",
            name="Phone",
            kind="phone",
            base_url="http://127.0.0.1:8765",
            trusted=False,
        ),
        path=registry,
    )

    with pytest.raises(PermissionError):
        controller.execute_remote_device_action(
            "phone",
            "window.focus",
            target="Notepad",
            secret="test",
            registry_path=registry,
        )


def test_remote_capability_must_be_advertised(
    tmp_path,
):
    registry = (
        tmp_path
        / "remote.json"
    )

    register_remote_device(
        RemoteDeviceDescriptor(
            device_id="pi-node",
            name="Pi Node",
            kind="raspberry_pi",
            base_url="http://127.0.0.1:8765",
            capabilities=[
                "camera.capture",
            ],
            trusted=True,
        ),
        path=registry,
    )

    with pytest.raises(PermissionError):
        controller.execute_remote_device_action(
            "pi-node",
            "filesystem.delete",
            target="x",
            approved=True,
            secret="test",
            registry_path=registry,
        )


def test_remote_action_uses_signed_transport(
    tmp_path,
    monkeypatch,
):
    registry = (
        tmp_path
        / "remote.json"
    )

    register_remote_device(
        RemoteDeviceDescriptor(
            device_id="server",
            name="Home Server",
            kind="server",
            base_url="http://10.0.0.5:8765",
            capabilities=[
                "window.focus",
            ],
            trusted=True,
        ),
        path=registry,
    )

    seen = {}

    def fake_post(
        base_url,
        path,
        payload,
        *,
        secret,
        timeout,
    ):
        seen["base_url"] = base_url
        seen["path"] = path
        seen["payload"] = payload
        seen["secret"] = secret

        return {
            "success": True,
            "verified": True,
            "result": {
                "ok": True,
            },
        }

    monkeypatch.setattr(
        controller,
        "post_signed_json",
        fake_post,
    )

    result = controller.execute_remote_device_action(
        "server",
        "window.focus",
        target="Notepad",
        secret="shared-secret",
        registry_path=registry,
    )

    assert result["success"] is True
    assert result["verified"] is True
    assert seen["path"] == "/evie/v1/action"
    assert seen["secret"] == "shared-secret"
