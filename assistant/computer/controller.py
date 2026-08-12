"""
E.V.I.E. - Computer Device Controller

Phase 13A / 13B / 13C / 13D / 13E
"""

from __future__ import annotations

from .applications import launch_application
from .clipboard import (
    clear_clipboard,
    read_clipboard_text,
    write_clipboard_text,
)
from .filesystem import (
    copy_path,
    create_directory,
    delete_path,
    get_known_folders,
    inspect_path,
    list_directory,
    move_path,
    read_text_file,
    rename_path,
    search_files,
    write_text_file,
)
from .local_windows import build_local_windows_device
from .notifications import send_windows_notification
from .processes import (
    find_processes,
    list_processes,
    terminate_process,
    top_processes,
)
from .registry import (
    get_device,
    list_devices,
    register_device,
)
from .resources import get_resource_state
from .settings import (
    list_safe_settings_pages,
    open_settings_page,
)
from .system_actions import (
    lock_workstation,
    supported_system_actions,
)
from .system_state import get_basic_system_state
from .windows import (
    desktop_state,
    find_windows,
    focus_window_target,
    maximize_window_target,
    minimize_window_target,
    move_window_target,
    restore_window_target,
)


def ensure_local_device():
    existing = get_device(
        "local-windows"
    )

    if existing is not None:
        return existing

    device = build_local_windows_device()

    device.metadata[
        "control_backend"
    ] = (
        "win32-ctypes+psutil+native-filesystem+"
        "windows-settings+toast"
    )

    device.metadata[
        "phase"
    ] = "13E"

    return register_device(
        device
    )


def describe_devices():
    ensure_local_device()
    return [
        device.to_dict()
        for device in list_devices()
    ]


def get_local_computer_state():
    ensure_local_device()

    return {
        "system": get_basic_system_state(),
        "resources": get_resource_state(),
        "desktop": desktop_state(),
    }


def search_local_windows(query: str):
    ensure_local_device()
    return [
        window.to_dict()
        for window in find_windows(query)
    ]


def focus_local_window(target: str | int):
    ensure_local_device()
    return focus_window_target(target).to_dict()


def minimize_local_window(target: str | int):
    ensure_local_device()
    return minimize_window_target(target).to_dict()


def maximize_local_window(target: str | int):
    ensure_local_device()
    return maximize_window_target(target).to_dict()


def restore_local_window(target: str | int):
    ensure_local_device()
    return restore_window_target(target).to_dict()


def move_local_window(
    target: str | int,
    *,
    x: int,
    y: int,
    width: int | None = None,
    height: int | None = None,
):
    ensure_local_device()
    return move_window_target(
        target,
        x=x,
        y=y,
        width=width,
        height=height,
    ).to_dict()


def launch_local_application(
    application: str,
    *,
    arguments: list[str] | None = None,
    cwd: str | None = None,
):
    ensure_local_device()
    return launch_application(
        application,
        arguments=arguments,
        cwd=cwd,
    ).to_dict()


def list_local_processes():
    ensure_local_device()
    return [
        process.to_dict()
        for process in list_processes()
    ]


def search_local_processes(query: str):
    ensure_local_device()
    return [
        process.to_dict()
        for process in find_processes(query)
    ]


def top_local_processes(
    *,
    limit: int = 10,
    sort_by: str = "memory",
):
    ensure_local_device()
    return [
        process.to_dict()
        for process in top_processes(
            limit=limit,
            sort_by=sort_by,
        )
    ]


def terminate_local_process(
    pid: int,
    *,
    approved: bool = False,
):
    ensure_local_device()
    return terminate_process(
        pid,
        approved=approved,
    )


def read_local_clipboard():
    ensure_local_device()
    return read_clipboard_text()


def write_local_clipboard(text: str):
    ensure_local_device()
    return write_clipboard_text(text)


def clear_local_clipboard():
    ensure_local_device()
    return clear_clipboard()


def get_known_local_folders():
    ensure_local_device()
    return get_known_folders()


def inspect_local_path(path: str):
    ensure_local_device()
    return inspect_path(path).to_dict()


def list_local_directory(path: str):
    ensure_local_device()
    return list_directory(path)


def read_local_text_file(path: str):
    ensure_local_device()
    return read_text_file(path)


def search_local_files(
    root: str,
    query: str,
    *,
    recursive: bool = True,
    limit: int = 100,
):
    ensure_local_device()
    return search_files(
        root,
        query,
        recursive=recursive,
        limit=limit,
    )


def create_local_directory(
    path: str,
    *,
    approved: bool = False,
):
    ensure_local_device()
    return create_directory(
        path,
        approved=approved,
    ).to_dict()


def write_local_text_file(
    path: str,
    content: str,
    *,
    overwrite: bool = False,
    approved: bool = False,
):
    ensure_local_device()
    return write_text_file(
        path,
        content,
        overwrite=overwrite,
        approved=approved,
    ).to_dict()


def copy_local_path(
    source: str,
    destination: str,
    *,
    overwrite: bool = False,
    approved: bool = False,
):
    ensure_local_device()
    return copy_path(
        source,
        destination,
        overwrite=overwrite,
        approved=approved,
    ).to_dict()


def move_local_path(
    source: str,
    destination: str,
    *,
    overwrite: bool = False,
    approved: bool = False,
):
    ensure_local_device()
    return move_path(
        source,
        destination,
        overwrite=overwrite,
        approved=approved,
    ).to_dict()


def rename_local_path(
    source: str,
    new_name: str,
    *,
    approved: bool = False,
):
    ensure_local_device()
    return rename_path(
        source,
        new_name,
        approved=approved,
    ).to_dict()


def delete_local_path(
    path: str,
    *,
    approved: bool = False,
):
    ensure_local_device()
    return delete_path(
        path,
        approved=approved,
    ).to_dict()


def send_local_notification(
    title: str,
    message: str,
):
    ensure_local_device()
    return send_windows_notification(
        title,
        message,
    ).to_dict()


def get_safe_local_settings_pages():
    ensure_local_device()
    return list_safe_settings_pages()


def open_local_settings_page(
    page: str,
):
    ensure_local_device()
    return open_settings_page(
        page
    )


def get_supported_local_system_actions():
    ensure_local_device()
    return supported_system_actions()


def lock_local_workstation(
    *,
    approved: bool = False,
):
    ensure_local_device()
    return lock_workstation(
        approved=approved,
    )
