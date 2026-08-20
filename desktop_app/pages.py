from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .widgets import (
    InsightTile,
    MiniLatencyChart,
    ScreenshotPreview,
    StatusBlock,
)


def label(text, obj=None):
    value = QLabel(str(text))
    if obj:
        value.setObjectName(obj)
    return value


def glass():
    value = QFrame()
    value.setObjectName("GlassCard")
    return value


class ValueRow(QFrame):
    def __init__(self, title, value="—", sub=""):
        super().__init__()
        self.setObjectName("InnerRow")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)

        left = QVBoxLayout()
        left.setSpacing(1)
        left.addWidget(label(title, "SectionTitle"))
        if sub:
            left.addWidget(label(sub, "Tiny"))

        self.value_label = label(value, "Muted")

        layout.addLayout(left)
        layout.addStretch()
        layout.addWidget(self.value_label)

    def set_value(self, value):
        self.value_label.setText("—" if value is None else str(value))


class ChatBubble(QFrame):
    def __init__(self, role, text="", meta="", live=False):
        super().__init__()
        self.role = role
        self.setObjectName(
            "ChatUser"
            if role == "user"
            else "ChatAssistant"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 11, 14, 11)
        layout.setSpacing(4)

        self.role_label = label(
            "YOU" if role == "user" else "E.V.I.E.",
            "Eyebrow",
        )

        self.text_label = QLabel(text)
        self.text_label.setWordWrap(True)
        self.text_label.setObjectName("ChatText")

        self.meta_label = label(meta, "UpdatedAt")

        layout.addWidget(self.role_label)
        layout.addWidget(self.text_label)
        if meta:
            layout.addWidget(self.meta_label)

        if live:
            self.setProperty("live", True)

    def set_text(self, text):
        self.text_label.setText(str(text or ""))


class ChatPanel(QFrame):
    submit_requested = Signal(str)

    def __init__(self):
        super().__init__()
        self.setObjectName("GlassCard")

        self._live_voice_bubble = None

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(10)

        head = QHBoxLayout()
        head.addWidget(label("Conversation", "SectionTitle"))
        head.addStretch()
        self.status = label("Starting", "UpdatedAt")
        head.addWidget(self.status)
        root.addLayout(head)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.surface = QWidget()
        self.messages = QVBoxLayout(self.surface)
        self.messages.setContentsMargins(0, 4, 5, 4)
        self.messages.setSpacing(9)
        self.messages.addStretch(1)

        self.scroll.setWidget(self.surface)
        root.addWidget(self.scroll, 1)

        composer = QHBoxLayout()
        composer.setSpacing(8)

        self.input = QLineEdit()
        self.input.setObjectName("CommandBox")
        self.input.setPlaceholderText("Ask E.V.I.E. or issue a command…")
        self.input.setEnabled(False)

        self.send = QPushButton("Send")
        self.send.setObjectName("LightPill")
        self.send.setEnabled(False)

        composer.addWidget(self.input, 1)
        composer.addWidget(self.send)

        root.addLayout(composer)

        self.input.returnPressed.connect(self._submit)
        self.send.clicked.connect(self._submit)

    def set_ready(self, ready):
        self.input.setEnabled(bool(ready))
        self.send.setEnabled(bool(ready))
        self.status.setText(
            "Online"
            if ready
            else "Loading"
        )

    def _submit(self):
        text = self.input.text().strip()
        if not text or not self.input.isEnabled():
            return

        self.input.clear()
        self.append_message("user", text, "Typed")
        self.submit_requested.emit(text)

    def clear_messages(self):
        while self.messages.count() > 1:
            item = self.messages.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        self._live_voice_bubble = None

    def set_history(self, conversations):
        if not conversations:
            return

        self.clear_messages()

        for item in conversations[-20:]:
            user_text = str(item.get("user_text") or "").strip()
            response = str(item.get("response") or "").strip()
            stamp = str(item.get("timestamp") or "")

            if user_text:
                self.append_message("user", user_text, stamp)
            if response:
                self.append_message("assistant", response, stamp)

    def append_message(self, role, text, meta=""):
        bubble = ChatBubble(role, text, meta)

        align = (
            Qt.AlignRight
            if role == "user"
            else Qt.AlignLeft
        )

        wrapper = QWidget()
        row = QHBoxLayout(wrapper)
        row.setContentsMargins(0, 0, 0, 0)

        if role == "user":
            row.addStretch(1)
            row.addWidget(bubble, 0, align)
        else:
            row.addWidget(bubble, 0, align)
            row.addStretch(1)

        bubble.setMaximumWidth(620)
        self.messages.insertWidget(self.messages.count() - 1, wrapper)
        self._scroll_bottom()
        return bubble

    def set_voice_transcript(self, kind, text):
        kind = str(kind or "").lower()
        text = str(text or "").strip()

        if kind in {"listening", "partial"}:
            if self._live_voice_bubble is None:
                self._live_voice_bubble = self.append_message(
                    "user",
                    text or "Listening…",
                    "Live voice",
                )
            else:
                self._live_voice_bubble.set_text(
                    text or "Listening…"
                )

        elif kind == "final":
            if self._live_voice_bubble is None:
                self._live_voice_bubble = self.append_message(
                    "user",
                    text,
                    "Voice",
                )
            else:
                self._live_voice_bubble.set_text(text)

        elif kind == "finalizing":
            self.status.setText("Finalizing speech")

    def finalize_voice_turn(self):
        self._live_voice_bubble = None

    def _scroll_bottom(self):
        QTimer = __import__(
            "PySide6.QtCore",
            fromlist=["QTimer"],
        ).QTimer

        QTimer.singleShot(
            0,
            lambda:
                self.scroll.verticalScrollBar().setValue(
                    self.scroll.verticalScrollBar().maximum()
                )
        )


