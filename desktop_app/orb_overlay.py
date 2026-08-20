from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import (
    QTimer,
    Qt,
    Slot,
)
from PySide6.QtGui import (
    QCursor,
    QPainter,
    QPixmap,
)
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
)


DESKTOP_APP_DIR = Path(__file__).resolve().parent
ORB_ASSETS_DIR = DESKTOP_APP_DIR / "assets" / "orb"

ORB_STATE_DIRS = {
    "listening": ORB_ASSETS_DIR / "listening",
    "thinking": ORB_ASSETS_DIR / "thinking",
    "speaking": ORB_ASSETS_DIR / "speaking",
}


class EvieOrbOverlay(QWidget):
    """
    Transparent E.V.I.E. desktop orb.

    Improvements in this version:
      * seamless loop crossfades instead of last-frame -> first-frame jumps
      * state-to-state crossfades instead of restarting visually
      * wake_heard state fades the listening orb in before authentication
      * no disk reads during playback
    """

    FRAME_INTERVAL_MS = 33

    # User requested 50% of the original overlay size.
    OVERLAY_SIZE = 135
    RENDER_SIZE = 125

    MARGIN_RIGHT = 24
    MARGIN_BOTTOM = 24

    # Number of frames used to blend the end of a sequence into its beginning.
    # 8 @ 30 fps ~= 267 ms, enough to remove the obvious reload without
    # making the animation look blurry.
    LOOP_BLEND_FRAMES = 8

    # State transitions are blended for roughly 230 ms.
    STATE_BLEND_MS = 230

    STATE_ALIASES = {
        "wake heard": "listening",
        "wake_heard": "listening",

        "listening": "listening",

        "thinking": "thinking",
        "processing": "thinking",
        "acting": "thinking",
        "finalizing": "thinking",

        "speaking": "speaking",
    }

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("E.V.I.E. Orb")

        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.WindowDoesNotAcceptFocus
        )

        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        self.setFixedSize(
            self.OVERLAY_SIZE,
            self.OVERLAY_SIZE,
        )

        self._frames: dict[str, list[QPixmap]] = {
            "listening": [],
            "thinking": [],
            "speaking": [],
        }

        self._assets_ready = False

        self._state = "hidden"
        self._frame_pos = 0.0

        self._current_pixmap = QPixmap()

        # Cross-state blend source.
        self._transition_source = QPixmap()
        self._transition_progress = 1.0
        self._transition_elapsed_ms = 0

        # Window fade.
        self._opacity = 0.0
        self._fade_target = 0.0
        self._fade_speed = 0.18

        self.frame_timer = QTimer(self)
        self.frame_timer.setTimerType(Qt.PreciseTimer)
        self.frame_timer.setInterval(self.FRAME_INTERVAL_MS)
        self.frame_timer.timeout.connect(self._advance_frame)

        self.fade_timer = QTimer(self)
        self.fade_timer.setInterval(16)
        self.fade_timer.timeout.connect(self._fade_tick)

        self._preload_frames()
        self.move_to_bottom_right()
        self.hide()

    # ------------------------------------------------------------------
    # Assets
    # ------------------------------------------------------------------

    def _preload_frames(self):
        missing = []

        for state, folder in ORB_STATE_DIRS.items():
            paths = []

            if folder.exists():
                paths = sorted(
                    (
                        p
                        for p in folder.iterdir()
                        if p.is_file()
                        and p.suffix.lower() == ".png"
                    ),
                    key=self._frame_sort_key,
                )

            loaded = []

            for path in paths:
                pixmap = QPixmap(str(path))

                if pixmap.isNull():
                    continue

                loaded.append(
                    pixmap.scaled(
                        self.RENDER_SIZE,
                        self.RENDER_SIZE,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation,
                    )
                )

            self._frames[state] = loaded

            if not loaded:
                missing.append(str(folder))

        self._assets_ready = all(
            self._frames[state]
            for state in ("listening", "thinking", "speaking")
        )

        if not self._assets_ready:
            print("[E.V.I.E. orb] Animation assets missing or unreadable:")
            for path in missing:
                print(f"  - {path}")
            return

        print(
            "[E.V.I.E. orb] Preloaded "
            f"{len(self._frames['listening'])} listening, "
            f"{len(self._frames['thinking'])} thinking, "
            f"{len(self._frames['speaking'])} speaking frames."
        )

    @staticmethod
    def _frame_sort_key(path: Path):
        try:
            return (0, int(path.stem))
        except ValueError:
            return (1, path.name.lower())

    # ------------------------------------------------------------------
    # Runtime state
    # ------------------------------------------------------------------

    @Slot(str, str)
    def set_runtime_state(self, state, detail=""):
        normalized = (
            str(state or "")
            .strip()
            .lower()
            .replace("_", " ")
        )

        target = self.STATE_ALIASES.get(normalized)

        if target is not None:
            self.show_state(target)
            return

        if normalized in {
            "standing by",
            "idle",
            "starting",
            "error",
            "",
        }:
            self.hide_orb()

    def show_state(self, state):
        if not self._assets_ready:
            return

        frames = self._frames.get(state, [])
        if not frames:
            return

        if state != self._state:
            # Preserve the exact current visual as the transition source.
            if not self._current_pixmap.isNull():
                self._transition_source = self._current_pixmap
                self._transition_progress = 0.0
                self._transition_elapsed_ms = 0
            else:
                self._transition_source = QPixmap()
                self._transition_progress = 1.0

            # Don't always start at authored frame zero. Start the new state at
            # the equivalent normalized phase of the old state so the internal
            # field does not visibly snap back to its beginning.
            old_frames = self._frames.get(self._state, [])
            phase = 0.0

            if old_frames:
                phase = (
                    self._frame_pos
                    % len(old_frames)
                ) / max(1, len(old_frames))

            self._frame_pos = phase * len(frames)
            self._state = state
            self._update_current_pixmap()

        self._fade_target = 1.0

        if not self.isVisible():
            self.move_to_bottom_right()
            self._opacity = 0.0
            self.show()
            self.raise_()
            self.fade_timer.start()

        if not self.frame_timer.isActive():
            self.frame_timer.start()

        self.update()

    def hide_orb(self):
        if not self.isVisible():
            self.frame_timer.stop()
            self._state = "hidden"
            return

        self._fade_target = 0.0
        if not self.fade_timer.isActive():
            self.fade_timer.start()

    # ------------------------------------------------------------------
    # Animation
    # ------------------------------------------------------------------

    def _advance_frame(self):
        frames = self._frames.get(self._state, [])
        if not frames:
            return

        self._frame_pos += 1.0

        if self._frame_pos >= len(frames):
            self._frame_pos -= len(frames)

        if self._transition_progress < 1.0:
            self._transition_elapsed_ms += self.FRAME_INTERVAL_MS
            self._transition_progress = min(
                1.0,
                self._transition_elapsed_ms / self.STATE_BLEND_MS,
            )

            if self._transition_progress >= 1.0:
                self._transition_source = QPixmap()

        self._update_current_pixmap()
        self.update()

    def _update_current_pixmap(self):
        frames = self._frames.get(self._state, [])

        if not frames:
            self._current_pixmap = QPixmap()
            return

        count = len(frames)
        index = int(self._frame_pos) % count

        # Near the end of each animation, crossfade toward the corresponding
        # beginning frame. This removes the visible frame-80 -> frame-1 reset.
        blend_start = max(
            0,
            count - self.LOOP_BLEND_FRAMES,
        )

        if (
            self.LOOP_BLEND_FRAMES > 0
            and index >= blend_start
            and count > self.LOOP_BLEND_FRAMES
        ):
            local = (
                index - blend_start
            ) / max(
                1,
                self.LOOP_BLEND_FRAMES - 1,
            )

            beginning_index = (
                index - blend_start
            ) % count

            self._current_pixmap = self._blend_pixmaps(
                frames[index],
                frames[beginning_index],
                local,
            )

        else:
            self._current_pixmap = frames[index]

    def _blend_pixmaps(self, a: QPixmap, b: QPixmap, amount: float):
        if a.isNull():
            return b

        if b.isNull():
            return a

        amount = max(
            0.0,
            min(
                1.0,
                float(amount),
            ),
        )

        result = QPixmap(
            self.RENDER_SIZE,
            self.RENDER_SIZE,
        )
        result.fill(Qt.transparent)

        painter = QPainter(result)

        try:
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

            painter.setOpacity(1.0)
            painter.drawPixmap(0, 0, a)

            painter.setOpacity(amount)
            painter.drawPixmap(0, 0, b)

        finally:
            painter.end()

        return result

    def _fade_tick(self):
        difference = self._fade_target - self._opacity

        if abs(difference) < 0.02:
            self._opacity = self._fade_target
            self.fade_timer.stop()

            if self._opacity <= 0.0:
                self.frame_timer.stop()
                self._state = "hidden"
                self._frame_pos = 0.0
                self._current_pixmap = QPixmap()
                self._transition_source = QPixmap()
                self.hide()

            self.update()
            return

        self._opacity += difference * self._fade_speed
        self.update()

    # ------------------------------------------------------------------
    # Position / paint
    # ------------------------------------------------------------------

    def move_to_bottom_right(self):
        screen = None

        try:
            screen = QApplication.screenAt(
                QCursor.pos()
            )
        except Exception:
            screen = None

        if screen is None:
            screen = QApplication.primaryScreen()

        if screen is None:
            return

        geo = screen.availableGeometry()

        self.move(
            geo.right()
            - self.width()
            - self.MARGIN_RIGHT
            + 1,
            geo.bottom()
            - self.height()
            - self.MARGIN_BOTTOM
            + 1,
        )

    def paintEvent(self, event):
        if (
            self._current_pixmap.isNull()
            or self._opacity <= 0.0
        ):
            return

        painter = QPainter(self)

        try:
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

            painter.setOpacity(
                max(
                    0.0,
                    min(1.0, self._opacity),
                )
            )

            x = (
                self.width()
                - self._current_pixmap.width()
            ) // 2

            y = (
                self.height()
                - self._current_pixmap.height()
            ) // 2

            # During a state change, softly retain the previous rendered frame
            # beneath the new state. This is what prevents a visible reload.
            if (
                not self._transition_source.isNull()
                and self._transition_progress < 1.0
            ):
                painter.setOpacity(
                    self._opacity
                    * (1.0 - self._transition_progress)
                )
                painter.drawPixmap(
                    x,
                    y,
                    self._transition_source,
                )

                painter.setOpacity(
                    self._opacity
                    * self._transition_progress
                )

            else:
                painter.setOpacity(self._opacity)

            painter.drawPixmap(
                x,
                y,
                self._current_pixmap,
            )

        finally:
            painter.end()

    def shutdown(self):
        self.frame_timer.stop()
        self.fade_timer.stop()
        self.hide()
        self.close()
