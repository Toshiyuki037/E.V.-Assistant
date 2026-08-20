from __future__ import annotations

from PySide6.QtCore import (
    Qt,
    QSize,
    Signal,
)

from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QStackedLayout,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .pages import (
    ActivityPage,
    DashboardPage,
    SystemPage,
    WorkspacePage,
    build_insights,
)

from .panels import (
    InsightsPanel,
    NotificationsPanel,
    SettingsPanel,
)

from .ui_assets import (
    CircularAvatar,
    FAVICONS,
    NAV_ICON_SIZE,
    PROFILE_DISPLAY_SIZE,
    UTILITY_ICON_SIZE,
    load_icon,
)


class ControlCenter(
    QMainWindow
):
    hidden_to_tray = Signal()
    snapshot_refresh_requested = Signal()
    voice_requested = Signal()
    prompt_requested = Signal(str)

    def __init__(
        self,
    ):
        super().__init__()

        self.setWindowTitle(
            "E.V.I.E."
        )

        self.resize(
            1500,
            930,
        )

        self.setMinimumSize(
            1180,
            740,
        )

        self._allow_close = False
        self._last_snapshot = {}
        self._runtime_errors = []
        self._runtime_ready = False

        root = QWidget()
        root.setObjectName(
            "AppRoot"
        )
        self.setCentralWidget(
            root
        )

        outer = QVBoxLayout(
            root
        )
        outer.setContentsMargins(
            28,
            16,
            28,
            24,
        )
        outer.setSpacing(
            16
        )

        outer.addWidget(
            self.build_nav()
        )

        # ---------------------------------------------------------------
        # Main content + in-app overlay layer
        # ---------------------------------------------------------------

        content_host = QWidget()

        self.content_layers = QStackedLayout(
            content_host
        )

        self.content_layers.setStackingMode(
            QStackedLayout.StackAll
        )

        self.stack = QStackedWidget()

        self.dashboard = DashboardPage()
        self.workspace = WorkspacePage()
        self.activity = ActivityPage()
        self.system = SystemPage()

        for page in (
            self.dashboard,
            self.workspace,
            self.activity,
            self.system,
        ):
            self.stack.addWidget(
                page
            )

        self.content_layers.addWidget(
            self.stack
        )

        # Transparent panel layer covering the current page.
        self.panel_layer = QWidget()
        self.panel_layer.setObjectName(
            "PanelLayer"
        )
        self.panel_layer.setAttribute(
            Qt.WA_StyledBackground,
            True,
        )

        panel_layout = QHBoxLayout(
            self.panel_layer
        )
        panel_layout.setContentsMargins(
            0,
            12,
            12,
            12,
        )
        panel_layout.addStretch(
            1
        )

        self.notifications_panel = NotificationsPanel(
            self.panel_layer
        )
        self.settings_panel = SettingsPanel(
            self.panel_layer
        )
        self.insights_panel = InsightsPanel(
            self.panel_layer
        )

        for panel in (
            self.notifications_panel,
            self.settings_panel,
            self.insights_panel,
        ):
            panel_layout.addWidget(
                panel,
                0,
                Qt.AlignTop | Qt.AlignRight,
            )

        self.panel_layer.hide()

        self.content_layers.addWidget(
            self.panel_layer
        )

        outer.addWidget(
            content_host,
            1,
        )

        # ---------------------------------------------------------------
        # Signals
        # ---------------------------------------------------------------

        self.dashboard.submit_requested.connect(
            self.prompt_requested.emit
        )
        self.dashboard.voice_requested.connect(
            self.voice_requested.emit
        )
        self.dashboard.insights_requested.connect(
            self.show_insights
        )

        self.workspace.refresh_requested.connect(
            self.snapshot_refresh_requested.emit
        )
        self.system.refresh_requested.connect(
            self.snapshot_refresh_requested.emit
        )

        self.activity.conversation_selected.connect(
            self.open_conversation
        )

        for panel in (
            self.notifications_panel,
            self.settings_panel,
            self.insights_panel,
        ):
            panel.closed.connect(
                self._panel_closed
            )

    # -----------------------------------------------------------------------
    # Navbar
    # -----------------------------------------------------------------------

    def build_nav(
        self,
    ):
        rail = QFrame()
        rail.setObjectName(
            "TopRail"
        )
        rail.setFixedHeight(
            62
        )

        grid = QGridLayout(
            rail
        )
        grid.setContentsMargins(
            9,
            7,
            9,
            7,
        )

        blank = QWidget()
        blank.setFixedWidth(
            170
        )

        nav = QWidget()
        nav.setObjectName(
            "NavZone"
        )

        nav_layout = QHBoxLayout(
            nav
        )
        nav_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        nav_layout.setSpacing(
            10
        )

        self.buttons = []

        nav_items = [
            (
                "Dashboard",
                FAVICONS[
                    "dashboard"
                ],
            ),
            (
                "Workspace",
                FAVICONS[
                    "workspace"
                ],
            ),
            (
                "Activity",
                FAVICONS[
                    "activity"
                ],
            ),
            (
                "System",
                FAVICONS[
                    "system"
                ],
            ),
        ]

        for index, (
            name,
            icon_path,
        ) in enumerate(
            nav_items
        ):
            button = QPushButton(
                name
            )

            button.setObjectName(
                "NavPill"
            )

            button.setCheckable(
                True
            )

            button.setChecked(
                index == 0
            )

            if icon_path.exists():
                icon = load_icon(
                    icon_path
                )

                if not icon.isNull():
                    button.setIcon(
                        icon
                    )
                    button.setIconSize(
                        QSize(
                            NAV_ICON_SIZE,
                            NAV_ICON_SIZE,
                        )
                    )

            button.clicked.connect(
                lambda checked, n=index:
                    self.select(
                        n
                    )
            )

            nav_layout.addWidget(
                button
            )

            self.buttons.append(
                button
            )

        tools = QWidget()
        tools.setObjectName(
            "ToolZone"
        )
        tools.setFixedWidth(
            170
        )

        tool_layout = QHBoxLayout(
            tools
        )
        tool_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        tool_layout.setSpacing(
            9
        )
        tool_layout.setAlignment(
            Qt.AlignRight
        )

        self.notification_button = (
            self._round_icon_button(
                FAVICONS[
                    "notifications"
                ],
                fallback=
                    "◔",
                tooltip=
                    "Notifications",
            )
        )

        self.notification_button.clicked.connect(
            self.show_notifications
        )

        self.settings_button = (
            self._round_icon_button(
                FAVICONS[
                    "settings"
                ],
                fallback=
                    "⚙",
                tooltip=
                    "Settings",
            )
        )

        self.settings_button.clicked.connect(
            self.show_settings
        )

        self.profile = CircularAvatar(
            display_size=
                PROFILE_DISPLAY_SIZE
        )

        self.profile.setToolTip(
            "Profile"
        )

        tool_layout.addWidget(
            self.notification_button
        )
        tool_layout.addWidget(
            self.settings_button
        )
        tool_layout.addWidget(
            self.profile,
            0,
            Qt.AlignVCenter,
        )

        grid.addWidget(
            blank,
            0,
            0,
        )
        grid.addWidget(
            nav,
            0,
            1,
            Qt.AlignCenter,
        )
        grid.addWidget(
            tools,
            0,
            2,
        )

        grid.setColumnStretch(
            0,
            1,
        )
        grid.setColumnStretch(
            2,
            1,
        )

        # Runtime-dependent controls remain disabled until the backend has
        # completely initialized and the first verified snapshot is available.
        for button in self.buttons:
            button.setEnabled(False)

        self.notification_button.setEnabled(False)
        self.settings_button.setEnabled(False)

        return rail

    def _round_icon_button(
        self,
        path,
        *,
        fallback,
        tooltip,
    ):
        button = QPushButton()
        button.setObjectName(
            "CircleButton"
        )
        button.setToolTip(
            tooltip
        )

        if path.exists():
            icon = load_icon(
                path
            )

            if not icon.isNull():
                button.setIcon(
                    icon
                )
                button.setIconSize(
                    QSize(
                        UTILITY_ICON_SIZE,
                        UTILITY_ICON_SIZE,
                    )
                )

            else:
                button.setText(
                    fallback
                )

        else:
            button.setText(
                fallback
            )

        return button

    def select(
        self,
        index,
    ):
        self._hide_all_panels()

        self.stack.setCurrentIndex(
            index
        )

        for i, button in enumerate(
            self.buttons
        ):
            button.blockSignals(
                True
            )

            button.setChecked(
                i == index
            )

            button.blockSignals(
                False
            )

    # -----------------------------------------------------------------------
    # In-app panels
    # -----------------------------------------------------------------------

    def _show_single_panel(
        self,
        panel,
    ):
        for item in (
            self.notifications_panel,
            self.settings_panel,
            self.insights_panel,
        ):
            item.hide()

        self.panel_layer.show()
        self.panel_layer.raise_()

        panel.show_panel()

    def _hide_all_panels(
        self,
    ):
        for item in (
            self.notifications_panel,
            self.settings_panel,
            self.insights_panel,
        ):
            item.hide()

        self.panel_layer.hide()

    def _panel_closed(
        self,
    ):
        if not any(
            panel.isVisible()
            for panel in (
                self.notifications_panel,
                self.settings_panel,
                self.insights_panel,
            )
        ):
            self.panel_layer.hide()


    def set_runtime_ready(
        self,
        ready,
    ):
        self._runtime_ready = bool(
            ready
        )

        for button in self.buttons:
            button.setEnabled(
                self._runtime_ready
            )

        self.notification_button.setEnabled(
            self._runtime_ready
        )

        self.settings_button.setEnabled(
            self._runtime_ready
        )

        self.dashboard.set_ready(
            self._runtime_ready
        )

        self.workspace.set_ready(
            self._runtime_ready
        )

        self.activity.set_ready(
            self._runtime_ready
        )

        self.system.set_ready(
            self._runtime_ready
        )

        if self._runtime_ready:
            self.buttons[0].setChecked(
                True
            )

    def open_conversation(
        self,
        conversation,
    ):
        if not self._runtime_ready:
            return

        self.select(
            0
        )

        self.dashboard.chat.clear_messages()

        user_text = str(
            conversation.get(
                "user_text"
            )
            or ""
        )

        response = str(
            conversation.get(
                "response"
            )
            or ""
        )

        timestamp = str(
            conversation.get(
                "timestamp"
            )
            or ""
        )

        if user_text:
            self.dashboard.chat.append_message(
                "user",
                user_text,
                timestamp,
            )

        if response:
            self.dashboard.chat.append_message(
                "assistant",
                response,
                timestamp,
            )


    # -----------------------------------------------------------------------
    # Backend -> UI
    # -----------------------------------------------------------------------

    def set_connected(
        self,
        connected,
    ):
        self.dashboard.backend_status.set_status(
            (
                "ONLINE"
                if connected
                else "OFFLINE"
            ),
            (
                "ONLINE"
                if connected
                else "OFFLINE"
            ),
        )

    def set_runtime_state(
        self,
        state,
        detail="",
    ):
        self.dashboard.state_value.setText(
            str(
                state
                or "idle"
            )
            .replace(
                "_",
                " ",
            )
            .title()
        )

        if detail:
            self.dashboard.state_detail.setText(
                detail
            )

        self.dashboard.set_runtime_phase(
            state
        )

    def set_transcript(
        self,
        kind,
        text,
    ):
        self.dashboard.set_transcript(
            kind,
            text,
        )

    def set_response(
        self,
        user_text,
        response,
    ):
        preview = str(
            response
            or ""
        ).replace(
            "\n",
            " ",
        ).strip()

        if len(
            preview
        ) > 260:
            preview = (
                preview[
                    :257
                ]
                .rstrip()
                + "..."
            )

        self.dashboard.state_detail.setText(
            preview
            or "Response complete."
        )

        self.dashboard.add_response(
            response
        )

    def set_latency(
        self,
        seconds,
    ):
        self.dashboard.latency_value.setText(
            f"{float(seconds):.2f}s"
        )

    def set_voice_active(
        self,
        active,
    ):
        self.dashboard.set_voice_active(
            active
        )

    def apply_snapshot(
        self,
        snapshot,
    ):
        self._last_snapshot = dict(
            snapshot
            or {}
        )

        self.dashboard.apply_snapshot(
            snapshot
        )
        self.workspace.apply_snapshot(
            snapshot
        )
        self.activity.apply_snapshot(
            snapshot
        )
        self.system.apply_snapshot(
            snapshot
        )

        self.settings_panel.set_runtime_snapshot(
            snapshot
        )

    def show_runtime_error(
        self,
        message,
    ):
        value = str(
            message
        )

        self._runtime_errors.insert(
            0,
            value,
        )

        self._runtime_errors = (
            self._runtime_errors[
                :20
            ]
        )

        self.set_runtime_state(
            "error",
            value,
        )

    # -----------------------------------------------------------------------
    # Panel population
    # -----------------------------------------------------------------------

    def show_notifications(
        self,
    ):
        snapshot = (
            self._last_snapshot
            or {}
        )

        items = []

        health = (
            snapshot.get(
                "health"
            )
            or {}
        )

        overall = health.get(
            "overall"
        )

        if (
            overall
            and str(
                overall
            ).upper()
            != "HEALTHY"
        ):
            items.append(
                {
                    "level":
                        "warning",

                    "title":
                        f"System health: {overall}",

                    "detail":
                        "Open System for component details.",
                }
            )

        for error in self._runtime_errors[
            :8
        ]:
            items.append(
                {
                    "level":
                        "error",

                    "title":
                        "Runtime error",

                    "detail":
                        error,
                }
            )

        activity = (
            snapshot.get(
                "activity"
            )
            or []
        )

        for item in activity[
            :5
        ]:
            total = item.get(
                "total_seconds"
            )

            items.append(
                {
                    "level":
                        "info",

                    "title":
                        (
                            item.get(
                                "user_text"
                            )
                            or "Request"
                        )[
                            :80
                        ],

                    "detail":
                        (
                            f"Completed in {float(total):.1f}s"
                            if isinstance(
                                total,
                                (
                                    int,
                                    float,
                                ),
                            )
                            else "Completed"
                        ),
                }
            )

        self.notifications_panel.set_notifications(
            items,
            snapshot.get(
                "updated_at_text"
            )
            or "—",
        )

        self._show_single_panel(
            self.notifications_panel
        )

    def show_settings(
        self,
    ):
        self.settings_panel.set_runtime_snapshot(
            self._last_snapshot
            or {}
        )

        self._show_single_panel(
            self.settings_panel
        )

    def show_insights(
        self,
    ):
        snapshot = (
            self._last_snapshot
            or {}
        )

        items = build_insights(
            snapshot
        )

        title = (
            items[0]
            if items
            else "No verified insight available."
        )

        self.insights_panel.set_insights(
            title,
            items[
                1:
            ],
            snapshot.get(
                "updated_at_text"
            )
            or "—",
        )

        self._show_single_panel(
            self.insights_panel
        )

    # -----------------------------------------------------------------------
    # Lifecycle
    # -----------------------------------------------------------------------

    def allow_real_close(
        self,
    ):
        self._allow_close = True

    def closeEvent(
        self,
        event,
    ):
        if self._allow_close:
            event.accept()
            return

        self.hide()
        self.hidden_to_tray.emit()
        event.ignore()
