"""
E.V.I.E. - Safe Local Filesystem Control

Phase 13D

Structured filesystem operations with path policy checks and postcondition
verification.
"""

from __future__ import annotations

import fnmatch
import os
from pathlib import Path
import shutil

from .filesystem_models import (
    FilesystemActionResult,
    PathInfo,
)
from .path_policy import (
    assert_mutation_allowed,
    canonicalize_path,
    classify_path,
)


def get_known_folders() -> dict[str, str]:
    home = Path.home()

    folders = {
        "home": home,
        "desktop": home / "Desktop",
        "documents": home / "Documents",
        "downloads": home / "Downloads",
        "pictures": home / "Pictures",
        "music": home / "Music",
        "videos": home / "Videos",
    }

    return {
        name: str(
            path.resolve(
                strict=False
            )
        )
        for name, path
        in folders.items()
    }


def inspect_path(
    value: str | os.PathLike,
) -> PathInfo:
    path = canonicalize_path(
        value
    )

    exists = path.exists()

    stat = None

    if exists:
        try:
            stat = path.stat()
        except OSError:
            stat = None

    return PathInfo(
        path=str(path),
        exists=exists,
        is_file=path.is_file(),
        is_directory=path.is_dir(),
        size=(
            int(stat.st_size)
            if stat
            else 0
        ),
        modified_at=(
            float(stat.st_mtime)
            if stat
            else 0.0
        ),
        risk=classify_path(
            path
        ),
    )


def list_directory(
    value: str | os.PathLike,
) -> list[dict]:
    path = canonicalize_path(
        value
    )

    if not path.exists():
        raise FileNotFoundError(
            str(path)
        )

    if not path.is_dir():
        raise NotADirectoryError(
            str(path)
        )

    items = []

    for child in sorted(
        path.iterdir(),
        key=lambda item: (
            not item.is_dir(),
            item.name.lower(),
        ),
    ):
        items.append(
            inspect_path(
                child
            ).to_dict()
        )

    return items


def read_text_file(
    value: str | os.PathLike,
    *,
    encoding: str = "utf-8",
    max_bytes: int = 2_000_000,
) -> str:
    path = canonicalize_path(
        value
    )

    if not path.is_file():
        raise FileNotFoundError(
            str(path)
        )

    size = path.stat().st_size

    if size > int(max_bytes):
        raise ValueError(
            (
                "Refusing to read oversized text file "
                f"({size} bytes > {max_bytes})."
            )
        )

    return path.read_text(
        encoding=encoding
    )


def search_files(
    root: str | os.PathLike,
    query: str,
    *,
    recursive: bool = True,
    limit: int = 100,
) -> list[dict]:
    root_path = canonicalize_path(
        root
    )

    if not root_path.is_dir():
        raise NotADirectoryError(
            str(root_path)
        )

    pattern = str(
        query
        or ""
    ).strip()

    if not pattern:
        raise ValueError(
            "Search query cannot be empty."
        )

    wildcard = (
        pattern
        if any(
            char in pattern
            for char in "*?[]"
        )
        else f"*{pattern}*"
    )

    iterator = (
        root_path.rglob("*")
        if recursive
        else root_path.glob("*")
    )

    results = []

    for path in iterator:
        if fnmatch.fnmatch(
            path.name.lower(),
            wildcard.lower(),
        ):
            results.append(
                inspect_path(
                    path
                ).to_dict()
            )

            if len(results) >= int(limit):
                break

    return results


def create_directory(
    value: str | os.PathLike,
    *,
    approved: bool = False,
) -> FilesystemActionResult:
    path = canonicalize_path(
        value
    )

    assert_mutation_allowed(
        path,
        approved=approved,
    )

    path.mkdir(
        parents=True,
        exist_ok=True,
    )

    verified = (
        path.exists()
        and path.is_dir()
    )

    return FilesystemActionResult(
        action="create_directory",
        destination=str(path),
        success=verified,
        verified=verified,
        message=(
            "Directory created."
            if verified
            else "Directory creation could not be verified."
        ),
    )


