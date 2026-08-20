from __future__ import annotations

import math

from PySide6.QtCore import (
    Qt,
    QRectF,
    QTimer,
    Signal,
)

from PySide6.QtGui import (
    QColor,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)


class InsightTile(QWidget):
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.phase = 0.0

        # Dashboard now uses a narrow operational column. The original square
        # tile looked pinched/tall there, so this is intentionally landscape.
        self.setMinimumSize(
            300,
            160,
        )

        self.setMaximumHeight(
            190
        )

        self.setSizePolicy(
            __import__(
                "PySide6.QtWidgets",
                fromlist=["QSizePolicy"],
            ).QSizePolicy(
                __import__(
                    "PySide6.QtWidgets",
                    fromlist=["QSizePolicy"],
                ).QSizePolicy.Expanding,
                __import__(
                    "PySide6.QtWidgets",
                    fromlist=["QSizePolicy"],
                ).QSizePolicy.Fixed,
            )
        )

        self.setCursor(
            Qt.PointingHandCursor
        )

        self.title = "E.V.I.E. Insight"
        self.subtitle = "Waiting for verified runtime data..."

        self.timer = QTimer(self)
        self.timer.timeout.connect(
            self.tick
        )
        self.timer.start(
            33
        )

    def tick(self):
        # ~7 second full breathing cycle.
        self.phase = (
            self.phase
            + 0.0048
        ) % 1.0

        self.update()

    def set_insight(
        self,
        title: str,
        subtitle: str,
    ):
        self.title = str(
            title
            or "E.V.I.E. Insight"
        )

        self.subtitle = str(
            subtitle
            or ""
        )

        self.update()

    def mouseReleaseEvent(
        self,
        event,
    ):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
            event.accept()
            return

        super().mouseReleaseEvent(
            event
        )

    def paintEvent(
        self,
        event,
    ):
        painter = QPainter(
            self
        )

        painter.setRenderHint(
            QPainter.Antialiasing
        )

        rect = QRectF(
            self.rect()
        ).adjusted(
            0,
            0,
            -1,
            -1,
        )

        theta = (
            self.phase
            * math.tau
        )

        breathe = (
            0.5
            - 0.5
            * math.cos(
                theta
            )
        )

        drift = (
            0.5
            + 0.5
            * math.sin(
                theta
            )
        )

        reverse = (
            0.5
            + 0.5
            * math.sin(
                theta
                + math.pi * 0.65
            )
        )

        start_x = (
            rect.left()
            + rect.width()
            * (
                -0.15
                + 0.28
                * drift
            )
        )

        start_y = (
            rect.top()
            + rect.height()
            * (
                0.02
                + 0.20
                * reverse
            )
        )

        end_x = (
            rect.right()
            - rect.width()
            * (
                -0.05
                + 0.17
                * reverse
            )
        )

        end_y = (
            rect.bottom()
            - rect.height()
            * (
                0.00
                + 0.18
                * drift
            )
        )

        gradient = QLinearGradient(
            start_x,
            start_y,
            end_x,
            end_y,
        )

        gradient.setColorAt(
            0.0,
            QColor(
                145 + int(25 * breathe),
                125 + int(18 * reverse),
                236,
            ),
        )

        gradient.setColorAt(
            0.30,
            QColor(
                196 + int(16 * reverse),
                151 + int(20 * breathe),
                221,
            ),
        )

        gradient.setColorAt(
            0.58,
            QColor(
                229 + int(12 * drift),
                173 + int(16 * reverse),
                184 + int(16 * breathe),
            ),
        )

        gradient.setColorAt(
            0.80,
            QColor(
                239,
                195 + int(16 * breathe),
                157 + int(18 * reverse),
            ),
        )

        gradient.setColorAt(
            1.0,
            QColor(
                225 + int(12 * reverse),
                212 + int(14 * drift),
                168 + int(14 * breathe),
            ),
        )

        painter.setPen(
            Qt.NoPen
        )

        painter.setBrush(
            gradient
        )

        painter.drawRoundedRect(
            rect,
            25,
            25,
        )

        wash = QLinearGradient(
            rect.left()
            + rect.width()
            * drift,
            rect.top(),
            rect.right()
            - rect.width()
            * reverse,
            rect.bottom(),
        )

        wash.setColorAt(
            0.0,
            QColor(
                255,
                255,
                255,
                8 + int(22 * breathe),
            ),
        )

        wash.setColorAt(
            0.46,
            QColor(
                255,
                255,
                255,
                0,
            ),
        )

        wash.setColorAt(
            1.0,
            QColor(
                91,
                65,
                132,
                10 + int(10 * reverse),
            ),
        )

        painter.setBrush(
            wash
        )

        painter.drawRoundedRect(
            rect,
            25,
            25,
        )

        # Header
        painter.setPen(
            QColor(
                255,
                255,
                255,
                230,
            )
        )

        painter.drawText(
            QRectF(
                24,
                20,
                rect.width() - 72,
                24,
            ),
            Qt.AlignLeft
            | Qt.AlignVCenter,
            self.title,
        )

        painter.drawText(
            QRectF(
                rect.width() - 50,
                18,
                28,
                28,
            ),
            Qt.AlignCenter,
            "↗",
        )

        # Body insight stays vertically centered instead of being shoved to the
        # bottom edge.
        painter.setPen(
            QColor(
                255,
                255,
                255,
                196,
            )
        )

        painter.drawText(
            QRectF(
                24,
                60,
                rect.width() - 48,
                max(
                    58,
                    rect.height() - 82,
                ),
            ),
            Qt.AlignLeft
            | Qt.AlignVCenter
            | Qt.TextWordWrap,
            self.subtitle,
        )

        painter.end()

class MiniLatencyChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setMinimumHeight(72)
        self.values = []

    def set_values(self, values):
        self.values = [
            float(value)
            for value in (values or [])
            if isinstance(
                value,
                (
                    int,
                    float,
                ),
            )
        ]

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect().adjusted(
            4,
            8,
            -4,
            -8,
        )

        if not self.values:
            painter.setPen(
                QPen(
                    QColor("#55585f"),
                    1,
                )
            )

            painter.drawLine(
                rect.left(),
                rect.center().y(),
                rect.right(),
                rect.center().y(),
            )

            painter.end()
            return

        minimum = min(self.values)
        maximum = max(self.values)
        span = max(
            maximum - minimum,
            0.001,
        )

        path = QPainterPath()

        for index, value in enumerate(self.values):
            x = (
                rect.left()
                + rect.width()
                * index
                / max(
                    1,
                    len(self.values) - 1,
                )
            )

            normalized = (
                value
                - minimum
            ) / span

            y = (
                rect.bottom()
                - rect.height()
                * normalized
            )

            if index == 0:
                path.moveTo(
                    x,
                    y,
                )

            else:
                path.lineTo(
                    x,
                    y,
                )

        painter.setPen(
            QPen(
                QColor("#a7ddd0"),
                1.5,
            )
        )

        painter.drawPath(path)
        painter.end()


class StatusBlock(QFrame):
    """
    Reference-inspired colored system status block.
    """

    def __init__(
        self,
        title: str,
        value: str = "—",
        detail: str = "",
        parent=None,
    ):
        super().__init__(parent)

        self._status = "unknown"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            13,
            10,
            13,
            10,
        )
        layout.setSpacing(3)

        top = QHBoxLayout()

        self.title_label = QLabel(title)
        self.title_label.setObjectName("StatusBlockTitle")

        self.value_label = QLabel(value)

        top.addWidget(self.title_label)
        top.addStretch()
        top.addWidget(self.value_label)

        self.detail_label = QLabel(detail)
        self.detail_label.setObjectName("Tiny")
        self.detail_label.setWordWrap(True)

        layout.addLayout(top)

        if detail:
            layout.addWidget(self.detail_label)

        self.set_status(
            "unknown",
            value,
            detail,
        )

    def set_status(
        self,
        status: str,
        value: str | None = None,
        detail: str | None = None,
    ):
        normalized = str(
            status
            or "unknown"
        ).strip().upper()

        if normalized in {
            "HEALTHY",
            "READY",
            "ONLINE",
            "ACTIVE",
            "CERTIFIED",
            "OK",
        }:
            group = "good"
            self.setObjectName("StatusGood")
            self.value_label.setObjectName("StatusBlockValueGood")

        elif normalized in {
            "DEGRADED",
            "LIMITED",
            "WARNING",
            "UNKNOWN",
        }:
            group = "warn"
            self.setObjectName("StatusWarn")
            self.value_label.setObjectName("StatusBlockValueWarn")

        elif normalized in {
            "UNAVAILABLE",
            "OFFLINE",
            "ERROR",
            "FAILED",
            "FAILURE",
            "INACTIVE",
        }:
            group = "bad"
            self.setObjectName("StatusBad")
            self.value_label.setObjectName("StatusBlockValueBad")

        else:
            group = "warn"
            self.setObjectName("StatusWarn")
            self.value_label.setObjectName("StatusBlockValueWarn")

        self._status = group

        if value is not None:
            self.value_label.setText(
                str(value)
            )

        if detail is not None:
            self.detail_label.setText(
                str(detail)
            )

        self.style().unpolish(self)
        self.style().polish(self)

        self.value_label.style().unpolish(
            self.value_label
        )
        self.value_label.style().polish(
            self.value_label
        )


class ScreenshotPreview(QFrame):
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("InnerRow")
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            10,
            10,
            10,
            10,
        )

        self.image = QLabel(
            "No screenshot captured"
        )

        self.image.setAlignment(
            Qt.AlignCenter
        )

        self.image.setMinimumHeight(
            180
        )

        self.image.setStyleSheet(
            (
                "background:rgba(0,0,0,60);"
                "border-radius:14px;"
                "color:#777b82;"
            )
        )

        layout.addWidget(
            self.image
        )

    def set_pixmap(
        self,
        pixmap: QPixmap | None,
    ):
        if (
            pixmap is None
            or pixmap.isNull()
        ):
            self.image.setPixmap(
                QPixmap()
            )

            self.image.setText(
                "No screenshot captured"
            )

            return

        scaled = pixmap.scaled(
            760,
            420,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )

        self.image.setText("")
        self.image.setPixmap(
            scaled
        )

    def mouseReleaseEvent(
        self,
        event,
    ):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
            event.accept()
            return

        super().mouseReleaseEvent(event)
