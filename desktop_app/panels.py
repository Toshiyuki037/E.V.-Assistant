from __future__ import annotations

from PySide6.QtCore import (
    Qt,
    Signal,
)

from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .widgets import (
    StatusBlock,
)


class OverlayPanel(
    QFrame
):
    closed = Signal()

    def __init__(
        self,
        title,
        subtitle,
        parent=None,
    ):
        super().__init__(
            parent
        )

        self.setObjectName(
            "OverlayPanel"
        )

        self.setVisible(
            False
        )

        self.setMinimumWidth(
            520
        )

        self.setMaximumWidth(
            620
        )

        self._root = QVBoxLayout(
            self
        )
        self._root.setContentsMargins(
            24,
            22,
            24,
            22,
        )
        self._root.setSpacing(
            14
        )

        header = QHBoxLayout()

        titles = QVBoxLayout()
        titles.setSpacing(
            2
        )

        title_label = QLabel(
            title
        )
        title_label.setObjectName(
            "PageTitle"
        )

        subtitle_label = QLabel(
            subtitle
        )
        subtitle_label.setObjectName(
            "PageSubtitle"
        )

        titles.addWidget(
            title_label
        )
        titles.addWidget(
            subtitle_label
        )

        header.addLayout(
            titles
        )
        header.addStretch()

        self.close_button = QLabel(
            "×"
        )
        self.close_button.setObjectName(
            "PanelClose"
        )
        self.close_button.setAlignment(
            Qt.AlignCenter
        )
        self.close_button.setFixedSize(
            34,
            34,
        )
        self.close_button.setCursor(
            Qt.PointingHandCursor
        )

        header.addWidget(
            self.close_button,
            0,
            Qt.AlignTop,
        )

        self._root.addLayout(
            header
        )

        self.updated = QLabel(
            "Last updated —"
        )
        self.updated.setObjectName(
            "UpdatedAt"
        )
        self._root.addWidget(
            self.updated
        )

    def mousePressEvent(
        self,
        event,
    ):
        if self.close_button.geometry().contains(
            event.position().toPoint()
        ):
            self.hide_panel()
            event.accept()
            return

        super().mousePressEvent(
            event
        )

    def show_panel(
        self,
    ):
        self.show()
        self.raise_()

    def hide_panel(
        self,
    ):
        self.hide()
        self.closed.emit()


class NotificationCard(
    QFrame
):
    def __init__(
        self,
        level,
        title,
        detail,
        parent=None,
    ):
        super().__init__(
            parent
        )

        normalized = str(
            level
            or "info"
        ).lower()

        if normalized == "error":
            self.setObjectName(
                "StatusBad"
            )
            accent = "#f48389"

        elif normalized == "warning":
            self.setObjectName(
                "StatusWarn"
            )
            accent = "#edc272"

        else:
            self.setObjectName(
                "StatusGood"
            )
            accent = "#79e2aa"

        layout = QHBoxLayout(
            self
        )
        layout.setContentsMargins(
            15,
            13,
            15,
            13,
        )
        layout.setSpacing(
            12
        )

        dot = QLabel(
            "●"
        )
        dot.setStyleSheet(
            f"color:{accent};font-size:12px;"
        )

        body = QVBoxLayout()
        body.setSpacing(
            3
        )

        title_label = QLabel(
            str(
                title
                or "E.V.I.E."
            )
        )
        title_label.setObjectName(
            "SectionTitle"
        )

        detail_label = QLabel(
            str(
                detail
                or ""
            )
        )
        detail_label.setObjectName(
            "Muted"
        )
        detail_label.setWordWrap(
            True
        )

        body.addWidget(
            title_label
        )
        body.addWidget(
            detail_label
        )

        layout.addWidget(
            dot,
            0,
            Qt.AlignTop,
        )
        layout.addLayout(
            body,
            1,
        )


