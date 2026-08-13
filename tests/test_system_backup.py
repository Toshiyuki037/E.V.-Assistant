import zipfile

from pathlib import (
    Path,
)

from assistant.system import backup


def test_backup_verify_restore_dry_run(
    monkeypatch,
    tmp_path,
):
    project = (
        tmp_path
        / "project"
    )

    memory = (
        project
        / "memory"
    )

    memory.mkdir(
        parents=True
    )

    db = (
        memory
        / "memory.db"
    )

    import sqlite3

    conn = sqlite3.connect(
        db
    )

    conn.execute(
        "CREATE TABLE test (id INTEGER)"
    )

    conn.commit()

    conn.close()


    runtime = (
        project
        / "runtime"
        / "health"
    )

    runtime.mkdir(
        parents=True
    )

    (
        runtime
        / "component_state.json"
    ).write_text(
        "{}",
        encoding="utf-8",
    )


    monkeypatch.setattr(
        backup,
        "PROJECT_ROOT",
        project,
    )

    monkeypatch.setattr(
        backup,
        "BACKUP_ROOT",
        project
        / "runtime"
        / "backups",
    )


    result = (
        backup.create_backup(
            label=
                "test"
        )
    )

    assert result.success is True


    verification = (
        backup.verify_backup(
            result.backup_path
        )
    )

    assert verification.success is True


    restore = (
        backup.restore_backup(
            result.backup_path,
            dry_run=
                True,
        )
    )

    assert restore.success is True
    assert restore.metadata["dry_run"] is True


def test_corrupt_backup_fails_verification(
    tmp_path,
):
    path = (
        tmp_path
        / "broken.zip"
    )

    path.write_bytes(
        b"not a zip"
    )

    result = (
        backup.verify_backup(
            path
        )
    )

    assert result.success is False


def test_restore_requires_valid_manifest(
    tmp_path,
):
    path = (
        tmp_path
        / "missing_manifest.zip"
    )

    with zipfile.ZipFile(
        path,
        "w",
    ) as archive:

        archive.writestr(
            "runtime/test.txt",
            "hello",
        )


    result = (
        backup.restore_backup(
            path,
            dry_run=
                True,
        )
    )

    assert result.success is False
