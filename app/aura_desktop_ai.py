import sys
import math
import time
import random

from PySide6.QtCore import Qt, QTimer, QRectF, QPointF
from PySide6.QtGui import (
    QColor,
    QPainter,
    QPen,
    QBrush,
    QFont,
    QFontDatabase,
    QRadialGradient,
)
from PySide6.QtWidgets import QApplication, QWidget


# ============================================================
# E.V.I.E.
# Minimal transparent F.R.I.D.A.Y.-style desktop overlay
#
# Controls:
#   0 = idle
#   1 = listening
#   2 = thinking
#   3 = speaking
#   H = hide/show
#   ESC = quit
# ============================================================


def clamp(value, minimum=0.0, maximum=1.0):
    return max(minimum, min(maximum, value))


class EvieOverlay(QWidget):

    # --------------------------------------------------------
    # COLORS
    # --------------------------------------------------------

    ORANGE = QColor(255, 94, 12)
    ORANGE_BRIGHT = QColor(255, 126, 32)
    ORANGE_DARK = QColor(150, 43, 5)

    WHITE = QColor(246, 245, 242)

    # --------------------------------------------------------
    # WINDOW
    # --------------------------------------------------------

    def __init__(self):
        super().__init__()

        self.setWindowTitle("E.V.I.E.")

        # Small desktop-overlay footprint.
        self.setFixedSize(250, 250)

        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )

        # Fully transparent window.
        self.setAttribute(
            Qt.WA_TranslucentBackground,
            True
        )

        self.setAttribute(
            Qt.WA_NoSystemBackground,
            True
        )

        # Makes it behave more like an overlay and not steal mouse clicks.
        self.setAttribute(
            Qt.WA_TransparentForMouseEvents,
            True
        )

        # ----------------------------------------------------
        # STATE
        # ----------------------------------------------------

        self.state = "idle"

        self.visible_hud = True

        self.t = 0.0
        self.last_time = time.monotonic()

        self.outer_rotation = 0.0
        self.middle_rotation = 0.0
        self.inner_rotation = 0.0

        self.voice = 0.0
        self.voice_target = 0.0

        # ----------------------------------------------------
        # POSITION
        # ----------------------------------------------------

        self.move_to_bottom_right()

        # ----------------------------------------------------
        # TIMER
        # ----------------------------------------------------

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(16)

        self.show()
        self.raise_()

    # ========================================================
    # POSITION
    # ========================================================

    def move_to_bottom_right(self):

        screen = QApplication.primaryScreen()

        if not screen:
            return

        geo = screen.availableGeometry()

        # Distance from Windows taskbar/screen edge.
        margin_right = 18
        margin_bottom = 18

        x = (
            geo.right()
            - self.width()
            - margin_right
            + 1
        )

        y = (
            geo.bottom()
            - self.height()
            - margin_bottom
            + 1
        )

        self.move(x, y)

    # ========================================================
    # STATES
    # ========================================================

    def set_idle(self):
        self.state = "idle"

    def set_listening(self):
        self.state = "listening"

    def set_thinking(self):
        self.state = "thinking"

    def set_speaking(self):
        self.state = "speaking"

    def set_voice_level(self, level):
        """
        Use this later with your real TTS audio.

        level:
            0.0 = silent
            1.0 = maximum
        """

        self.voice_target = clamp(level)

    # ========================================================
    # ANIMATION
    # ========================================================

    def tick(self):

        now = time.monotonic()

        dt = min(
            0.04,
            now - self.last_time
        )

        self.last_time = now
        self.t += dt

        # ----------------------------------------------------
        # VERY SLOW IDLE MOVEMENT
        # ----------------------------------------------------

        if self.state == "idle":

            outer_speed = 1.2
            middle_speed = -1.8
            inner_speed = 1.1

        elif self.state == "listening":

            outer_speed = 1.8
            middle_speed = -2.7
            inner_speed = 1.6

        elif self.state == "thinking":

            outer_speed = 3.0
            middle_speed = -6.0
            inner_speed = 4.0

        else:  # speaking

            outer_speed = 2.0
            middle_speed = -3.6
            inner_speed = 2.5

        self.outer_rotation += (
            dt * outer_speed
        )

        self.middle_rotation += (
            dt * middle_speed
        )

        self.inner_rotation += (
            dt * inner_speed
        )

        # ----------------------------------------------------
        # SPEECH
        # ----------------------------------------------------

        if self.state == "speaking":

            # Demo voice animation.
            #
            # Remove this block later if you drive
            # set_voice_level() from real TTS audio.

            target = (
                0.13
                + 0.13 * abs(
                    math.sin(self.t * 5.4)
                )
                + 0.08 * abs(
                    math.sin(
                        self.t * 9.3 + 0.7
                    )
                )
                + random.uniform(
                    -0.012,
                    0.012
                )
            )

            # Natural pauses.
            if (
                math.sin(self.t * 1.75)
                < -0.62
            ):
                target *= 0.15

            self.voice_target = clamp(
                target,
                0.01,
                0.45
            )

        else:

            self.voice_target *= 0.88

        speed = (
            14
            if self.voice_target > self.voice
            else 8
        )

        self.voice += (
            self.voice_target
            - self.voice
        ) * min(
            1.0,
            dt * speed
        )

        self.update()

    # ========================================================
    # COLOR HELPER
    # ========================================================

    def alpha_color(
        self,
        color,
        alpha
    ):

        return QColor(
            color.red(),
            color.green(),
            color.blue(),
            int(
                255 * clamp(alpha)
            )
        )

    # ========================================================
    # ARC
    # ========================================================

    def arc(
        self,
        painter,
        radius,
        width,
        color,
        alpha,
        start=0,
        span=360,
        glow=False,
        cap=Qt.FlatCap
    ):

        rect = QRectF(
            -radius,
            -radius,
            radius * 2,
            radius * 2
        )

        # Very restrained glow.
        if glow:

            glow_pen = QPen(
                self.alpha_color(
                    color,
                    alpha * 0.08
                ),
                width * 4.2
            )

            glow_pen.setCapStyle(cap)

            painter.setPen(
                glow_pen
            )

            painter.drawArc(
                rect,
                int(-start * 16),
                int(-span * 16)
            )

        pen = QPen(
            self.alpha_color(
                color,
                alpha
            ),
            width
        )

        pen.setCapStyle(cap)

        painter.setPen(pen)

        painter.drawArc(
            rect,
            int(-start * 16),
            int(-span * 16)
        )

    # ========================================================
    # AMBIENT GLOW
    # ========================================================

    def draw_glow(self, p):

        glow = QRadialGradient(
            QPointF(0, 0),
            108
        )

        glow.setColorAt(
            0.0,
            QColor(
                255,
                88,
                8,
                7
            )
        )

        glow.setColorAt(
            0.62,
            QColor(
                255,
                72,
                5,
                3
            )
        )

        glow.setColorAt(
            1.0,
            QColor(
                255,
                60,
                0,
                0
            )
        )

        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(glow))

        p.drawEllipse(
            QPointF(0, 0),
            108,
            108
        )

    # ========================================================
    # OUTER RING
    # ========================================================

    def draw_outer_ring(self, p):

        rotation = (
            self.outer_rotation
        )

        # Main bright outer border.
        self.arc(
            p,
            96,
            2.7,
            self.ORANGE,
            0.96,
            glow=True
        )

        # Subtle secondary outline.
        self.arc(
            p,
            91.5,
            0.65,
            self.ORANGE_BRIGHT,
            0.25
        )

        # Broken architectural segments.
        segments = [
            (18, 58),
            (103, 50),
            (177, 78),
            (280, 53),
        ]

        for start, span in segments:

            self.arc(
                p,
                86,
                1.35,
                self.ORANGE,
                0.55,
                start + rotation,
                span
            )

    # ========================================================
    # OUTER TICKS
    # ========================================================

    def draw_ticks(self, p):

        # Less dense than previous version.
        count = 32

        for i in range(count):

            angle = math.radians(
                i * 360 / count
                + self.outer_rotation * 0.10
            )

            if i % 4 == 0:

                outer = 82
                inner = 76.5

                alpha = 0.65
                width = 1.1

            else:

                outer = 81
                inner = 78

                alpha = 0.28
                width = 0.65

            p.setPen(
                QPen(
                    self.alpha_color(
                        self.ORANGE_BRIGHT,
                        alpha
                    ),
                    width
                )
            )

            p.drawLine(
                QPointF(
                    math.cos(angle) * inner,
                    math.sin(angle) * inner
                ),
                QPointF(
                    math.cos(angle) * outer,
                    math.sin(angle) * outer
                )
            )

    # ========================================================
    # MIDDLE STRUCTURE
    # ========================================================

    def draw_middle(self, p):

        rot = self.middle_rotation

        # Thick orange ring.
        self.arc(
            p,
            70,
            5.5,
            self.ORANGE,
            0.82,
            glow=True
        )

        # Slight dark separation.
        self.arc(
            p,
            65,
            0.7,
            self.ORANGE_DARK,
            0.70
        )

        # Segmented mechanical ring.
        segments = [
            (rot + 8, 51),
            (rot + 78, 24),
            (rot + 121, 63),
            (rot + 207, 35),
            (rot + 264, 72)
        ]

        for index, (
            start,
            span
        ) in enumerate(segments):

            self.arc(
                p,
                61,
                (
                    2.2
                    if index in (0, 2, 4)
                    else 1.0
                ),
                self.ORANGE_BRIGHT,
                (
                    0.58
                    if index in (0, 2, 4)
                    else 0.34
                ),
                start,
                span,
                glow=False
            )

    # ========================================================
    # CORE
    # ========================================================

    def draw_core(self, p):

        # Transparent-looking dark center.
        #
        # It is dark enough to make E.V.I.E. readable,
        # but it doesn't create a giant black square.

        core = QRadialGradient(
            QPointF(-5, -8),
            57
        )

        core.setColorAt(
            0.0,
            QColor(
                35,
                19,
                14,
                205
            )
        )

        core.setColorAt(
            0.52,
            QColor(
                14,
                9,
                8,
                218
            )
        )

        core.setColorAt(
            1.0,
            QColor(
                4,
                3,
                3,
                225
            )
        )

        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(core))

        p.drawEllipse(
            QPointF(0, 0),
            52,
            52
        )

        # Main inner orange border.
        self.arc(
            p,
            52,
            2.7,
            self.ORANGE,
            0.88,
            glow=True
        )

        self.arc(
            p,
            47,
            0.7,
            self.ORANGE_BRIGHT,
            0.35
        )

        # Rotating internal geometry.
        rot = self.inner_rotation

        self.arc(
            p,
            43,
            1.1,
            self.ORANGE,
            0.30,
            rot + 12,
            81
        )

        self.arc(
            p,
            43,
            1.1,
            self.ORANGE,
            0.24,
            rot + 129,
            48
        )

        self.arc(
            p,
            43,
            1.1,
            self.ORANGE,
            0.32,
            rot + 223,
            97
        )

        self.arc(
            p,
            37,
            0.55,
            self.ORANGE_DARK,
            0.47
        )

    # ========================================================
    # LITTLE REFERENCE-STYLE MARKER
    # ========================================================

    def draw_marker(self, p):

        # Small detail around the lower-left side,
        # similar to the reference image.

        angle = math.radians(217)

        for i in range(3):

            r = 90 - i * 4

            x = math.cos(angle) * r
            y = math.sin(angle) * r

            size = (
                1.5
                if i == 0
                else 0.9
            )

            p.setPen(Qt.NoPen)

            p.setBrush(
                self.alpha_color(
                    self.ORANGE_BRIGHT,
                    0.92 - i * 0.20
                )
            )

            p.drawEllipse(
                QPointF(x, y),
                size,
                size
            )

    # ========================================================
    # LISTENING
    # ========================================================

    def draw_listening(self, p):

        if self.state != "listening":
            return

        pulse = (
            0.70
            + 0.15
            * math.sin(
                self.t * 2.1
            )
        )

        self.arc(
            p,
            88.5,
            1.1,
            self.WHITE,
            0.20 * pulse,
            198,
            43,
            glow=False
        )

    # ========================================================
    # THINKING
    # ========================================================

    def draw_thinking(self, p):

        if self.state != "thinking":
            return

        scan = (
            self.t * 42
        ) % 360

        self.arc(
            p,
            64,
            1.7,
            self.ORANGE_BRIGHT,
            0.48,
            scan,
            34,
            glow=True
        )

    # ========================================================
    # SPEAKING
    # ========================================================

    def draw_speaking(self, p):

        if self.state != "speaking":
            return

        if self.voice < 0.015:
            return

        # Very restrained speech response.
        #
        # Only tiny marks just outside the center ring.

        count = 16

        for i in range(count):

            angle = math.radians(
                i * 360 / count
            )

            phase = (
                0.5
                + 0.5
                * math.sin(
                    self.t * 7.5
                    + i * 0.82
                )
            )

            amount = (
                self.voice
                * phase
            )

            r1 = 54
            r2 = (
                r1
                + 1.5
                + amount * 6
            )

            p.setPen(
                QPen(
                    self.alpha_color(
                        self.ORANGE_BRIGHT,
                        0.12
                        + amount * 0.50
                    ),
                    0.8
                )
            )

            p.drawLine(
                QPointF(
                    math.cos(angle) * r1,
                    math.sin(angle) * r1
                ),
                QPointF(
                    math.cos(angle) * r2,
                    math.sin(angle) * r2
                )
            )

    # ========================================================
    # FONT
    # ========================================================

    def choose_font(self):

        installed = set(
            QFontDatabase.families()
        )

        candidates = [
            "Eurostile",
            "Microgramma D Extended",
            "Bank Gothic",
            "Square 721",
            "Orbitron",
            "Michroma",
            "Bahnschrift",
            "Arial",
        ]

        for family in candidates:

            if family in installed:
                return family

        return "Arial"

    # ========================================================
    # E.V.I.E. WORDMARK
    # ========================================================

    def draw_wordmark(self, p):

        font = QFont(
            self.choose_font()
        )

        font.setPointSizeF(13.5)

        font.setWeight(
            QFont.Weight.DemiBold
        )

        font.setStretch(112)

        font.setLetterSpacing(
            QFont.SpacingType.AbsoluteSpacing,
            1.1
        )

        p.setFont(font)

        rect = QRectF(
            -54,
            -16,
            108,
            32
        )

        # Dark outline/shadow.
        p.setPen(
            QColor(
                0,
                0,
                0,
                230
            )
        )

        offsets = [
            (-1.1, 0),
            (1.1, 0),
            (0, -1.1),
            (0, 1.1),
        ]

        for ox, oy in offsets:

            p.drawText(
                QRectF(
                    rect.x() + ox,
                    rect.y() + oy,
                    rect.width(),
                    rect.height()
                ),
                Qt.AlignCenter,
                "E.V.I.E."
            )

        # Main white text.
        p.setPen(
            QColor(
                self.WHITE.red(),
                self.WHITE.green(),
                self.WHITE.blue(),
                250
            )
        )

        p.drawText(
            rect,
            Qt.AlignCenter,
            "E.V.I.E."
        )

    # ========================================================
    # PAINT
    # ========================================================

    def paintEvent(self, event):

        if not self.visible_hud:
            return

        p = QPainter(self)

        try:

            p.setRenderHint(
                QPainter.Antialiasing,
                True
            )

            p.setRenderHint(
                QPainter.TextAntialiasing,
                True
            )

            p.translate(
                self.width() / 2,
                self.height() / 2
            )

            # Very subtle floating/breathing effect.
            drift_x = (
                math.sin(
                    self.t * 0.34
                ) * 0.18
            )

            drift_y = (
                math.sin(
                    self.t * 0.41 + 0.7
                ) * 0.25
            )

            p.translate(
                drift_x,
                drift_y
            )

            breath = (
                1.0
                + math.sin(
                    self.t * 1.05
                ) * 0.0015
                + self.voice * 0.0015
            )

            p.scale(
                breath,
                breath
            )

            # --------------------------------------------
            # NO BACKGROUND RECTANGLE.
            # Everything outside the circles is transparent.
            # --------------------------------------------

            self.draw_glow(p)

            self.draw_outer_ring(p)

            self.draw_ticks(p)

            self.draw_marker(p)

            self.draw_middle(p)

            self.draw_speaking(p)

            self.draw_core(p)

            self.draw_listening(p)

            self.draw_thinking(p)

            self.draw_wordmark(p)

        finally:

            p.end()

    # ========================================================
    # KEYBOARD
    # ========================================================

    def keyPressEvent(self, event):

        key = event.key()

        if key == Qt.Key_Escape:

            QApplication.quit()

        elif key == Qt.Key_0:

            self.set_idle()

        elif key == Qt.Key_1:

            self.set_listening()

        elif key == Qt.Key_2:

            self.set_thinking()

        elif key == Qt.Key_3:

            self.set_speaking()

        elif key == Qt.Key_H:

            self.visible_hud = (
                not self.visible_hud
            )

            self.update()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    app = QApplication(sys.argv)

    app.setQuitOnLastWindowClosed(
        True
    )

    evie = EvieOverlay()

    sys.exit(
        app.exec()
    )