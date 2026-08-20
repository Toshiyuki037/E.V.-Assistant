from __future__ import annotations

import sys

from PySide6.QtCore import (
    QTimer,
    Qt,
)

from PySide6.QtGui import (
    QAction,
    QColor,
    QIcon,
    QPainter,
    QPixmap,
)

from PySide6.QtNetwork import (
    QLocalServer,
    QLocalSocket,
)

from PySide6.QtWidgets import (
    QApplication,
    QMenu,
    QSystemTrayIcon,
)

from .control_center import (
    ControlCenter,
)

from .orb_overlay import (
    EvieOrbOverlay,
)

from .resource_paths import (
    prepare_runtime_environment,
)

from .runtime_bridge import (
    EvieRuntimeBridge,
)

from .theme import (
    APP_QSS,
)

from .ui_assets import (
    app_profile_icon,
)


SINGLE_INSTANCE_NAME = (
    "EVIE_DESKTOP_V1_SINGLE_INSTANCE"
)


def create_fallback_icon():
    pixmap = QPixmap(
        64,
        64,
    )

    pixmap.fill(
        Qt.transparent
    )

    painter = QPainter(
        pixmap
    )

    painter.setRenderHint(
        QPainter.Antialiasing
    )

    painter.setPen(
        QColor(
            232,
            234,
            239,
            220,
        )
    )

    painter.drawEllipse(
        10,
        10,
        44,
        44,
    )

    painter.drawEllipse(
        17,
        17,
        30,
        30,
    )

    painter.setPen(
        QColor(
            248,
            248,
            250,
        )
    )

    painter.drawText(
        pixmap.rect(),
        Qt.AlignCenter,
        "E",
    )

    painter.end()

    return QIcon(
        pixmap
    )


def create_app_icon():
    profile = app_profile_icon()

    if not profile.isNull():
        return profile

    return create_fallback_icon()


def acquire_single_instance():
    probe = QLocalSocket()

    probe.connectToServer(
        SINGLE_INSTANCE_NAME
    )

    if probe.waitForConnected(
        250
    ):
        probe.write(
            b"SHOW"
        )

        probe.flush()

        probe.waitForBytesWritten(
            250
        )

        probe.disconnectFromServer()

        return None

    QLocalServer.removeServer(
        SINGLE_INSTANCE_NAME
    )

    server = QLocalServer()

    if not server.listen(
        SINGLE_INSTANCE_NAME
    ):
        raise RuntimeError(
            "Could not establish the E.V.I.E. single-instance server."
        )

    return server


