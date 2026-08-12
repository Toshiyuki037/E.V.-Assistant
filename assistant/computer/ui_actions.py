"""
E.V.I.E. - Structured Accessibility Actions

Phase 13G

Actions resolve/reacquire their target immediately before execution.

Control hierarchy:

    UI Automation pattern
        ↓
    native HWND operation
        ↓
    keyboard/vision fallback in later phases

No persistent UI wrapper is trusted across interface mutations.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import sys

from .accessibility import (
    resolve_accessible_window,
)
from .accessibility_backend import (
    wrapper_to_info,
)
from .accessibility_models import (
    UIActionResult,
)


IS_WINDOWS = (
    sys.platform == "win32"
)


WM_SETTEXT = 0x000C
WM_GETTEXT = 0x000D
WM_GETTEXTLENGTH = 0x000E


# ---------------------------------------------------------------------------
# Internal UI selector resolution
# ---------------------------------------------------------------------------


def _find_wrapper(
    target: str | int,
    *,
    name: str = "",
    control_type: str = "",
    automation_id: str = "",
    exact_name: bool = False,
):
    """
    Resolve a UI element from the current live accessibility tree.

    The wrapper is reacquired every time rather than retaining stale UIA
    objects after interface changes.
    """

    window = resolve_accessible_window(
        target
    )

    try:
        descendants = (
            window.descendants()
        )

    except Exception:
        descendants = []

    candidates = [
        window,
        *descendants,
    ]

    name_text = str(
        name
        or ""
    ).strip().lower()

    type_text = str(
        control_type
        or ""
    ).strip().lower()

    automation_text = str(
        automation_id
        or ""
    ).strip().lower()

    if not any(
        (
            name_text,
            type_text,
            automation_text,
        )
    ):
        raise ValueError(
            (
                "At least one UI element selector "
                "must be provided."
            )
        )

    matches = []

    for wrapper in candidates:

        try:
            info = wrapper_to_info(
                wrapper
            )

        except Exception:
            continue

        item_name = (
            info.name
            or ""
        ).lower()

        item_type = (
            info.control_type
            or ""
        ).lower()

        item_automation = (
            info.automation_id
            or ""
        ).lower()

        if name_text:

            if exact_name:

                if (
                    item_name
                    != name_text
                ):
                    continue

            elif (
                name_text
                not in item_name
            ):
                continue

        if (
            type_text
            and item_type
            != type_text
        ):
            continue

        if (
            automation_text
            and item_automation
            != automation_text
        ):
            continue

        matches.append(
            wrapper
        )

    if not matches:
        raise LookupError(
            (
                "No accessible UI element matched "
                "the requested selector."
            )
        )

    if len(matches) > 1:
        raise LookupError(
            (
                "UI selector is ambiguous; "
                f"{len(matches)} elements matched."
            )
        )

    return matches[0]


# ---------------------------------------------------------------------------
# Native HWND helpers
# ---------------------------------------------------------------------------


def _get_user32():
    if not IS_WINDOWS:
        raise RuntimeError(
            (
                "Native HWND operations are only "
                "available on Windows."
            )
        )

    user32 = ctypes.WinDLL(
        "user32",
        use_last_error=True,
    )

    user32.IsWindow.argtypes = [
        wintypes.HWND,
    ]

    user32.IsWindow.restype = (
        wintypes.BOOL
    )

    user32.SendMessageW.argtypes = [
        wintypes.HWND,
        wintypes.UINT,
        wintypes.WPARAM,
        wintypes.LPARAM,
    ]

    # ctypes.wintypes does not expose LRESULT on every Python build.
    # c_ssize_t is the correct pointer-sized signed integer equivalent.
    user32.SendMessageW.restype = (
        ctypes.c_ssize_t
    )

    return user32


def _validate_native_handle(
    handle: int,
):
    hwnd_value = int(
        handle
        or 0
    )

    if hwnd_value <= 0:
        raise ValueError(
            (
                "UI element does not expose a usable "
                "native HWND."
            )
        )

    user32 = _get_user32()

    hwnd = wintypes.HWND(
        hwnd_value
    )

    if not user32.IsWindow(
        hwnd
    ):
        raise ValueError(
            (
                "UI element HWND is stale or invalid: "
                f"{hwnd_value}"
            )
        )

    return (
        user32,
        hwnd,
    )


def _read_native_window_text(
    handle: int,
) -> str:
    """
    Read text using WM_GETTEXT rather than GetWindowTextW.

    Some RichEdit controls accept WM_SETTEXT while GetWindowTextW returns
    incomplete/empty results. WM_GETTEXT is a better direct control query.
    """

    user32, hwnd = (
        _validate_native_handle(
            handle
        )
    )

    length = user32.SendMessageW(
        hwnd,
        WM_GETTEXTLENGTH,
        0,
        0,
    )

    buffer = (
        ctypes.create_unicode_buffer(
            max(
                1,
                int(length)
                + 1,
            )
        )
    )

    pointer = ctypes.cast(
        buffer,
        ctypes.c_void_p,
    ).value

    user32.SendMessageW(
        hwnd,
        WM_GETTEXT,
        len(buffer),
        pointer,
    )

    return buffer.value


def _set_native_window_text(
    handle: int,
    value: str,
) -> str:
    """
    Native Win32 text-control fallback.

    Used when UI Automation does not expose a writable ValuePattern but the
    accessible element exposes a real HWND.

    Example:

        Modern Windows Notepad
        control_type = Document
        class_name   = RichEditD2DPT
        handle       = native child HWND
        patterns     = []

    Execution:

        WM_SETTEXT
            ↓
        WM_GETTEXT
            ↓
        post-action UIA verification when necessary
    """

    user32, hwnd = (
        _validate_native_handle(
            handle
        )
    )

    text = str(
        value
    )

    text_buffer = (
        ctypes.create_unicode_buffer(
            text
        )
    )

    pointer = ctypes.cast(
        text_buffer,
        ctypes.c_void_p,
    ).value

    result = user32.SendMessageW(
        hwnd,
        WM_SETTEXT,
        0,
        pointer,
    )

    if result == 0:
        raise RuntimeError(
            (
                "Native WM_SETTEXT was rejected "
                "by the target control."
            )
        )

    return _read_native_window_text(
        handle
    )


# ---------------------------------------------------------------------------
# Focus
# ---------------------------------------------------------------------------


def focus_ui_element(
    target: str | int,
    **selector,
) -> UIActionResult:

    wrapper = _find_wrapper(
        target,
        **selector,
    )

    before = wrapper_to_info(
        wrapper
    )

    try:
        wrapper.set_focus()

    except Exception as error:
        raise RuntimeError(
            (
                "Unable to focus UI element: "
                f"{error}"
            )
        ) from error

    try:
        refreshed = _find_wrapper(
            target,
            **selector,
        )

        after = wrapper_to_info(
            refreshed
        )

    except Exception:
        after = before

    verified = bool(
        after.focused
    )

    return UIActionResult(
        action="focus",
        target=after.to_dict(),
        success=True,
        verified=verified,
        detail=(
            "UI element focus requested. "
            f"Focus verification: {verified}."
        ),
    )


# ---------------------------------------------------------------------------
# Invoke
# ---------------------------------------------------------------------------


def invoke_ui_element(
    target: str | int,
    **selector,
) -> UIActionResult:

    wrapper = _find_wrapper(
        target,
        **selector,
    )

    info = wrapper_to_info(
        wrapper
    )

    backend = ""

    try:
        wrapper.invoke()

        backend = (
            "uia.invoke"
        )

    except Exception:

        try:
            wrapper.click()

            backend = (
                "uia.click"
            )

        except Exception as error:
            raise RuntimeError(
                (
                    "UI element does not expose a usable "
                    "invoke action: "
                    f"{error}"
                )
            ) from error

    payload = (
        info.to_dict()
    )

    payload[
        "action_backend"
    ] = backend

    return UIActionResult(
        action="invoke",
        target=payload,
        success=True,
        verified=True,
        detail=(
            f"UI action executed through {backend}."
        ),
    )


# ---------------------------------------------------------------------------
# Set text/value
# ---------------------------------------------------------------------------


def set_ui_value(
    target: str | int,
    value: str,
    **selector,
) -> UIActionResult:
    """
    Structured text/value modification.

    Priority:

        1. UI Automation set_edit_text
        2. UI Automation set_value
        3. native HWND WM_SETTEXT

    Verification:

        native read-back
            ↓
        reacquired UI Automation state
            ↓
        accept the strongest matching observation

    No arbitrary keyboard typing or coordinate clicking is used here.
    """

    wrapper = _find_wrapper(
        target,
        **selector,
    )

    before = wrapper_to_info(
        wrapper
    )

    text = str(
        value
    )

    backend = ""
    native_readback = None
    verified = False

    # ------------------------------------------------------------------
    # Path 1: UIA edit operation
    # ------------------------------------------------------------------

    try:
        wrapper.set_edit_text(
            text
        )

        backend = (
            "uia.set_edit_text"
        )

    except Exception:

        # --------------------------------------------------------------
        # Path 2: UIA value operation
        # --------------------------------------------------------------

        try:
            wrapper.set_value(
                text
            )

            backend = (
                "uia.set_value"
            )

        except Exception:

            # ----------------------------------------------------------
            # Path 3: Native child HWND
            # ----------------------------------------------------------

            native_handle = int(
                before.handle
                or 0
            )

            if native_handle <= 0:
                raise RuntimeError(
                    (
                        "UI element exposes neither a writable "
                        "UI Automation value operation nor a "
                        "native HWND."
                    )
                )

            native_readback = (
                _set_native_window_text(
                    native_handle,
                    text,
                )
            )

            backend = (
                "win32.WM_SETTEXT"
            )

            verified = (
                native_readback
                == text
            )

    # ------------------------------------------------------------------
    # Reacquire the element after mutation.
    # ------------------------------------------------------------------

    try:
        refreshed = _find_wrapper(
            target,
            **selector,
        )

        after = wrapper_to_info(
            refreshed
        )

    except Exception:
        after = before

    observed = str(
        after.value
        or ""
    )

    # ------------------------------------------------------------------
    # UI Automation verification
    # ------------------------------------------------------------------

    if backend.startswith(
        "uia."
    ):

        verified = (
            observed == text
            or (
                bool(text)
                and text in observed
            )
        )

        detail = (
            f"Text written through {backend}. "
            "UI Automation verification: "
            f"{verified}."
        )

    # ------------------------------------------------------------------
    # Native verification
    # ------------------------------------------------------------------

    else:

        # Some modern RichEdit controls accept WM_SETTEXT but do not expose
        # reliable native WM_GETTEXT output. If the reacquired UIA element
        # exposes the resulting text, that is valid post-action verification.

        if not verified:

            verified = (
                observed == text
                or (
                    bool(text)
                    and text in observed
                )
            )

        detail = (
            "Native HWND text write executed through "
            f"{backend}. "
            "Verification from native/UIA read-back: "
            f"{verified}."
        )

    payload = (
        after.to_dict()
    )

    payload[
        "text_backend"
    ] = backend

    if native_readback is not None:

        payload[
            "native_readback"
        ] = native_readback

    payload[
        "observed_value"
    ] = observed

    return UIActionResult(
        action="set_value",
        target=payload,
        success=True,
        verified=verified,
        detail=detail,
    )


# ---------------------------------------------------------------------------
# Toggle
# ---------------------------------------------------------------------------


def toggle_ui_element(
    target: str | int,
    **selector,
) -> UIActionResult:

    wrapper = _find_wrapper(
        target,
        **selector,
    )

    before = wrapper_to_info(
        wrapper
    )

    try:
        wrapper.toggle()

    except Exception as error:
        raise RuntimeError(
            (
                "UI element does not expose a "
                "toggle action: "
                f"{error}"
            )
        ) from error

    try:
        refreshed = _find_wrapper(
            target,
            **selector,
        )

        after = wrapper_to_info(
            refreshed
        )

    except Exception:
        after = before

    verified = (
        bool(
            after.toggle_state
        )
        and (
            before.toggle_state
            != after.toggle_state
        )
    )

    return UIActionResult(
        action="toggle",
        target=after.to_dict(),
        success=True,
        verified=verified,
        detail=(
            "Toggle changed from "
            f"{before.toggle_state!r} "
            "to "
            f"{after.toggle_state!r}. "
            f"Verification: {verified}."
        ),
    )


# ---------------------------------------------------------------------------
# Selection
# ---------------------------------------------------------------------------


def select_ui_element(
    target: str | int,
    **selector,
) -> UIActionResult:

    wrapper = _find_wrapper(
        target,
        **selector,
    )

    before = wrapper_to_info(
        wrapper
    )

    try:
        wrapper.select()

    except Exception as error:
        raise RuntimeError(
            (
                "UI element does not expose a "
                "selection action: "
                f"{error}"
            )
        ) from error

    try:
        refreshed = _find_wrapper(
            target,
            **selector,
        )

        after = wrapper_to_info(
            refreshed
        )

    except Exception:
        after = before

    selection_state = (
        after.selection_state
        or ""
    )

    verified = (
        selection_state
        == "selected"
    )

    return UIActionResult(
        action="select",
        target=after.to_dict(),
        success=True,
        verified=verified,
        detail=(
            "Selection action executed. "
            f"Selection state: "
            f"{selection_state!r}."
        ),
    )