class DashboardPage(QWidget):
    submit_requested = Signal(str)
    voice_requested = Signal()
    insights_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setObjectName("PageCanvas")
        self._history_loaded = False

        root = QVBoxLayout(self)
        root.setContentsMargins(4, 8, 4, 4)
        root.setSpacing(14)

        head = QHBoxLayout()
        titles = QVBoxLayout()
        titles.setSpacing(2)
        titles.addWidget(label("Dashboard", "PageTitle"))
        titles.addWidget(
            label(
                "Conversation, live runtime state, latency, and insights.",
                "PageSubtitle",
            )
        )

        head.addLayout(titles)
        head.addStretch()

        self.updated = label("Last updated —", "UpdatedAt")
        head.addWidget(self.updated, 0, Qt.AlignBottom)

        root.addLayout(head)

        body = QHBoxLayout()
        body.setSpacing(14)

        # Left half: the product's primary interaction.
        self.chat = ChatPanel()
        self.chat.submit_requested.connect(self.submit_requested.emit)
        body.addWidget(self.chat, 11)

        # Right half: operational information that is actually useful.
        right = QVBoxLayout()
        right.setSpacing(14)

        hero = glass()
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(20, 17, 20, 17)
        hero_layout.setSpacing(6)

        state_head = QHBoxLayout()
        state_head.addWidget(label("E.V.I.E. STATUS", "Eyebrow"))
        state_head.addStretch()

        self.system_ready = label("●  STARTING", "Good")
        state_head.addWidget(self.system_ready)
        hero_layout.addLayout(state_head)

        self.state_value = label("Starting", "HeroState")
        self.state_detail = label("Loading runtime…", "Muted")
        self.state_detail.setWordWrap(True)

        hero_layout.addWidget(self.state_value)
        hero_layout.addWidget(self.state_detail)

        self.voice_button = QPushButton("Wake Starting")
        self.voice_button.setObjectName("DarkPill")
        self.voice_button.setEnabled(False)
        self.voice_button.clicked.connect(self.voice_requested.emit)

        hero_layout.addWidget(self.voice_button, 0, Qt.AlignLeft)

        right.addWidget(hero)

        status_card = glass()
        status_layout = QGridLayout(status_card)
        status_layout.setContentsMargins(16, 15, 16, 15)
        status_layout.setSpacing(8)

        self.backend_status = StatusBlock("Backend")
        self.memory_status = StatusBlock("Memory")
        self.voice_status = StatusBlock("Wake")
        self.tools_status = StatusBlock("Tools")

        status_layout.addWidget(self.backend_status, 0, 0)
        status_layout.addWidget(self.memory_status, 0, 1)
        status_layout.addWidget(self.voice_status, 1, 0)
        status_layout.addWidget(self.tools_status, 1, 1)

        right.addWidget(status_card)

        performance = glass()
        performance_layout = QVBoxLayout(performance)
        performance_layout.setContentsMargins(18, 15, 18, 14)
        performance_layout.setSpacing(3)

        ph = QHBoxLayout()
        ph.addWidget(label("Latency", "SectionTitle"))
        ph.addStretch()
        self.performance_updated = label("Updated —", "UpdatedAt")
        ph.addWidget(self.performance_updated)

        performance_layout.addLayout(ph)

        self.latency_value = label("—", "Value")
        performance_layout.addWidget(self.latency_value)
        performance_layout.addWidget(
            label("Latest verified first sentence", "Muted")
        )

        self.latency_chart = MiniLatencyChart()
        self.latency_chart.setMaximumHeight(84)
        performance_layout.addWidget(self.latency_chart)

        right.addWidget(performance)

        self.insight = InsightTile()
        self.insight.clicked.connect(
            self.insights_requested.emit
        )

        # Fill the operational column instead of keeping the old square-card
        # geometry. This is the intended compact landscape Insights surface.
        right.addWidget(
            self.insight
        )

        body.addLayout(right, 9)

        root.addLayout(body, 1)

    def set_ready(self, ready):
        self.chat.set_ready(ready)
        self.voice_button.setEnabled(bool(ready))
        self.voice_button.setText(
            "Wake Active"
            if ready
            else "Wake Starting"
        )

    def set_voice_active(self, active):
        self.voice_button.setText(
            "Wake Active"
            if active
            else "Start Wake"
        )

        self.voice_status.set_status(
            "ACTIVE" if active else "INACTIVE",
            "ACTIVE" if active else "INACTIVE",
        )

    def set_transcript(self, kind, text):
        self.chat.set_voice_transcript(kind, text)

    def set_runtime_phase(self, state):
        normalized = str(state or "").lower()

        if normalized in {
            "thinking",
            "acting",
            "speaking",
            "listening",
            "finalizing",
        }:
            self.chat.status.setText(
                normalized.replace("_", " ").title()
            )
        elif normalized in {
            "standing by",
            "standing_by",
        }:
            self.chat.status.setText("Online")

    def add_response(self, response):
        value = str(response or "").strip()
        if value:
            self.chat.append_message(
                "assistant",
                value,
                "E.V.I.E.",
            )
        self.chat.finalize_voice_turn()

    def apply_snapshot(self, snapshot):
        updated = str(snapshot.get("updated_at_text") or "—")
        self.updated.setText(f"Last updated {updated}")
        self.performance_updated.setText(f"Updated {updated}")

        health = snapshot.get("health") or {}
        overall = health.get("overall")

        self.system_ready.setText(
            "●  " + str(
                overall
                or (
                    "ONLINE"
                    if snapshot.get("backend_online")
                    else "OFFLINE"
                )
            )
        )

        self.backend_status.set_status(
            "ONLINE" if snapshot.get("backend_online") else "OFFLINE",
            "ONLINE" if snapshot.get("backend_online") else "OFFLINE",
        )

        memory = snapshot.get("memory") or {}
        memory_count = memory.get("active_memories")
        self.memory_status.set_status(
            "READY" if memory_count is not None else "UNKNOWN",
            f"{memory_count} active" if memory_count is not None else "—",
        )

        tools = snapshot.get("tools") or {}
        tool_count = tools.get("count")
        self.tools_status.set_status(
            "READY" if tool_count is not None else "UNKNOWN",
            f"{tool_count} tools" if tool_count is not None else "—",
        )

        self.set_voice_active(
            bool(snapshot.get("voice_running") or snapshot.get("voice_enabled"))
        )

        perf = snapshot.get("performance") or {}
        first_sentence = perf.get("latest_first_sentence_seconds")

        self.latency_value.setText(
            f"{float(first_sentence):.2f}s"
            if isinstance(first_sentence, (int, float))
            else "—"
        )

        self.latency_chart.set_values(
            perf.get("recent_total_seconds") or []
        )

        title, insight = build_insight_summary(snapshot)
        self.insight.set_insight(title, insight)

        conversations = snapshot.get("conversations") or []

        if conversations and not self._history_loaded:
            self.chat.set_history(conversations)
            self._history_loaded = True


