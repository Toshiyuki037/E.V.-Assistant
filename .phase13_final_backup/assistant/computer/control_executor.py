
"""
E.V.I.E. - Unified Computer Control Executor

Phase 13J
"""

from __future__ import annotations

from .control_context import ControlContext
from .control_models import (
    AttemptStatus,
    ControlAttempt,
    ControlMethod,
    ComputerControlRequest,
    ComputerControlResult,
)
from .control_policy import (
    ensure_request_allowed,
    may_fallback_after,
    ordered_methods,
)
from .control_router import (
    method_supports_request,
    unsupported_attempt,
)

from .controller import (
    copy_local_path,
    create_local_directory,
    delete_local_path,
    focus_local_window,
    launch_local_application,
    maximize_local_window,
    minimize_local_window,
    move_local_path,
    move_local_window,
    open_local_settings_page,
    rename_local_path,
    send_local_notification,
    terminate_local_process,
    write_local_clipboard,
    write_local_text_file,
)
from .accessibility_controller import (
    focus_local_ui_element,
    invoke_local_ui_element,
    select_local_ui_element,
    set_local_ui_value,
    toggle_local_ui_element,
)
from .browser_controller import (
    click_local_dom_element,
    fill_local_dom_element,
    navigate_local_browser_page,
    press_local_dom_key,
    select_local_dom_option,
    set_local_dom_checked,
)
from .vision_controller import (
    click_local_visual_target,
    move_local_pointer_to_visual_target,
)


def _success(
    request,
    method,
    value,
    *,
    verified=True,
    confidence=1.0,
    attempts=None,
):
    return ComputerControlResult(
        action=request.action,
        target=request.target,
        success=True,
        method=method.value,
        verified=bool(verified),
        confidence=float(confidence),
        result=value,
        attempts=list(attempts or []),
        detail=(
            f"Computer action executed through {method.value}."
        ),
    )


def _native(
    request: ComputerControlRequest,
):
    a = request.action
    x = request.arguments

    if a == "window.focus":
        return focus_local_window(
            request.target
        )

    if a == "window.minimize":
        return minimize_local_window(
            request.target
        )

    if a == "window.maximize":
        return maximize_local_window(
            request.target
        )

    if a == "window.move":
        return move_local_window(
            request.target,
            x=int(x["x"]),
            y=int(x["y"]),
            width=x.get("width"),
            height=x.get("height"),
        )

    if a == "application.launch":
        return launch_local_application(
            request.target,
            arguments=x.get("arguments"),
            cwd=x.get("cwd"),
        )

    if a == "filesystem.create_directory":
        return create_local_directory(
            request.target,
            approved=request.approved,
        )

    if a == "filesystem.write":
        return write_local_text_file(
            request.target,
            str(x.get("content", "")),
            overwrite=bool(
                x.get("overwrite", False)
            ),
            approved=request.approved,
        )

    if a == "filesystem.copy":
        return copy_local_path(
            request.target,
            str(x["destination"]),
            overwrite=bool(
                x.get("overwrite", False)
            ),
            approved=request.approved,
        )

    if a == "filesystem.move":
        return move_local_path(
            request.target,
            str(x["destination"]),
            overwrite=bool(
                x.get("overwrite", False)
            ),
            approved=request.approved,
        )

    if a == "filesystem.rename":
        return rename_local_path(
            request.target,
            str(x["new_name"]),
            approved=request.approved,
        )

    if a == "filesystem.delete":
        return delete_local_path(
            request.target,
            approved=request.approved,
        )

    if a == "clipboard.write":
        return write_local_clipboard(
            str(x.get("text", ""))
        )

    if a == "notification.send":
        return send_local_notification(
            str(x.get("title", "E.V.I.E.")),
            str(x.get("message", "")),
        )

    if a == "settings.open":
        return open_local_settings_page(
            request.target
        )

    if a == "process.terminate":
        return terminate_local_process(
            int(x["pid"]),
            approved=request.approved,
        )

    raise NotImplementedError(
        a
    )


def _accessibility(
    request: ComputerControlRequest,
):
    x = request.arguments
    selector = dict(
        x.get(
            "selector",
            {},
        )
    )

    if request.action == "accessibility.focus":
        return focus_local_ui_element(
            request.target,
            **selector,
        )

    if request.action == "accessibility.invoke":
        return invoke_local_ui_element(
            request.target,
            **selector,
        )

    if request.action == "accessibility.set_value":
        return set_local_ui_value(
            request.target,
            str(x.get("value", "")),
            **selector,
        )

    if request.action == "accessibility.toggle":
        return toggle_local_ui_element(
            request.target,
            **selector,
        )

    if request.action == "accessibility.select":
        return select_local_ui_element(
            request.target,
            **selector,
        )

    raise NotImplementedError(
        request.action
    )


