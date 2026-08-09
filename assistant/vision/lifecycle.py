"""
E.V.I.E. - Vision Lifecycle Manager

Created: August 9, 2026
Last Edited: August 9, 2026
Author: Max Maehara

Purpose:
    Manages temporary screenshots created by E.V.I.E.'s vision system.

How It Works:
    - Only files inside runtime/vision may be automatically deleted.
    - Normal vision screenshots are deleted after the reasoning request.
    - Stale orphaned screenshots are removed after crashes or forced exits.
    - Persistent visual memory, if added later, should use a different folder.

Most Recent Change:
    Added safe temporary screenshot deletion and stale-artifact cleanup.
"""

from datetime import datetime, timedelta
from pathlib import Path


ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
    .parent
)

VISION_CACHE = (
    ROOT
    / "runtime"
    / "vision"
)

VISION_CACHE.mkdir(
    parents=True,
    exist_ok=True,
)


def is_temporary_visual_artifact(
    file_path,
) -> bool:
    """
    Returns True only when the file resolves inside runtime/vision.
    """

    if not file_path:
        return False

    try:
        path = Path(file_path).resolve()
        cache = VISION_CACHE.resolve()
        path.relative_to(cache)
        return path.is_file()

    except (
        OSError,
        ValueError,
    ):
        return False


def delete_visual_artifact(
    file_path,
) -> bool:
    """
    Safely deletes one temporary visual artifact.

    Refuses to delete files outside runtime/vision.
    """

    if not is_temporary_visual_artifact(
        file_path
    ):
        return False

    try:
        Path(
            file_path
        ).resolve().unlink()

        return True

    except OSError:
        return False


def cleanup_stale_visual_artifacts(
    max_age_minutes: int = 60,
) -> int:
    """
    Deletes orphaned screenshot files older than max_age_minutes.
    """

    if max_age_minutes < 0:
        raise ValueError(
            "max_age_minutes must be non-negative."
        )

    cutoff = (
        datetime.now()
        - timedelta(
            minutes=max_age_minutes
        )
    ).timestamp()

    deleted = 0

    for pattern in (
        "screen_*.png",
        "screen_*.jpg",
        "screen_*.jpeg",
    ):
        for path in VISION_CACHE.glob(
            pattern
        ):
            try:
                if (
                    path.is_file()
                    and path.stat().st_mtime < cutoff
                ):
                    if delete_visual_artifact(
                        path
                    ):
                        deleted += 1

            except OSError:
                continue

    return deleted


if __name__ == "__main__":

    print(
        "E.V.I.E. Vision Lifecycle"
    )

    print(
        "--------------------------"
    )

    print(
        "Temporary cache:",
        VISION_CACHE,
    )

    deleted = (
        cleanup_stale_visual_artifacts(
            max_age_minutes=60
        )
    )

    print(
        "Stale screenshots deleted:",
        deleted,
    )