class DesktopApplication:
    def __init__(
        self,
        app,
        instance_server,
    ):
        self.app = app
        self.instance_server = instance_server

        print(
            "[E.V.I.E. desktop] Creating control center...",
            flush=True,
        )

        self.window = ControlCenter()

        self.window.setWindowIcon(
            create_app_icon()
        )

        print(
            "[E.V.I.E. desktop] Creating runtime bridge...",
            flush=True,
        )

        self.runtime = EvieRuntimeBridge(
            self.window
        )

        # Orb is intentionally lazy. Loading ~240 PNGs should never block the
        # UI or delay backend/model startup.
        self.orb_overlay = None

        # -------------------------------------------------------------------
        # Runtime -> UI
        # -------------------------------------------------------------------

        self.runtime.connected.connect(
            self.window.set_connected
        )

        self.runtime.state.connect(
            self.window.set_runtime_state
        )

        self.runtime.response.connect(
            self.window.set_response
        )

        self.runtime.latency.connect(
            self.window.set_latency
        )

        self.runtime.snapshot_ready.connect(
            self.window.apply_snapshot
        )

        self.runtime.voice_status.connect(
            self.window.set_voice_active
        )

        self.runtime.transcript.connect(
            self.window.set_transcript
        )

        self.runtime.ready_changed.connect(
            self.window.set_runtime_ready
        )

        self.runtime.error.connect(
            self.window.show_runtime_error
        )

        # Debug-console visibility for packaged startup failures.
        self.runtime.error.connect(
            self._print_runtime_error
        )

        # -------------------------------------------------------------------
        # UI -> Runtime
        # -------------------------------------------------------------------

        self.window.prompt_requested.connect(
            self.runtime.submit
        )

        self.window.voice_requested.connect(
            self.runtime.ensure_voice_active
        )

        self.window.snapshot_refresh_requested.connect(
            self.runtime.refresh_snapshot
        )

        # -------------------------------------------------------------------
        # Single instance / tray
        # -------------------------------------------------------------------

        self.instance_server.newConnection.connect(
            self._handle_instance_message
        )

        self.tray = QSystemTrayIcon(
            create_app_icon(),
            self.app,
        )

        self.tray.setToolTip(
            "E.V.I.E. — wake word active in background"
        )

        menu = QMenu()

        open_action = QAction(
            "Open E.V.I.E.",
            menu,
        )

        open_action.triggered.connect(
            self.show_window
        )

        wake_action = QAction(
            "Ensure wake word active",
            menu,
        )

        wake_action.triggered.connect(
            self.runtime.ensure_voice_active
        )

        refresh_action = QAction(
            "Refresh system data",
            menu,
        )

        refresh_action.triggered.connect(
            self.runtime.refresh_snapshot
        )

        quit_action = QAction(
            "Quit E.V.I.E.",
            menu,
        )

        quit_action.triggered.connect(
            self.quit
        )

        menu.addAction(
            open_action
        )

        menu.addAction(
            wake_action
        )

        menu.addAction(
            refresh_action
        )

        menu.addSeparator()

        menu.addAction(
            quit_action
        )

        self.tray.setContextMenu(
            menu
        )

        self.tray.activated.connect(
            self._tray_activated
        )

        self.tray.show()

        # Paint the application before any model or animation asset work.
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()

        print(
            "[E.V.I.E. desktop] Starting backend worker...",
            flush=True,
        )

        # start() itself is non-blocking; it immediately launches the existing
        # backend initialization on its worker thread. Do not rely on a Qt
        # singleShot just to start the backend.
        self.runtime.start()

        # Create/preload the overlay only after the Qt event loop begins.
        QTimer.singleShot(
            0,
            self._initialize_orb_overlay,
        )

    def _initialize_orb_overlay(
        self,
    ):
        if self.orb_overlay is not None:
            return

        try:
            print(
                "[E.V.I.E. desktop] Loading orb overlay...",
                flush=True,
            )

            overlay = EvieOrbOverlay()

            self.orb_overlay = overlay

            self.runtime.state.connect(
                overlay.set_runtime_state
            )

            print(
                "[E.V.I.E. desktop] Orb overlay ready.",
                flush=True,
            )

        except Exception as error:
            # Orb is presentation-only. A rendering problem must never stop the
            # assistant runtime or the Control Center.
            print(
                (
                    "[E.V.I.E. desktop] Orb overlay unavailable: "
                    f"{type(error).__name__}: {error}"
                ),
                flush=True,
            )

    def _print_runtime_error(
        self,
        message,
    ):
        print(
            f"[E.V.I.E. runtime error] {message}",
            flush=True,
        )

    def _handle_instance_message(
        self,
    ):
        while self.instance_server.hasPendingConnections():
            socket = (
                self.instance_server.nextPendingConnection()
            )

            if socket is None:
                continue

            socket.waitForReadyRead(
                100
            )

            message = bytes(
                socket.readAll()
            ).decode(
                "utf-8",
                errors="ignore",
            ).strip().upper()

            socket.disconnectFromServer()
            socket.deleteLater()

            if (
                message == "SHOW"
                or not message
            ):
                self.show_window()

    def _tray_activated(
        self,
        reason,
    ):
        if reason in (
            QSystemTrayIcon.Trigger,
            QSystemTrayIcon.DoubleClick,
        ):
            self.show_window()

    def show_window(
        self,
    ):
        self.window.show()

        if self.window.isMinimized():
            self.window.showNormal()

        self.window.raise_()
        self.window.activateWindow()

    def quit(
        self,
    ):
        print(
            "[E.V.I.E. desktop] Shutting down...",
            flush=True,
        )

        self.runtime.shutdown()

        if self.orb_overlay is not None:
            try:
                self.orb_overlay.shutdown()
            except Exception:
                pass

        self.window.allow_real_close()
        self.window.close()

        self.tray.hide()

        try:
            self.instance_server.close()

            QLocalServer.removeServer(
                SINGLE_INSTANCE_NAME
            )

        except Exception:
            pass

        self.app.quit()


def main():
    prepare_runtime_environment()

    app = QApplication(
        sys.argv
    )

    app.setApplicationName(
        "E.V.I.E."
    )

    app.setQuitOnLastWindowClosed(
        False
    )

    app.setStyleSheet(
        APP_QSS
    )

    app.setWindowIcon(
        create_app_icon()
    )

    instance_server = acquire_single_instance()

    if instance_server is None:
        return 0

    print(
        "[E.V.I.E. desktop] First instance acquired.",
        flush=True,
    )

    desktop = DesktopApplication(
        app,
        instance_server,
    )

    print(
        "[E.V.I.E. desktop] Qt event loop online.",
        flush=True,
    )

    return app.exec()


if __name__ == "__main__":
    sys.exit(
        main()
    )