def write_text_file(
    value: str | os.PathLike,
    content: str,
    *,
    encoding: str = "utf-8",
    overwrite: bool = False,
    approved: bool = False,
) -> FilesystemActionResult:
    path = canonicalize_path(
        value
    )

    assert_mutation_allowed(
        path,
        approved=approved,
    )

    if (
        path.exists()
        and not overwrite
    ):
        raise FileExistsError(
            str(path)
        )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    value_text = str(
        content
    )

    path.write_text(
        value_text,
        encoding=encoding,
    )

    verified = (
        path.exists()
        and path.is_file()
        and path.read_text(
            encoding=encoding
        ) == value_text
    )

    return FilesystemActionResult(
        action="write_text_file",
        destination=str(path),
        success=verified,
        verified=verified,
        message=(
            "File written."
            if verified
            else "File write could not be verified."
        ),
    )


def copy_path(
    source: str | os.PathLike,
    destination: str | os.PathLike,
    *,
    overwrite: bool = False,
    approved: bool = False,
) -> FilesystemActionResult:
    src = canonicalize_path(
        source
    )

    dst = canonicalize_path(
        destination
    )

    if not src.exists():
        raise FileNotFoundError(
            str(src)
        )

    assert_mutation_allowed(
        dst,
        approved=approved,
    )

    if (
        dst.exists()
        and not overwrite
    ):
        raise FileExistsError(
            str(dst)
        )

    if src.is_dir():
        shutil.copytree(
            src,
            dst,
            dirs_exist_ok=overwrite,
        )
    else:
        dst.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        shutil.copy2(
            src,
            dst,
        )

    verified = dst.exists()

    return FilesystemActionResult(
        action="copy",
        source=str(src),
        destination=str(dst),
        success=verified,
        verified=verified,
        message=(
            "Path copied."
            if verified
            else "Copy could not be verified."
        ),
    )


def move_path(
    source: str | os.PathLike,
    destination: str | os.PathLike,
    *,
    overwrite: bool = False,
    approved: bool = False,
) -> FilesystemActionResult:
    src = canonicalize_path(
        source
    )

    dst = canonicalize_path(
        destination
    )

    if not src.exists():
        raise FileNotFoundError(
            str(src)
        )

    assert_mutation_allowed(
        src,
        approved=approved,
    )

    assert_mutation_allowed(
        dst,
        approved=approved,
    )

    if (
        dst.exists()
        and not overwrite
    ):
        raise FileExistsError(
            str(dst)
        )

    if (
        dst.exists()
        and overwrite
    ):
        if dst.is_dir():
            shutil.rmtree(
                dst
            )
        else:
            dst.unlink()

    dst.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    shutil.move(
        str(src),
        str(dst),
    )

    verified = (
        dst.exists()
        and not src.exists()
    )

    return FilesystemActionResult(
        action="move",
        source=str(src),
        destination=str(dst),
        success=verified,
        verified=verified,
        message=(
            "Path moved."
            if verified
            else "Move could not be verified."
        ),
    )


def rename_path(
    source: str | os.PathLike,
    new_name: str,
    *,
    approved: bool = False,
) -> FilesystemActionResult:
    src = canonicalize_path(
        source
    )

    if not src.exists():
        raise FileNotFoundError(
            str(src)
        )

    name = str(
        new_name
        or ""
    ).strip()

    if not name:
        raise ValueError(
            "New name cannot be empty."
        )

    if (
        Path(name).name
        != name
    ):
        raise ValueError(
            "rename_path accepts a filename only, not another path."
        )

    dst = src.with_name(
        name
    )

    return move_path(
        src,
        dst,
        approved=approved,
    )


def delete_path(
    value: str | os.PathLike,
    *,
    approved: bool = False,
) -> FilesystemActionResult:
    """
    Phase 13D destructive deletion is intentionally approval-gated.

    This uses direct deletion rather than Recycle Bin so automated tests stay
    deterministic. Higher-level natural-language integration should describe
    this as destructive and require explicit approval.
    """
    path = canonicalize_path(
        value
    )

    if not path.exists():
        raise FileNotFoundError(
            str(path)
        )

    if not approved:
        raise PermissionError(
            "Filesystem deletion requires explicit approval."
        )

    assert_mutation_allowed(
        path,
        approved=True,
    )

    if path.is_dir():
        shutil.rmtree(
            path
        )
    else:
        path.unlink()

    verified = (
        not path.exists()
    )

    return FilesystemActionResult(
        action="delete",
        source=str(path),
        success=verified,
        verified=verified,
        message=(
            "Path deleted."
            if verified
            else "Deletion could not be verified."
        ),
    )
