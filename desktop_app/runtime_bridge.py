from __future__ import annotations

import threading
import traceback

from PySide6.QtCore import (
    QObject,
    QMetaObject,
    Qt,
    QTimer,
    Signal,
    Slot,
)

from .backend_runtime import (
    BackendRuntime,
)


class EvieRuntimeBridge(QObject):
    connected = Signal(bool)
    state = Signal(str, str)
    response = Signal(str, str)
    activity = Signal(str, str)
    latency = Signal(float)
    snapshot_ready = Signal(dict)
    voice_status = Signal(bool)
    transcript = Signal(str, str)
    ready_changed = Signal(bool)
    error = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._ready = False
        self._busy = False
        self._snapshot_busy = False
        self._shutdown = False

        self.backend = BackendRuntime(
            on_state=self._emit_state,
            on_response=self._emit_response,
            on_activity=self._emit_activity,
            on_error=self._emit_error,
            on_transcript=self._emit_transcript,
        )

        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(5000)
        self.refresh_timer.timeout.connect(
            self.refresh_snapshot
        )

    @property
    def ready(self):
        return self._ready

    @property
    def busy(self):
        return self._busy

    @Slot()
    def start(self):
        if self._ready or self._shutdown:
            return

        self.state.emit(
            "starting",
            "Loading E.V.I.E. backend...",
        )

        threading.Thread(
            target=self._load_worker,
            daemon=True,
            name="evie-desktop-backend-loader",
        ).start()

    def _load_worker(self):
        try:
            print(
                "[E.V.I.E. runtime] initialize() entered.",
                flush=True,
            )

            self.backend.initialize()

            print(
                "[E.V.I.E. runtime] initialize() completed.",
                flush=True,
            )

            if self._shutdown:
                return

            self._ready = True
            self.connected.emit(True)

            self.voice_status.emit(
                bool(
                    self.backend.voice_running
                    or self.backend.voice_enabled
                )
            )

            self._snapshot_worker()

            self.ready_changed.emit(
                True
            )

            self.state.emit(
                "standing by",
                "Online. Wake word armed.",
            )

            QMetaObject.invokeMethod(
                self,
                "_start_refresh_timer",
                Qt.QueuedConnection,
            )

        except Exception as exc:
            self._ready = False
            self.connected.emit(False)
            self.ready_changed.emit(False)

            print(
                "[E.V.I.E. runtime] BACKEND INITIALIZATION FAILED",
                flush=True,
            )

            traceback.print_exc()

            self.state.emit(
                "error",
                "Backend failed to initialize.",
            )

            self.error.emit(
                f"{type(exc).__name__}: {exc}"
            )

    @Slot()
    def _start_refresh_timer(self):
        if (
            not self._shutdown
            and self._ready
        ):
            self.refresh_timer.start()

    @Slot(str)
    def submit(self, text: str):
        value = str(
            text
            or ""
        ).strip()

        if not value:
            return

        if not self._ready:
            self.error.emit(
                "E.V.I.E. is still loading."
            )
            return

        if self._busy:
            self.error.emit(
                "E.V.I.E. is already processing a request."
            )
            return

        self._busy = True

        threading.Thread(
            target=self._execute_worker,
            args=(value,),
            daemon=True,
            name="evie-desktop-text-request",
        ).start()

    def _execute_worker(self, text):
        try:
            elapsed = self.backend.execute_text(
                text
            )

            if isinstance(
                elapsed,
                (
                    int,
                    float,
                ),
            ):
                self.latency.emit(
                    float(
                        elapsed
                    )
                )

        except Exception as exc:
            self.error.emit(
                f"{type(exc).__name__}: {exc}"
            )
            self.state.emit(
                "error",
                "Request failed.",
            )

        finally:
            self._busy = False
            self.refresh_snapshot()

    @Slot()
    def ensure_voice_active(self):
        if not self._ready:
            self.error.emit(
                "E.V.I.E. is still loading."
            )
            return

        try:
            active = self.backend.ensure_voice_active()
            self.voice_status.emit(
                bool(active)
            )

        except Exception as exc:
            self.error.emit(
                f"{type(exc).__name__}: {exc}"
            )

    @Slot()
    def refresh_snapshot(self):
        if (
            not self._ready
            or self._snapshot_busy
            or self._shutdown
        ):
            return

        self._snapshot_busy = True

        threading.Thread(
            target=self._snapshot_worker,
            daemon=True,
            name="evie-desktop-snapshot",
        ).start()

    def _snapshot_worker(self):
        if not self._snapshot_busy:
            self._snapshot_busy = True

        try:
            snapshot = self.backend.snapshot()

            if not isinstance(
                snapshot,
                dict,
            ):
                raise RuntimeError(
                    "Backend snapshot did not return a dictionary."
                )

            self.snapshot_ready.emit(
                snapshot
            )

            self.voice_status.emit(
                bool(
                    snapshot.get("voice_running")
                    or snapshot.get("voice_enabled")
                )
            )

        except Exception as exc:
            self.error.emit(
                f"Snapshot: {type(exc).__name__}: {exc}"
            )

        finally:
            self._snapshot_busy = False

    def _emit_state(self, state, detail):
        self.state.emit(
            str(state or ""),
            str(detail or ""),
        )

    def _emit_response(self, user_text, response):
        self.response.emit(
            str(user_text or ""),
            str(response or ""),
        )

    def _emit_activity(self, title, value):
        self.activity.emit(
            str(title or ""),
            str(value or ""),
        )

    def _emit_transcript(self, kind, text):
        self.transcript.emit(
            str(kind or ""),
            str(text or ""),
        )

    def _emit_error(self, message):
        self.error.emit(
            str(message or "")
        )

    def shutdown(self):
        self._shutdown = True
        self.refresh_timer.stop()

        try:
            self.backend.shutdown()

        finally:
            self._ready = False
            self.connected.emit(False)
            self.ready_changed.emit(False)
