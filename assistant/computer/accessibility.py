"""
E.V.I.E. - Structured UI Accessibility Inspection

Phase 13G

Window resolution deliberately reuses Phase 13B's native Win32 window
resolver, then binds Microsoft's UI Automation layer to the exact HWND.

This prevents disagreement between Win32 window discovery and UIA title
enumeration.
"""

from __future__ import annotations

from .accessibility_backend import (
    desktop,
    wrapper_to_info,
)

from .windows import (
    resolve_window,
)


def resolve_accessible_window(
    target: str | int,
):
    """
    Resolve the target through the proven Phase 13B native window layer,
    then attach the UI Automation backend to the exact native HWND.

    Hierarchy:

        native Win32 discovery
                ↓
        verified HWND
                ↓
        UI Automation wrapper
    """

    native_window = resolve_window(
        target
    )

    handle = int(
        native_window.handle
    )

    if handle <= 0:
        raise LookupError(
            (
                "Resolved window does not have a valid "
                f"native handle: {target}"
            )
        )

    ui_desktop = desktop()

    try:
        specification = ui_desktop.window(
            handle=handle
        )

        wrapper = (
            specification.wrapper_object()
        )

    except Exception as error:
        raise LookupError(
            (
                "Native window was found, but UI Automation "
                "could not attach to it. "
                f"Target={target!r}, HWND={handle}. "
                f"Reason: {error}"
            )
        ) from error

    return wrapper


def _walk_tree(
    wrapper,
    *,
    depth: int,
    max_depth: int,
    max_elements: int,
    path: list[int],
    output: list,
):
    if len(output) >= max_elements:
        return

    try:
        output.append(
            wrapper_to_info(
                wrapper,
                depth=depth,
                path=path,
            )
        )
    except Exception:
        # Individual UI controls can disappear while an application is
        # changing. One stale child must not invalidate the whole tree.
        return

    if depth >= max_depth:
        return

    try:
        children = (
            wrapper.children()
        )

    except Exception:
        children = []

    for index, child in enumerate(
        children
    ):
        if len(output) >= max_elements:
            break

        _walk_tree(
            child,
            depth=depth + 1,
            max_depth=max_depth,
            max_elements=max_elements,
            path=[
                *path,
                index,
            ],
            output=output,
        )


def inspect_ui_tree(
    target: str | int,
    *,
    max_depth: int = 5,
    max_elements: int = 500,
) -> list[dict]:
    window = resolve_accessible_window(
        target
    )

    depth_limit = max(
        0,
        int(max_depth),
    )

    element_limit = max(
        1,
        min(
            int(max_elements),
            5000,
        ),
    )

    output = []

    _walk_tree(
        window,
        depth=0,
        max_depth=depth_limit,
        max_elements=element_limit,
        path=[],
        output=output,
    )

    return [
        item.to_dict()
        for item in output
    ]


def find_ui_elements(
    target: str | int,
    *,
    name: str = "",
    control_type: str = "",
    automation_id: str = "",
    exact_name: bool = False,
    max_depth: int = 8,
    limit: int = 100,
) -> list[dict]:
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
            "At least one UI search field must be provided."
        )

    tree = inspect_ui_tree(
        target,
        max_depth=max_depth,
        max_elements=2000,
    )

    matches = []

    for item in tree:
        item_name = str(
            item.get(
                "name",
                "",
            )
        ).lower()

        item_type = str(
            item.get(
                "control_type",
                "",
            )
        ).lower()

        item_automation = str(
            item.get(
                "automation_id",
                "",
            )
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
            and type_text != item_type
        ):
            continue

        if (
            automation_text
            and automation_text
            != item_automation
        ):
            continue

        matches.append(
            item
        )

        if (
            len(matches)
            >= int(limit)
        ):
            break

    return matches


def reacquire_element(
    target: str | int,
    selector: dict,
):
    """
    Re-run the structured lookup rather than trusting a stored UI object
    after the interface may have changed.
    """

    matches = find_ui_elements(
        target,
        name=str(
            selector.get(
                "name",
                "",
            )
        ),
        control_type=str(
            selector.get(
                "control_type",
                "",
            )
        ),
        automation_id=str(
            selector.get(
                "automation_id",
                "",
            )
        ),
        exact_name=bool(
            selector.get(
                "exact_name",
                False,
            )
        ),
        max_depth=int(
            selector.get(
                "max_depth",
                8,
            )
        ),
        limit=10,
    )

    if not matches:
        raise LookupError(
            (
                "No UI element matched "
                f"selector: {selector}"
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