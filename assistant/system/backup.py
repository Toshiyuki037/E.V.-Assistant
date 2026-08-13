"""
E.V.I.E. - Backup, Restore & Integrity

Phase 15K

Purpose:
    Protects persistent E.V.I.E. state without backing up the entire source tree.

Backed-up state may include:
    - memory database
    - runtime integration metadata
    - workflow/task state
    - voice identity
    - health/failure history
    - selected runtime configuration

Important:
    - source code is not backed up here; Git remains authoritative for code
    - credentials stored in OS keyring are NOT exported
    - restore is explicit
    - backup contents are verified before restore
"""

from __future__ import annotations

import json
import shutil
import sqlite3
import zipfile

from dataclasses import (
    asdict,
    dataclass,
    field,
)

from datetime import (
    datetime,
    timezone,
)

from pathlib import (
    Path,
)

from typing import (
    Any,
)


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

BACKUP_ROOT = (
    PROJECT_ROOT
    / "runtime"
    / "backups"
)

MANIFEST_NAME = (
    "backup_manifest.json"
)


@dataclass
class BackupResult:
    success: bool

    backup_path: str = ""

    detail: str = ""

    included_files: list[str] = field(
        default_factory=list
    )

    skipped_files: list[str] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class IntegrityResult:
    success: bool

    component: str

    detail: str = ""

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


def _now_stamp():
    return (
        datetime.now(
            timezone.utc
        )
        .strftime(
            "%Y%m%d_%H%M%S"
        )
    )


def _candidate_state_paths():
    """
    Returns persistent-state candidates only.

    Missing paths are fine; they are skipped.
    """

    return [
        PROJECT_ROOT
        / "memory"
        / "memory.db",

        PROJECT_ROOT
        / "runtime"
        / "integrations"
        / "accounts.json",

        PROJECT_ROOT
        / "runtime"
        / "health"
        / "component_state.json",

        PROJECT_ROOT
        / "runtime"
        / "voice_identity",

        PROJECT_ROOT
        / "runtime"
        / "workflows",

        PROJECT_ROOT
        / "runtime"
        / "agent",

        PROJECT_ROOT
        / "runtime"
        / "preferences",
    ]


def _relative_name(
    path: Path,
):
    return str(
        path.relative_to(
            PROJECT_ROOT
        )
    ).replace(
        "\\",
        "/",
    )


def _iter_files(
    path: Path,
):
    if path.is_file():
        yield path

    elif path.is_dir():

        for item in path.rglob(
            "*"
        ):

            if item.is_file():
                yield item


def validate_memory_database():
    path = (
        PROJECT_ROOT
        / "memory"
        / "memory.db"
    )

    if not path.exists():

        return IntegrityResult(
            success=
                False,

            component=
                "memory.database",

            detail=
                "Memory database does not exist.",
        )


    try:

        conn = sqlite3.connect(
            str(
                path
            )
        )

        result = (
            conn.execute(
                "PRAGMA quick_check"
            )
            .fetchone()
        )

        conn.close()


    except Exception as error:

        return IntegrityResult(
            success=
                False,

            component=
                "memory.database",

            detail=
                str(
                    error
                ),
        )


    value = (
        result[
            0
        ]
        if result
        else ""
    )


    success = (
        str(
            value
        )
        .lower()
        == "ok"
    )


    return IntegrityResult(
        success=
            success,

        component=
            "memory.database",

        detail=(
            "SQLite quick_check passed."
            if success
            else f"SQLite quick_check returned: {value}"
        ),
    )


def create_backup(
    *,
    label: str = "manual",
):
    BACKUP_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )


    backup_name = (
        f"evie_state_{_now_stamp()}_{label}.zip"
    )


    backup_path = (
        BACKUP_ROOT
        / backup_name
    )


    included = []

    skipped = []


    try:

        with zipfile.ZipFile(
            backup_path,
            "w",
            zipfile.ZIP_DEFLATED,
        ) as archive:

            for candidate in _candidate_state_paths():

                if not candidate.exists():

                    skipped.append(
                        _relative_name(
                            candidate
                        )
                    )

                    continue


                for file_path in _iter_files(
                    candidate
                ):

                    relative = (
                        _relative_name(
                            file_path
                        )
                    )

                    archive.write(
                        file_path,
                        relative,
                    )

                    included.append(
                        relative
                    )


            manifest = {
                "created_at":
                    datetime.now(
                        timezone.utc
                    )
                    .isoformat(),

                "label":
                    label,

                "included_files":
                    included,

                "skipped_paths":
                    skipped,

                "credentials_exported":
                    False,

                "source_code_included":
                    False,
            }


            archive.writestr(
                MANIFEST_NAME,
                json.dumps(
                    manifest,
                    indent=2,
                    ensure_ascii=False,
                ),
            )


    except Exception as error:

        return BackupResult(
            success=
                False,

            backup_path=
                str(
                    backup_path
                ),

            detail=
                str(
                    error
                ),

            included_files=
                included,

            skipped_files=
                skipped,
        )


    verification = (
        verify_backup(
            backup_path
        )
    )


    if not verification.success:

        return BackupResult(
            success=
                False,

            backup_path=
                str(
                    backup_path
                ),

            detail=(
                "Backup was created but verification failed: "
                + verification.detail
            ),

            included_files=
                included,

            skipped_files=
                skipped,
        )


    return BackupResult(
        success=
            True,

        backup_path=
            str(
                backup_path
            ),

        detail=
            "Backup created and verified.",

        included_files=
            included,

        skipped_files=
            skipped,

        metadata={
            "file_count":
                len(
                    included
                ),
        },
    )


