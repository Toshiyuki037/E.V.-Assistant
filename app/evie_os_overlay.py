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
# E.V.I.E. MINI OVERLAY
#
# Transparent bottom-right desktop AI interface.
#
# States:
#   idle
#   listening
#   processing
#   speaking
#
# Controls:
#   0 = idle
#   1 = listening
#   2 = processing
#   3 = speaking
#   SPACE = automatic demo cycle
#   ESC = quit
# ============================================================


def clamp(value, minimum=0.0, maximum=1.0):
    return max(minimum, min(maximum, value))


class EvieOverlay(QWidget):

    ORANGE = QColor(255, 94, 12)
    ORANGE_BRIGHT = QColor(255, 132, 39)
    ORANGE_DARK = QColor(136, 38, 5)
    WHITE = QColor(247, 245, 241)

    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"

    def __init__(self):
        super().__init__()

        # ====================================================
        # WINDOW
        # ====================================================

        self.setWindowTitle("E.V.I.E.")

        # 1.5x larger than the previous 125x125 version.
        self.setFixedSize(188, 188)

        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )

        self.setAttribute(
            Qt.WA_TranslucentBackground,
            True
        )

        self.setAttribute(
            Qt.WA_NoSystemBackground,
            True
        )

        # Click-through overlay.
        self.setAttribute(
            Qt.WA_TransparentForMouseEvents,
            True
        )

        # ====================================================
        # STATE
        # ====================================================

        self.state = self.IDLE
        self.previous_state = self.IDLE

        self.state_started = time.monotonic()

        self.t = 0.0
        self.last_time = time.monotonic()

        self.listen_amount = 0.0
        self.process_amount = 0.0
        self.speak_amount = 0.0

        self.outer_rotation = 0.0
        self.middle_rotation = 0.0
        self.inner_rotation = 0.0

        self.voice = 0.0
        self.voice_target = 0.0

        # Demo sequence.
        self.demo_states = []
        self.demo_index = 0

        self.demo_timer = QTimer(self)
        self.demo_timer.setSingleShot(True)
        self.demo_timer.timeout.connect(
            self.next_demo_state
        )

        # ====================================================
        # POSITION
        # ====================================================

        self.move_to_bottom_right()

        # ====================================================
        # ANIMATION
        # ====================================================

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

        if screen is None:
            return

        geo = screen.availableGeometry()

        margin_right = 14
        margin_bottom = 14

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
    # STATE CONTROL
    # ========================================================

    def change_state(self, new_state):

        if new_state == self.state:
            return

        self.previous_state = self.state
        self.state = new_state
        self.state_started = time.monotonic()

    def set_idle(self):
        self.change_state(self.IDLE)

    def set_listening(self):
        self.change_state(self.LISTENING)

    def set_processing(self):
        self.change_state(self.PROCESSING)

    def set_speaking(self):
        self.change_state(self.SPEAKING)

    def set_voice_level(self, level):
        """
        Connect this later to real TTS audio.

        0.0 = silent
        1.0 = loud
        """

        self.voice_target = clamp(level)

    # ========================================================
    # AUTOMATIC DEMO
    # ========================================================

    def run_demo(self):

        self.demo_states = [
            (self.LISTENING, 2600),
            (self.PROCESSING, 3200),
            (self.SPEAKING, 4200),
            (self.IDLE, 1600),
        ]

        self.demo_index = 0
        self.next_demo_state()

    def next_demo_state(self):

        if self.demo_index >= len(self.demo_states):
            return

        state, duration = self.demo_states[self.demo_index]

        self.demo_index += 1

        self.change_state(state)

        self.demo_timer.start(duration)

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
        # SMOOTH STATE BLENDING
        # ----------------------------------------------------

        listen_target = (
            1.0
            if self.state == self.LISTENING
            else 0.0
        )

        process_target = (
            1.0
            if self.state == self.PROCESSING
            else 0.0
        )

        speak_target = (
            1.0
            if self.state == self.SPEAKING
            else 0.0
        )

        self.listen_amount += (
            listen_target
            - self.listen_amount
        ) * min(
            1.0,
            dt * 6.5
        )

        self.process_amount += (
            process_target
            - self.process_amount
        ) * min(
            1.0,
            dt * 7.5
        )

        self.speak_amount += (
            speak_target
            - self.speak_amount
        ) * min(
            1.0,
            dt * 7.5
        )

        # ----------------------------------------------------
        # ROTATION
        # ----------------------------------------------------

        outer_speed = (
            1.0
            + self.listen_amount * 1.2
            + self.process_amount * 5.0
            + self.speak_amount * 1.8
        )

        middle_speed = (
            -1.35
            - self.listen_amount * 0.9
            - self.process_amount * 8.0
            - self.speak_amount * 2.8
        )

        inner_speed = (
            0.8
            + self.listen_amount * 0.7
            + self.process_amount * 6.0
            + self.speak_amount * 2.3
        )

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
        # SPEAKING AUDIO SIMULATION
        # ----------------------------------------------------

        if self.state == self.SPEAKING:

            target = (
                0.10
                + 0.17 * abs(
                    math.sin(
                        self.t * 5.7
                    )
                )
                + 0.10 * abs(
                    math.sin(
                        self.t * 10.2 + 0.4
                    )
                )
                + 0.05 * abs(
                    math.sin(
                        self.t * 15.1 + 1.4
                    )
                )
            )

            # Natural pauses.
            if math.sin(
                self.t * 1.85
            ) < -0.60:
                target *= 0.15

            target += random.uniform(
                -0.012,
                0.012
            )

            self.voice_target = clamp(
                target,
                0.01,
                0.48
            )

        else:
            self.voice_target *= 0.85

        voice_speed = (
            18
            if self.voice_target > self.voice
            else 9
        )

        self.voice += (
            self.voice_target
            - self.voice
        ) * min(
            1.0,
            dt * voice_speed
        )

        self.update()

    # ========================================================
    # HELPERS
    # ========================================================

    def color(self, base, alpha):

        return QColor(
            base.red(),
            base.green(),
            base.blue(),
            int(
                255 * clamp(alpha)
            )
        )

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

        if glow:

            glow_pen = QPen(
                self.color(
                    color,
                    alpha * 0.08
                ),
                width * 4
            )

            glow_pen.setCapStyle(cap)

            painter.setPen(glow_pen)

            painter.drawArc(
                rect,
                int(-start * 16),
                int(-span * 16)
            )

        pen = QPen(
            self.color(
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

        strength = (
            1.0
            + self.listen_amount * 0.3
            + self.process_amount * 0.25
            + self.speak_amount
            * self.voice
            * 1.2
        )

        glow = QRadialGradient(
            QPointF(0, 0),
            55
        )

        glow.setColorAt(
            0.0,
            QColor(
                255,
                92,
                10,
                int(8 * strength)
            )
        )

        glow.setColorAt(
            0.6,
            QColor(
                255,
                75,
                5,
                int(4 * strength)
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
            55,
            55
        )

    # ========================================================
    # OUTER STRUCTURE
    # ========================================================

    def draw_outer(self, p):

        self.arc(
            p,
            48,
            1.45,
            self.ORANGE,
            0.95,
            glow=True
        )

        self.arc(
            p,
            45.8,
            0.40,
            self.ORANGE_BRIGHT,
            0.25
        )

        segments = [
            (18, 54),
            (104, 46),
            (179, 72),
            (283, 50),
        ]

        for start, span in segments:

            self.arc(
                p,
                43,
                0.8,
                self.ORANGE,
                0.52,
                start + self.outer_rotation,
                span
            )

    # ========================================================
    # TICKS
    # ========================================================

    def draw_ticks(self, p):

        count = 28

        for i in range(count):

            angle = math.radians(
                i * 360 / count
                + self.outer_rotation * 0.08
            )

            major = (
                i % 4 == 0
            )

            if major:

                inner = 38.0
                outer = 41.5
                width = 0.8
                alpha = 0.60

            else:

                inner = 39.2
                outer = 41.0
                width = 0.45
                alpha = 0.27

            p.setPen(
                QPen(
                    self.color(
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

        pulse = (
            1.0
            + self.listen_amount
            * (
                0.025
                + 0.018 * math.sin(
                    self.t * 3.0
                )
            )
        )

        p.save()
        p.scale(pulse, pulse)

        self.arc(
            p,
            35,
            2.8,
            self.ORANGE,
            0.80,
            glow=True
        )

        self.arc(
            p,
            32.5,
            0.45,
            self.ORANGE_DARK,
            0.65
        )

        p.restore()

        rot = self.middle_rotation

        segments = [
            (rot + 8, 50),
            (rot + 81, 23),
            (rot + 126, 58),
            (rot + 211, 31),
            (rot + 267, 66),
        ]

        for index, (
            start,
            span
        ) in enumerate(segments):

            active = self.process_amount

            width = (
                0.8
                + active
                * (
                    0.7
                    if index % 2 == 0
                    else 0.25
                )
            )

            alpha = (
                0.32
                + (
                    0.22
                    if index % 2 == 0
                    else 0.10
                )
                + active * 0.18
            )

            self.arc(
                p,
                30.5,
                width,
                self.ORANGE_BRIGHT,
                alpha,
                start,
                span,
                glow=(
                    active > 0.4
                    and index == 0
                )
            )

    # ========================================================
    # CORE
    # ========================================================

    def draw_core(self, p):

        core = QRadialGradient(
            QPointF(-2, -3),
            29
        )

        core.setColorAt(
            0.0,
            QColor(
                34,
                19,
                14,
                205
            )
        )

        core.setColorAt(
            0.55,
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
            26,
            26
        )

        self.arc(
            p,
            26,
            1.35,
            self.ORANGE,
            0.90,
            glow=True
        )

        self.arc(
            p,
            23.5,
            0.38,
            self.ORANGE_BRIGHT,
            0.32
        )

        rot = self.inner_rotation

        self.arc(
            p,
            21.3,
            0.65,
            self.ORANGE,
            0.27,
            rot + 10,
            80
        )

        self.arc(
            p,
            21.3,
            0.65,
            self.ORANGE,
            0.23,
            rot + 132,
            46
        )

        self.arc(
            p,
            21.3,
            0.65,
            self.ORANGE,
            0.30,
            rot + 224,
            96
        )

    # ========================================================
    # LISTENING PHASE
    # ========================================================

    def draw_listening(self, p):

        amount = self.listen_amount

        if amount < 0.01:
            return

        sweep = (
            38
            + 9 * math.sin(
                self.t * 1.8
            )
        )

        rotation = (
            self.t * 16
        ) % 360

        self.arc(
            p,
            44.5,
            0.85,
            self.WHITE,
            amount * 0.25,
            rotation,
            sweep,
            glow=False
        )

        self.arc(
            p,
            40.8,
            1.0,
            self.ORANGE_BRIGHT,
            amount * 0.40,
            rotation + 178,
            28,
            glow=True
        )

        pulse = (
            1.0
            + 0.025 * math.sin(
                self.t * 2.5
            )
        )

        self.arc(
            p,
            27.5 * pulse,
            0.55,
            self.ORANGE,
            amount * 0.20
        )

    # ========================================================
    # PROCESSING PHASE
    # ========================================================

    def draw_processing(self, p):

        amount = self.process_amount

        if amount < 0.01:
            return

        scan = (
            self.t * 105
        ) % 360

        self.arc(
            p,
            33,
            1.15,
            self.ORANGE_BRIGHT,
            amount * 0.66,
            scan,
            31,
            glow=True
        )

        scan2 = (
            -self.t * 68
        ) % 360

        self.arc(
            p,
            28.5,
            0.75,
            self.ORANGE,
            amount * 0.45,
            scan2,
            52
        )

        for i in range(6):

            angle = math.radians(
                scan
                + i * 60
            )

            radius = 46

            x = (
                math.cos(angle)
                * radius
            )

            y = (
                math.sin(angle)
                * radius
            )

            opacity = (
                amount
                * (
                    0.55
                    - i * 0.065
                )
            )

            p.setPen(Qt.NoPen)

            p.setBrush(
                self.color(
                    self.ORANGE_BRIGHT,
                    opacity
                )
            )

            p.drawEllipse(
                QPointF(x, y),
                0.65,
                0.65
            )

    # ========================================================
    # SPEAKING PHASE
    # ========================================================

    def draw_speaking(self, p):

        amount = self.speak_amount

        if (
            amount < 0.01
            or self.voice < 0.01
        ):
            return

        count = 18

        for i in range(count):

            angle = math.radians(
                i * 360 / count
            )

            phase = (
                0.5
                + 0.5 * math.sin(
                    self.t * 8.4
                    + i * 0.71
                )
            )

            amplitude = (
                self.voice
                * phase
                * amount
            )

            inner = 27.3

            outer = (
                inner
                + 0.8
                + amplitude * 5.5
            )

            opacity = (
                0.10
                + amplitude * 0.68
            )

            p.setPen(
                QPen(
                    self.color(
                        self.ORANGE_BRIGHT,
                        opacity
                    ),
                    0.55
                    + amplitude * 0.8
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

        self.arc(
            p,
            27 + self.voice * 1.8,
            0.55 + self.voice * 0.5,
            self.ORANGE_BRIGHT,
            amount
            * self.voice
            * 0.30,
            glow=True
        )

    # ========================================================
    # SMALL DETAIL MARKER
    # ========================================================

    def draw_marker(self, p):

        angle = math.radians(217)

        for i in range(3):

            radius = (
                45
                - i * 2.2
            )

            x = (
                math.cos(angle)
                * radius
            )

            y = (
                math.sin(angle)
                * radius
            )

            size = (
                0.75
                if i == 0
                else 0.45
            )

            p.setPen(Qt.NoPen)

            p.setBrush(
                self.color(
                    self.ORANGE_BRIGHT,
                    0.9
                    - i * 0.2
                )
            )

            p.drawEllipse(
                QPointF(x, y),
                size,
                size
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
    # WORDMARK
    # ========================================================

    def draw_wordmark(self, p):

        font = QFont(
            self.choose_font()
        )

        font.setPointSizeF(7.0)

        font.setWeight(
            QFont.Weight.DemiBold
        )

        font.setStretch(112)

        font.setLetterSpacing(
            QFont.SpacingType.AbsoluteSpacing,
            0.55
        )

        p.setFont(font)

        rect = QRectF(
            -29,
            -8,
            58,
            16
        )

        p.setPen(
            QColor(
                0,
                0,
                0,
                225
            )
        )

        offsets = [
            (-0.65, 0),
            (0.65, 0),
            (0, -0.65),
            (0, 0.65),
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

        p.setPen(
            QColor(
                247,
                247,
                244,
                250
            )
        )

        p.drawText(
            rect,
            Qt.AlignCenter,
            "E.V.I.E."
        )

    # ========================================================
    # PAINT EVENT
    # ========================================================

    def paintEvent(self, event):

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

            # Center the original 125x125 design
            # inside the larger 188x188 overlay.
            p.translate(
                self.width() / 2,
                self.height() / 2
            )

            # Scale entire design up by 1.5x.
            p.scale(
                1.5,
                1.5
            )

            # Tiny organic motion.
            p.translate(
                0.08
                * math.sin(
                    self.t * 0.35
                ),
                0.12
                * math.sin(
                    self.t * 0.41 + 0.7
                )
            )

            # Listening gently breathes.
            listening_breath = (
                self.listen_amount
                * 0.006
                * math.sin(
                    self.t * 2.2
                )
            )

            # Speaking subtly reacts to voice.
            voice_scale = (
                self.voice
                * self.speak_amount
                * 0.003
            )

            scale = (
                1.0
                + listening_breath
                + voice_scale
            )

            p.scale(
                scale,
                scale
            )

            # Fully transparent background.
            self.draw_glow(p)

            self.draw_outer(p)
            self.draw_ticks(p)
            self.draw_marker(p)

            self.draw_middle(p)

            self.draw_listening(p)
            self.draw_processing(p)

            self.draw_core(p)

            self.draw_speaking(p)

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
            self.set_processing()

        elif key == Qt.Key_3:
            self.set_speaking()

        elif key == Qt.Key_Space:
            self.run_demo()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    app = QApplication(sys.argv)

    app.setQuitOnLastWindowClosed(True)

    evie = EvieOverlay()

    # Uncomment this if you want E.V.I.E. to automatically
    # demonstrate:
    #
    # listening -> processing -> speaking -> idle
    #
    # QTimer.singleShot(500, evie.run_demo)

    sys.exit(app.exec())