def _dom(
    request: ComputerControlRequest,
    context: ControlContext,
):
    session = context.browser_session

    if session is None:
        raise LookupError(
            "No browser DOM session is available."
        )

    x = request.arguments

    if request.action == "browser.navigate":
        return navigate_local_browser_page(
            session,
            str(x["url"]),
            page_target=x.get(
                "page_target"
            ),
        )

    if request.action == "browser.dom.click":
        return click_local_dom_element(
            session,
            **x,
        )

    if request.action == "browser.dom.fill":
        value = str(
            x.pop(
                "value"
            )
        )

        return fill_local_dom_element(
            session,
            value,
            **x,
        )

    if request.action == "browser.dom.check":
        checked = bool(
            x.pop(
                "checked"
            )
        )

        return set_local_dom_checked(
            session,
            checked,
            **x,
        )

    if request.action == "browser.dom.select":
        value = str(
            x.pop(
                "value"
            )
        )

        return select_local_dom_option(
            session,
            value,
            **x,
        )

    if request.action == "browser.dom.press":
        key = str(
            x.pop(
                "key"
            )
        )

        return press_local_dom_key(
            session,
            key,
            **x,
        )

    raise NotImplementedError(
        request.action
    )


def _vision(
    request: ComputerControlRequest,
):
    x = request.arguments

    payload = dict(
        x["visual_target"]
    )

    common = {
        "screen_width":
            int(x["screen_width"]),

        "screen_height":
            int(x["screen_height"]),
    }

    if request.action == "vision.pointer_move":
        return move_local_pointer_to_visual_target(
            payload,
            **common,
        )

    if request.action == "vision.click":
        return click_local_visual_target(
            payload,
            approved=request.approved,
            **common,
        )

    raise NotImplementedError(
        request.action
    )


def execute_computer_control(
    request: ComputerControlRequest,
    *,
    context: ControlContext | None = None,
) -> ComputerControlResult:
    ensure_request_allowed(
        request
    )

    ctx = context or ControlContext(
        request=request
    )

    attempts = []

    for method in ordered_methods(
        request
    ):
        if not method_supports_request(
            method,
            request,
        ):
            attempts.append(
                unsupported_attempt(
                    method,
                    request.action,
                )
            )
            continue

        try:
            if method == ControlMethod.NATIVE:
                value = _native(
                    request
                )

            elif method == ControlMethod.ACCESSIBILITY:
                value = _accessibility(
                    request
                )

            elif method == ControlMethod.DOM:
                value = _dom(
                    request,
                    ctx,
                )

            elif method == ControlMethod.VISION:
                value = _vision(
                    request
                )

            else:
                raise NotImplementedError(
                    method.value
                )

            verified = True

            if isinstance(
                value,
                dict,
            ):
                verified = bool(
                    value.get(
                        "verified",
                        value.get(
                            "success",
                            True,
                        ),
                    )
                )

            attempts.append(
                ControlAttempt(
                    method=method,
                    status=AttemptStatus.SUCCESS,
                    detail="Execution succeeded.",
                    confidence=1.0,
                )
            )

            return _success(
                request,
                method,
                value,
                verified=verified,
                attempts=attempts,
            )

        except LookupError as error:
            status = (
                AttemptStatus.NOT_FOUND
            )
            error_detail = str(
                error
            )

        except NotImplementedError as error:
            status = (
                AttemptStatus.UNSUPPORTED
            )
            error_detail = str(
                error
            )

        except PermissionError as error:
            # Request-level approval was already checked by
            # ensure_request_allowed() before execution began.
            #
            # A PermissionError raised here therefore represents a
            # backend/policy denial such as:
            #
            # - protected filesystem path
            # - disabled/trust boundary
            # - operation-specific safety restriction
            #
            # Record it as BLOCKED and do NOT fall through to a weaker
            # control method such as vision.
            status = (
                AttemptStatus.BLOCKED
            )
            error_detail = str(
                error
            )

        except Exception as error:
            status = (
                AttemptStatus.FAILED
            )
            error_detail = str(
                error
            )

        attempts.append(
            ControlAttempt(
                method=method,
                status=status,
                detail=error_detail,
                confidence=0.0,
            )
        )

        if not may_fallback_after(
            status
        ):
            break

    return ComputerControlResult(
        action=request.action,
        target=request.target,
        success=False,
        attempts=attempts,
        detail="No control method completed the requested action.",
    )