class WorkspacePage(QWidget):
    refresh_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setObjectName("PageCanvas")

        root = QVBoxLayout(self)
        root.setContentsMargins(4, 8, 4, 4)
        root.setSpacing(14)

        head = QHBoxLayout()
        titles = QVBoxLayout()
        titles.addWidget(label("Workspace", "PageTitle"))
        titles.addWidget(
            label(
                "Live project, Git, files, and computer context.",
                "PageSubtitle",
            )
        )

        head.addLayout(titles)
        head.addStretch()

        self.updated = label("Last updated —", "UpdatedAt")
        head.addWidget(self.updated)

        self.capture_button = QPushButton("Capture Screen")
        self.capture_button.setObjectName("DarkPill")
        self.capture_button.setEnabled(False)
        self.capture_button.clicked.connect(self.capture_screen)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setObjectName("DarkPill")
        self.refresh_button.setEnabled(False)
        self.refresh_button.clicked.connect(self.refresh_requested.emit)

        head.addWidget(self.capture_button)
        head.addWidget(self.refresh_button)

        root.addLayout(head)

        top = QGridLayout()
        top.setSpacing(14)

        project = glass()
        pl = QVBoxLayout(project)
        pl.setContentsMargins(20, 18, 20, 18)
        pl.addWidget(label("Project", "SectionTitle"))

        self.project_value = label("—", "HeroState")
        self.project_path = label("", "Muted")
        self.project_path.setWordWrap(True)

        pl.addWidget(self.project_value)
        pl.addWidget(self.project_path)
        pl.addStretch()

        git = glass()
        gl = QVBoxLayout(git)
        gl.setContentsMargins(20, 18, 20, 18)
        gl.addWidget(label("Git", "SectionTitle"))

        self.branch_value = label("—", "HeroState")
        self.git_detail = label("", "Muted")

        gl.addWidget(self.branch_value)
        gl.addWidget(self.git_detail)
        gl.addStretch()

        computer = glass()
        cl = QVBoxLayout(computer)
        cl.setContentsMargins(20, 18, 20, 18)
        cl.addWidget(label("Computer / Vision", "SectionTitle"))

        self.app_value = label("—", "HeroState")
        self.app_detail = label("", "Muted")
        self.app_detail.setWordWrap(True)

        cl.addWidget(self.app_value)
        cl.addWidget(self.app_detail)
        cl.addStretch()

        top.addWidget(project, 0, 0)
        top.addWidget(git, 0, 1)
        top.addWidget(computer, 0, 2)

        root.addLayout(top)

        body = QHBoxLayout()
        body.setSpacing(14)

        files = glass()
        fl = QVBoxLayout(files)
        fl.setContentsMargins(20, 18, 20, 18)
        fl.addWidget(label("Changed files", "SectionTitle"))

        self.changed_files = QListWidget()
        self.changed_files.setStyleSheet(
            """
            QListWidget {
                background: rgba(255,255,255,6);
                border: none;
                border-radius: 16px;
                padding: 7px;
            }
            QListWidget::item { padding: 8px; }
            """
        )
        fl.addWidget(self.changed_files, 1)

        vision = glass()
        vl = QVBoxLayout(vision)
        vl.setContentsMargins(20, 18, 20, 18)
        vl.addWidget(label("Current screen", "SectionTitle"))

        self.screen_preview = ScreenshotPreview()
        vl.addWidget(self.screen_preview, 1)

        body.addWidget(files, 1)
        body.addWidget(vision, 2)

        root.addLayout(body, 1)

    def set_ready(self, ready):
        self.capture_button.setEnabled(bool(ready))
        self.refresh_button.setEnabled(bool(ready))

    def capture_screen(self):
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            self.screen_preview.set_pixmap(None)
            return

        self.screen_preview.set_pixmap(
            screen.grabWindow(0)
        )

    def apply_snapshot(self, snapshot):
        self.updated.setText(
            "Last updated "
            + str(snapshot.get("updated_at_text") or "—")
        )

        self.project_value.setText(
            str(snapshot.get("project") or "—")
        )
        self.project_path.setText(
            str(snapshot.get("project_path") or "")
        )

        self.app_value.setText(
            str(snapshot.get("active_app") or "—")
        )
        self.app_detail.setText(
            "Live Windows foreground window"
            if snapshot.get("active_app")
            else "Foreground-window data unavailable."
        )

        git = snapshot.get("git") or {}
        self.branch_value.setText(
            str(git.get("branch") or "—")
        )

        changed_count = git.get("changed_count")
        self.git_detail.setText(
            f"{changed_count} changed files"
            if changed_count is not None
            else ""
        )

        self.changed_files.clear()
        changed = git.get("changed_files") or []

        for item in changed:
            self.changed_files.addItem(
                QListWidgetItem(str(item))
            )

        if not changed:
            self.changed_files.addItem(
                "No changed files."
                if changed_count == 0
                else "Git status unavailable."
            )


