"""
E.V.I.E. - Safe Windows Settings Navigation

Phase 13E

Only allowlisted Windows Settings URIs may be opened.
No arbitrary URI or command execution is accepted.
"""

from __future__ import annotations

import os
import sys


IS_WINDOWS = sys.platform == "win32"


SAFE_SETTINGS_PAGES = {
    "system": "ms-settings:system",
    "display": "ms-settings:display",
    "sound": "ms-settings:sound",
    "notifications": "ms-settings:notifications",
    "power": "ms-settings:powersleep",
    "storage": "ms-settings:storagesense",
    "bluetooth": "ms-settings:bluetooth",
    "devices": "ms-settings:connecteddevices",
    "network": "ms-settings:network",
    "wifi": "ms-settings:network-wifi",
    "ethernet": "ms-settings:network-ethernet",
    "vpn": "ms-settings:network-vpn",
    "airplane_mode": "ms-settings:network-airplanemode",
    "personalization": "ms-settings:personalization",
    "apps": "ms-settings:appsfeatures",
    "startup_apps": "ms-settings:startupapps",
    "privacy": "ms-settings:privacy",
    "camera_privacy": "ms-settings:privacy-webcam",
    "microphone_privacy": "ms-settings:privacy-microphone",
    "windows_update": "ms-settings:windowsupdate",
}


class SettingsBackendUnavailable(RuntimeError):
    pass


def list_safe_settings_pages() -> dict[str, str]:
    return dict(
        SAFE_SETTINGS_PAGES
    )


def resolve_settings_page(
    page: str,
) -> str:
    key = str(
        page
        or ""
    ).strip().lower()

    key = key.replace(
        " ",
        "_",
    )

    if key not in SAFE_SETTINGS_PAGES:
        raise ValueError(
            (
                "Unknown or non-allowlisted Windows settings page: "
                f"{page}"
            )
        )

    return SAFE_SETTINGS_PAGES[
        key
    ]


def open_settings_page(
    page: str,
) -> dict:
    if not IS_WINDOWS:
        raise SettingsBackendUnavailable(
            "Windows Settings integration is only available on Windows."
        )

    uri = resolve_settings_page(
        page
    )

    os.startfile(
        uri
    )

    return {
        "page": str(page),
        "uri": uri,
        "success": True,
    }
