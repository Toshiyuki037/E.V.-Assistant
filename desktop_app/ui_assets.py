from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import (
    QRectF,
    QSize,
    Qt,
)

from PySide6.QtGui import (
    QIcon,
    QPainter,
    QPainterPath,
    QPixmap,
)

from PySide6.QtWidgets import (
    QLabel,
)


DESKTOP_APP_DIR = (
    Path(__file__)
    .resolve()
    .parent
)

ASSETS_DIR = (
    DESKTOP_APP_DIR
    / "assets"
)

FAVICON_DIR = (
    ASSETS_DIR
    / "favicons"
)

PROFILE_SOURCE = (
    ASSETS_DIR
    / "IMG_8319.jpeg"
)

PROFILE_CACHE = (
    ASSETS_DIR
    / "profile_circle.png"
)


FAVICONS = {
    "dashboard":
        FAVICON_DIR / "home.png",

    "workspace":
        FAVICON_DIR / "document.png",

    "activity":
        FAVICON_DIR / "activity.png",

    "system":
        FAVICON_DIR / "menu.png",

    "settings":
        FAVICON_DIR / "setting.png",

    "notifications":
        FAVICON_DIR / "notification.png",
}


# Original navbar favicon target was ~20 px.
# User requested 0.75x, so final target is 15 px.
NAV_ICON_SIZE = 15

# Utility icons were ~20 px.
# Keep the same 0.75x treatment for visual consistency.
UTILITY_ICON_SIZE = 15

# Profile is intentionally smaller than the 46 px utility-button diameter.
PROFILE_DISPLAY_SIZE = 36


def load_icon(
    path: Path,
) -> QIcon:
    if not path.exists():
        return QIcon()

    return QIcon(
        str(path)
    )


def build_circular_profile_pixmap(
    source_path: Path = PROFILE_SOURCE,
    *,
    output_size: int = 144,
) -> QPixmap:
    if not source_path.exists():
        return QPixmap()

    source = QPixmap(
        str(source_path)
    )

    if source.isNull():
        return QPixmap()

    width = source.width()
    height = source.height()
    side = min(
        width,
        height,
    )

    left = (
        width
        - side
    ) // 2

    top = (
        height
        - side
    ) // 2

    cropped = source.copy(
        left,
        top,
        side,
        side,
    )

    target = max(
        96,
        int(output_size),
    )

    scaled = cropped.scaled(
        target,
        target,
        Qt.KeepAspectRatioByExpanding,
        Qt.SmoothTransformation,
    )

    result = QPixmap(
        target,
        target,
    )

    result.fill(
        Qt.transparent
    )

    painter = QPainter(
        result
    )

    painter.setRenderHint(
        QPainter.Antialiasing,
        True,
    )

    painter.setRenderHint(
        QPainter.SmoothPixmapTransform,
        True,
    )

    clip = QPainterPath()

    # Slight inset prevents aliasing on the outermost pixel.
    clip.addEllipse(
        QRectF(
            1,
            1,
            target - 2,
            target - 2,
        )
    )

    painter.setClipPath(
        clip
    )

    painter.drawPixmap(
        0,
        0,
        scaled,
    )

    painter.end()

    return result


def ensure_profile_cache():
    if not PROFILE_SOURCE.exists():
        return None

    rebuild = (
        not PROFILE_CACHE.exists()
    )

    if not rebuild:
        try:
            rebuild = (
                PROFILE_SOURCE.stat().st_mtime
                > PROFILE_CACHE.stat().st_mtime
            )

        except OSError:
            rebuild = True

    if rebuild:
        pixmap = build_circular_profile_pixmap()

        if not pixmap.isNull():
            try:
                pixmap.save(
                    str(PROFILE_CACHE),
                    "PNG",
                    100,
                )

            except Exception:
                return None

    return (
        PROFILE_CACHE
        if PROFILE_CACHE.exists()
        else None
    )


class CircularAvatar(QLabel):
    def __init__(
        self,
        parent=None,
        *,
        display_size: int = PROFILE_DISPLAY_SIZE,
    ):
        super().__init__(
            parent
        )

        self.display_size = int(
            display_size
        )

        self.setFixedSize(
            self.display_size,
            self.display_size,
        )

        self.setAlignment(
            Qt.AlignCenter
        )

        self.setObjectName(
            "ProfileAvatar"
        )

        self.reload()

    def reload(
        self,
    ):
        cached = ensure_profile_cache()

        if cached is None:
            self.setText(
                "MM"
            )
            return

        pixmap = QPixmap(
            str(cached)
        )

        if pixmap.isNull():
            self.setText(
                "MM"
            )
            return

        self.setText("")

        self.setPixmap(
            pixmap.scaled(
                self.display_size,
                self.display_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )


def app_profile_icon():
    cached = ensure_profile_cache()

    if cached is None:
        return QIcon()

    return QIcon(
        str(cached)
    )