class NotificationsPanel(
    OverlayPanel
):
    def __init__(
        self,
        parent=None,
    ):
        super().__init__(
            "Notifications",
            "Health, runtime warnings, and recent verified activity.",
            parent,
        )

        summary = QHBoxLayout()

        self.attention_block = StatusBlock(
            "Attention",
            "0",
            "Current items requiring review",
        )

        self.recent_block = StatusBlock(
            "Recent",
            "0",
            "Recent runtime events",
        )

        summary.addWidget(
            self.attention_block
        )
        summary.addWidget(
            self.recent_block
        )

        self._root.addLayout(
            summary
        )

        scroll = QScrollArea()
        scroll.setWidgetResizable(
            True
        )
        scroll.setFrameShape(
            QFrame.NoFrame
        )

        body = QWidget()

        self.cards = QVBoxLayout(
            body
        )
        self.cards.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        self.cards.setSpacing(
            9
        )
        self.cards.addStretch(
            1
        )

        scroll.setWidget(
            body
        )

        self._root.addWidget(
            scroll,
            1,
        )

    def _clear_cards(
        self,
    ):
        while self.cards.count() > 1:
            item = self.cards.takeAt(
                0
            )

            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

    def set_notifications(
        self,
        items,
        updated_text="—",
    ):
        values = list(
            items
            or []
        )

        self.updated.setText(
            f"Last updated {updated_text}"
        )

        self._clear_cards()

        attention = sum(
            1
            for item in values
            if str(
                item.get(
                    "level"
                )
                or ""
            ).lower()
            in {
                "error",
                "warning",
            }
        )

        self.attention_block.set_status(
            (
                "HEALTHY"
                if attention == 0
                else "WARNING"
            ),
            str(
                attention
            ),
            (
                "No warnings"
                if attention == 0
                else "Requires review"
            ),
        )

        self.recent_block.set_status(
            "READY",
            str(
                len(
                    values
                )
            ),
            "Visible events",
        )

        if not values:
            self.cards.insertWidget(
                0,
                NotificationCard(
                    "info",
                    "All clear",
                    "There are no current notifications.",
                ),
            )
            return

        for item in values:
            self.cards.insertWidget(
                self.cards.count() - 1,
                NotificationCard(
                    item.get(
                        "level"
                    ),
                    item.get(
                        "title"
                    ),
                    item.get(
                        "detail"
                    ),
                ),
            )