class ActivityPage(QWidget):
    conversation_selected = Signal(dict)

    def __init__(self):
        super().__init__()
        self.setObjectName("PageCanvas")
        self._conversations = []

        root = QVBoxLayout(self)
        root.setContentsMargins(4, 8, 4, 4)
        root.setSpacing(14)

        header = QHBoxLayout()
        titles = QVBoxLayout()
        titles.addWidget(label("Activity", "PageTitle"))
        titles.addWidget(
            label(
                "Conversation history and verified runtime activity.",
                "PageSubtitle",
            )
        )

        header.addLayout(titles)
        header.addStretch()

        self.updated = label("Last updated —", "UpdatedAt")
        header.addWidget(self.updated)

        root.addLayout(header)

        body = QHBoxLayout()
        body.setSpacing(14)

        conversations = glass()
        conversation_layout = QVBoxLayout(conversations)
        conversation_layout.setContentsMargins(18, 16, 18, 16)
        conversation_layout.addWidget(label("Conversations", "SectionTitle"))

        self.conversation_list = QListWidget()
        self.conversation_list.itemDoubleClicked.connect(
            self._open_conversation
        )
        conversation_layout.addWidget(self.conversation_list, 1)

        runtime = glass()
        runtime_layout = QVBoxLayout(runtime)
        runtime_layout.setContentsMargins(18, 16, 18, 16)
        runtime_layout.addWidget(label("Runtime activity", "SectionTitle"))

        self.runtime_list = QListWidget()
        runtime_layout.addWidget(self.runtime_list, 1)

        body.addWidget(conversations, 1)
        body.addWidget(runtime, 1)

        root.addLayout(body, 1)

    def set_ready(self, ready):
        self.conversation_list.setEnabled(bool(ready))
        self.runtime_list.setEnabled(bool(ready))

    def _open_conversation(self, item):
        index = item.data(Qt.UserRole)
        if isinstance(index, int) and 0 <= index < len(self._conversations):
            self.conversation_selected.emit(
                self._conversations[index]
            )

    def apply_snapshot(self, snapshot):
        self.updated.setText(
            "Last updated "
            + str(snapshot.get("updated_at_text") or "—")
        )

        self._conversations = snapshot.get("conversations") or []
        self.conversation_list.clear()

        for index, item in enumerate(self._conversations):
            user = str(item.get("user_text") or "Conversation")
            row = QListWidgetItem(user[:120])
            row.setData(Qt.UserRole, index)
            self.conversation_list.addItem(row)

        if not self._conversations:
            self.conversation_list.addItem("No saved conversations found.")

        self.runtime_list.clear()
        activity = snapshot.get("activity") or []

        for item in activity[:30]:
            timestamp = item.get("timestamp")
            when = (
                datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")
                if isinstance(timestamp, (int, float))
                else ""
            )

            text = item.get("user_text") or "Request"
            total = item.get("total_seconds")
            suffix = (
                f" · {float(total):.1f}s"
                if isinstance(total, (int, float))
                else ""
            )

            self.runtime_list.addItem(
                f"{when}  {text}{suffix}"
            )

        if not activity:
            self.runtime_list.addItem("No telemetry activity found.")


