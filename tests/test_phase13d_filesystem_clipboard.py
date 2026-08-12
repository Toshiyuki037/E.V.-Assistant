import sys

import pytest

from assistant.computer.filesystem import (
    copy_path,
    create_directory,
    delete_path,
    inspect_path,
    move_path,
    read_text_file,
    rename_path,
    search_files,
    write_text_file,
)
from assistant.computer.filesystem_models import (
    PathRisk,
)
from assistant.computer.path_policy import (
    classify_path,
)


def test_normal_temp_path_is_not_protected(
    tmp_path,
):
    assert (
        classify_path(tmp_path)
        != PathRisk.PROTECTED
    )


def test_create_write_read_search_copy_move_rename_delete(
    tmp_path,
):
    root = tmp_path / "workspace"

    created = create_directory(
        root
    )
    assert created.verified is True

    source = root / "hello.txt"

    written = write_text_file(
        source,
        "Phase 13D works.",
    )
    assert written.verified is True
    assert read_text_file(source) == "Phase 13D works."

    results = search_files(
        root,
        "hello",
    )
    assert len(results) == 1

    copied_path = root / "copy.txt"

    copied = copy_path(
        source,
        copied_path,
    )
    assert copied.verified is True

    moved_path = root / "moved.txt"

    moved = move_path(
        copied_path,
        moved_path,
    )
    assert moved.verified is True

    renamed = rename_path(
        moved_path,
        "renamed.txt",
    )
    assert renamed.verified is True

    renamed_path = root / "renamed.txt"

    with pytest.raises(PermissionError):
        delete_path(
            renamed_path,
            approved=False,
        )

    deleted = delete_path(
        renamed_path,
        approved=True,
    )

    assert deleted.verified is True
    assert not renamed_path.exists()


def test_write_refuses_overwrite_by_default(
    tmp_path,
):
    path = tmp_path / "note.txt"

    write_text_file(
        path,
        "one",
    )

    with pytest.raises(FileExistsError):
        write_text_file(
            path,
            "two",
        )


def test_sensitive_path_requires_approval(
    tmp_path,
):
    sensitive = (
        tmp_path
        / ".git"
        / "config"
    )

    with pytest.raises(PermissionError):
        write_text_file(
            sensitive,
            "test",
            approved=False,
        )


@pytest.mark.skipif(
    sys.platform != "win32",
    reason="Native Windows clipboard test",
)
def test_native_clipboard_round_trip():
    from assistant.computer.clipboard import (
        read_clipboard_text,
        write_clipboard_text,
    )

    marker = "E.V.I.E. Phase 13D clipboard"

    write_clipboard_text(
        marker
    )

    assert (
        read_clipboard_text()
        == marker
    )