class SettingsPanel(
    OverlayPanel
):
    def __init__(
        self,
        parent=None,
    ):
        super().__init__(
            "Settings",
            "Desktop presentation and live runtime state.",
            parent,
        )

        self.tabs = QTabWidget()
        self.tabs.setObjectName(
            "UtilityTabs"
        )

        general = QWidget()
        general_layout = QVBoxLayout(
            general
        )
        general_layout.setContentsMargins(
            12,
            16,
            12,
            16,
        )
        general_layout.setSpacing(
            12
        )

        heading = QLabel(
            "Desktop behavior"
        )
        heading.setObjectName(
            "SectionTitle"
        )
        general_layout.addWidget(
            heading
        )

        card = QFrame()
        card.setObjectName(
            "InnerRow"
        )

        card_layout = QVBoxLayout(
            card
        )
        card_layout.setContentsMargins(
            16,
            14,
            16,
            14,
        )
        card_layout.setSpacing(
            10
        )

        self.run_background = QCheckBox(
            "Keep E.V.I.E. running when the window closes"
        )
        self.run_background.setChecked(
            True
        )

        self.start_wake = QCheckBox(
            "Keep wake-word session active"
        )
        self.start_wake.setChecked(
            True
        )

        card_layout.addWidget(
            self.run_background
        )
        card_layout.addWidget(
            self.start_wake
        )

        general_layout.addWidget(
            card
        )
        general_layout.addStretch(
            1
        )

        runtime = QWidget()
        runtime_layout = QVBoxLayout(
            runtime
        )
        runtime_layout.setContentsMargins(
            12,
            16,
            12,
            16,
        )
        runtime_layout.setSpacing(
            10
        )

        self.backend_block = StatusBlock(
            "Backend",
            "—",
        )
        self.health_block = StatusBlock(
            "Health",
            "—",
        )
        self.voice_block = StatusBlock(
            "Wake word",
            "—",
        )
        self.project_block = StatusBlock(
            "Project",
            "—",
        )
        self.git_block = StatusBlock(
            "Git branch",
            "—",
        )

        for block in (
            self.backend_block,
            self.health_block,
            self.voice_block,
            self.project_block,
            self.git_block,
        ):
            runtime_layout.addWidget(
                block
            )

        runtime_layout.addStretch(
            1
        )

        about = QWidget()
        about_layout = QVBoxLayout(
            about
        )
        about_layout.setContentsMargins(
            12,
            16,
            12,
            16,
        )

        about_card = QFrame()
        about_card.setObjectName(
            "InnerRow"
        )

        about_card_layout = QVBoxLayout(
            about_card
        )
        about_card_layout.setContentsMargins(
            16,
            14,
            16,
            14,
        )

        about_text = QLabel(
            (
                "E.V.I.E. Desktop\n\n"
                "This application reads from the existing E.V.I.E. runtime. "
                "Frontend presentation does not rewrite the certified backend."
            )
        )
        about_text.setObjectName(
            "Muted"
        )
        about_text.setWordWrap(
            True
        )

        about_card_layout.addWidget(
            about_text
        )

        about_layout.addWidget(
            about_card
        )
        about_layout.addStretch(
            1
        )

        self.tabs.addTab(
            general,
            "General",
        )
        self.tabs.addTab(
            runtime,
            "Runtime",
        )
        self.tabs.addTab(
            about,
            "About",
        )

        self._root.addWidget(
            self.tabs,
            1,
        )

    def set_runtime_snapshot(
        self,
        snapshot,
    ):
        health = (
            snapshot.get(
                "health"
            )
            or {}
        )

        git = (
            snapshot.get(
                "git"
            )
            or {}
        )

        backend_online = bool(
            snapshot.get(
                "backend_online"
            )
        )

        health_value = (
            health.get(
                "overall"
            )
            or "UNKNOWN"
        )

        voice_active = bool(
            snapshot.get(
                "voice_running"
            )
            or snapshot.get(
                "voice_enabled"
            )
        )

        project = (
            snapshot.get(
                "project"
            )
            or "—"
        )

        branch = (
            git.get(
                "branch"
            )
            or "—"
        )

        self.backend_block.set_status(
            (
                "ONLINE"
                if backend_online
                else "OFFLINE"
            ),
            (
                "ONLINE"
                if backend_online
                else "OFFLINE"
            ),
        )

        self.health_block.set_status(
            health_value,
            health_value,
        )

        self.voice_block.set_status(
            (
                "ACTIVE"
                if voice_active
                else "INACTIVE"
            ),
            (
                "ACTIVE"
                if voice_active
                else "INACTIVE"
            ),
        )

        self.project_block.set_status(
            (
                "READY"
                if project != "—"
                else "UNKNOWN"
            ),
            project,
        )

        self.git_block.set_status(
            (
                "READY"
                if branch != "—"
                else "UNKNOWN"
            ),
            branch,
        )

        self.updated.setText(
            (
                "Last updated "
                + str(
                    snapshot.get(
                        "updated_at_text"
                    )
                    or "—"
                )
            )
        )


class InsightsPanel(
    OverlayPanel
):
    def __init__(
        self,
        parent=None,
    ):
        super().__init__(
            "Insights",
            "Verified observations from E.V.I.E.'s current runtime state.",
            parent,
        )

        self.summary = QLabel(
            "Waiting for verified runtime data..."
        )
        self.summary.setObjectName(
            "HeroState"
        )
        self.summary.setWordWrap(
            True
        )

        self._root.addWidget(
            self.summary
        )

        self.cards = QVBoxLayout()
        self.cards.setSpacing(
            9
        )

        self._root.addLayout(
            self.cards
        )
        self._root.addStretch(
            1
        )

    def _clear_cards(
        self,
    ):
        while self.cards.count():
            item = self.cards.takeAt(
                0
            )

            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

    def set_insights(
        self,
        title,
        items,
        updated_text="—",
    ):
        self.updated.setText(
            f"Last updated {updated_text}"
        )

        self.summary.setText(
            title
            or "No verified insight available."
        )

        self._clear_cards()

        values = list(
            items
            or []
        )

        if not values:
            values = [
                "No additional observations."
            ]

        for value in values:
            card = QFrame()
            card.setObjectName(
                "InnerRow"
            )

            layout = QVBoxLayout(
                card
            )
            layout.setContentsMargins(
                15,
                12,
                15,
                12,
            )

            text = QLabel(
                str(
                    value
                )
            )
            text.setObjectName(
                "Muted"
            )
            text.setWordWrap(
                True
            )

            layout.addWidget(
                text
            )

            self.cards.addWidget(
                card
            )