class SystemPage(QWidget):
    refresh_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setObjectName("PageCanvas")

        root = QVBoxLayout(self)
        root.setContentsMargins(4, 8, 4, 4)
        root.setSpacing(14)

        head = QHBoxLayout()
        titles = QVBoxLayout()
        titles.addWidget(label("System", "PageTitle"))
        titles.addWidget(
            label(
                "Health, capabilities, performance, and debugging detail.",
                "PageSubtitle",
            )
        )

        head.addLayout(titles)
        head.addStretch()

        self.updated = label("Last updated —", "UpdatedAt")
        head.addWidget(self.updated)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setObjectName("DarkPill")
        self.refresh_button.setEnabled(False)
        self.refresh_button.clicked.connect(self.refresh_requested.emit)
        head.addWidget(self.refresh_button)

        root.addLayout(head)

        summary = QHBoxLayout()

        self.overall_block = StatusBlock("Overall health", "CHECKING")
        self.voice_block = StatusBlock("Wake runtime", "CHECKING")
        self.backend_block = StatusBlock("Backend", "CHECKING")

        summary.addWidget(self.overall_block)
        summary.addWidget(self.voice_block)
        summary.addWidget(self.backend_block)

        root.addLayout(summary)

        grid = QGridLayout()
        grid.setSpacing(14)

        self.health_list = self._list_card("Health components")
        self.tools_list = self._list_card("Tools / features")
        self.integrations_list = self._list_card("Integrations")
        self.memory_list = self._list_card("Memory / performance")

        grid.addWidget(self.health_list[0], 0, 0)
        grid.addWidget(self.tools_list[0], 0, 1)
        grid.addWidget(self.integrations_list[0], 1, 0)
        grid.addWidget(self.memory_list[0], 1, 1)

        root.addLayout(grid, 1)

    def set_ready(self, ready):
        self.refresh_button.setEnabled(bool(ready))

    def _list_card(self, title):
        card = glass()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.addWidget(label(title, "SectionTitle"))

        widget = QListWidget()
        layout.addWidget(widget, 1)
        return card, widget

    def apply_snapshot(self, snapshot):
        self.updated.setText(
            "Last updated "
            + str(snapshot.get("updated_at_text") or "—")
        )

        health = snapshot.get("health") or {}
        overall = health.get("overall") or "UNKNOWN"

        self.overall_block.set_status(overall, overall)

        voice_active = bool(
            snapshot.get("voice_running")
            or snapshot.get("voice_enabled")
        )

        self.voice_block.set_status(
            "ACTIVE" if voice_active else "INACTIVE",
            "ACTIVE" if voice_active else "INACTIVE",
        )

        online = bool(snapshot.get("backend_online"))
        self.backend_block.set_status(
            "ONLINE" if online else "OFFLINE",
            "ONLINE" if online else "OFFLINE",
        )

        self.health_list[1].clear()
        for item in (health.get("components") or [])[:30]:
            component = item.get("component") or "component"
            status = item.get("status") or "UNKNOWN"
            detail = item.get("detail") or ""
            self.health_list[1].addItem(
                f"{component}  ·  {status}\n{detail}"
            )

        if self.health_list[1].count() == 0:
            self.health_list[1].addItem("Health data unavailable.")

        tools = snapshot.get("tools") or {}
        self.tools_list[1].clear()
        count = tools.get("count")
        self.tools_list[1].addItem(
            f"Registered tools: {count if count is not None else '—'}"
        )

        for item in (tools.get("items") or [])[:30]:
            self.tools_list[1].addItem(
                f"{item.get('name')}  ·  {item.get('risk')}\n"
                f"{item.get('description') or ''}"
            )

        integrations = snapshot.get("integrations") or {}
        self.integrations_list[1].clear()
        self.integrations_list[1].addItem(
            f"Providers: {integrations.get('providers') if integrations.get('providers') is not None else '—'}"
        )
        self.integrations_list[1].addItem(
            f"Capabilities: {integrations.get('capabilities') if integrations.get('capabilities') is not None else '—'}"
        )
        self.integrations_list[1].addItem(
            f"Accounts: {integrations.get('accounts') if integrations.get('accounts') is not None else '—'}"
        )

        for account in (integrations.get("account_items") or [])[:20]:
            status = (
                "ready"
                if account.get("connected") and account.get("authenticated")
                else "limited"
            )
            self.integrations_list[1].addItem(
                f"{account.get('provider')}:{account.get('account_id')} · {status}"
            )

        memory = snapshot.get("memory") or {}
        perf = snapshot.get("performance") or {}

        self.memory_list[1].clear()
        self.memory_list[1].addItem(
            f"Active memories: {memory.get('active_memories') if memory.get('active_memories') is not None else '—'}"
        )
        self.memory_list[1].addItem(
            "Latest total: " + fmt_seconds(perf.get("latest_total_seconds"))
        )
        self.memory_list[1].addItem(
            "First sentence: " + fmt_seconds(perf.get("latest_first_sentence_seconds"))
        )
        self.memory_list[1].addItem(
            "First audio: " + fmt_seconds(perf.get("latest_first_audio_seconds"))
        )