def verify_backup(
    backup_path: str | Path,
):
    path = (
        Path(
            backup_path
        )
    )


    if not path.exists():

        return IntegrityResult(
            success=
                False,

            component=
                "backup",

            detail=
                "Backup file does not exist.",
        )


    try:

        with zipfile.ZipFile(
            path,
            "r",
        ) as archive:

            bad_file = (
                archive.testzip()
            )


            if bad_file:

                return IntegrityResult(
                    success=
                        False,

                    component=
                        "backup",

                    detail=
                        f"Corrupt archive member: {bad_file}",
                )


            names = (
                archive.namelist()
            )


            if MANIFEST_NAME not in names:

                return IntegrityResult(
                    success=
                        False,

                    component=
                        "backup",

                    detail=
                        "Backup manifest is missing.",
                )


            manifest = json.loads(
                archive.read(
                    MANIFEST_NAME
                )
                .decode(
                    "utf-8"
                )
            )


            if not isinstance(
                manifest,
                dict,
            ):

                return IntegrityResult(
                    success=
                        False,

                    component=
                        "backup",

                    detail=
                        "Backup manifest is invalid.",
                )


    except Exception as error:

        return IntegrityResult(
            success=
                False,

            component=
                "backup",

            detail=
                str(
                    error
                ),
        )


    return IntegrityResult(
        success=
            True,

        component=
            "backup",

        detail=
            "Backup archive integrity verified.",

        metadata={
            "manifest":
                manifest,
        },
    )


def restore_backup(
    backup_path: str | Path,
    *,
    dry_run: bool = True,
):
    verification = (
        verify_backup(
            backup_path
        )
    )


    if not verification.success:

        return BackupResult(
            success=
                False,

            backup_path=
                str(
                    backup_path
                ),

            detail=
                verification.detail,
        )


    path = (
        Path(
            backup_path
        )
    )


    with zipfile.ZipFile(
        path,
        "r",
    ) as archive:

        names = [
            name

            for name
            in archive.namelist()

            if name
            != MANIFEST_NAME
        ]


        if dry_run:

            return BackupResult(
                success=
                    True,

                backup_path=
                    str(
                        path
                    ),

                detail=
                    "Restore validation passed. Dry run only; no files changed.",

                included_files=
                    names,

                metadata={
                    "dry_run":
                        True,
                },
            )


        for name in names:

            target = (
                PROJECT_ROOT
                / name
            ).resolve()


            if PROJECT_ROOT.resolve() not in target.parents:

                return BackupResult(
                    success=
                        False,

                    backup_path=
                        str(
                            path
                        ),

                    detail=
                        f"Unsafe restore path rejected: {name}",
                )


            target.parent.mkdir(
                parents=True,
                exist_ok=True,
            )


            with archive.open(
                name
            ) as source, target.open(
                "wb"
            ) as destination:

                shutil.copyfileobj(
                    source,
                    destination,
                )


    return BackupResult(
        success=
            True,

        backup_path=
            str(
                path
            ),

        detail=
            "Backup restored.",

        included_files=
            names,

        metadata={
            "dry_run":
                False,
        },
    )


def list_backups():
    if not BACKUP_ROOT.exists():

        return []


    return sorted(
        BACKUP_ROOT.glob(
            "evie_state_*.zip"
        ),
        key=lambda path:
            path.stat().st_mtime,
        reverse=True,
    )


def prune_backups(
    *,
    keep_latest: int = 10,
):
    backups = (
        list_backups()
    )


    keep_latest = max(
        0,
        int(
            keep_latest
        ),
    )


    removed = []


    for path in backups[
        keep_latest:
    ]:

        try:

            path.unlink()

            removed.append(
                str(
                    path
                )
            )

        except OSError:

            pass


    return BackupResult(
        success=
            True,

        detail=
            f"Pruned {len(removed)} old backups.",

        included_files=
            removed,

        metadata={
            "removed":
                len(
                    removed
                ),

            "kept":
                min(
                    len(
                        backups
                    ),
                    keep_latest,
                ),
        },
    )