def fmt_seconds(value):
    return (
        f"{float(value):.2f}s"
        if isinstance(value, (int, float))
        else "—"
    )


def build_insight_summary(snapshot):
    insights = build_insights(snapshot)
    if not insights:
        return "Insights", "No verified issue or trend detected yet."
    return "Insights", insights[0]


def build_insights(snapshot):
    items = []

    health = snapshot.get("health") or {}
    overall = health.get("overall")

    if overall and str(overall).upper() != "HEALTHY":
        items.append(f"System health is {overall}.")

    git = snapshot.get("git") or {}
    changed_count = git.get("changed_count")

    if isinstance(changed_count, int) and changed_count > 0:
        items.append(
            f"Project has {changed_count} uncommitted Git changes."
        )

    performance = snapshot.get("performance") or {}
    first_sentence = performance.get("latest_first_sentence_seconds")

    if isinstance(first_sentence, (int, float)):
        if first_sentence > 6:
            items.append(
                f"Latest first-sentence latency is {first_sentence:.1f}s, above the conversational target."
            )
        elif first_sentence <= 3:
            items.append(
                f"Latest first-sentence latency is {first_sentence:.1f}s, inside the fast conversational range."
            )

    integrations = snapshot.get("integrations") or {}
    accounts = integrations.get("account_items") or []

    limited = [
        item
        for item in accounts
        if not (
            item.get("connected")
            and item.get("authenticated")
        )
    ]

    if limited:
        items.append(
            f"{len(limited)} connected-service accounts need attention."
        )

    if snapshot.get("voice_running") or snapshot.get("voice_enabled"):
        items.append("Wake-word runtime is armed in the background.")

    if not items:
        items.append("No verified runtime issue is currently surfaced.")

    return items
