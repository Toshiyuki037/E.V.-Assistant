"""
E.V.I.E. Desktop Backend Runtime Adapter

IMPORTANT:
    This file does NOT edit assistant/main.py or any backend file.

    The existing assistant/main.py contains the terminal/voice startup loop at
    module scope. Importing it normally would start "Mode:" and block the GUI.

    To keep the backend frozen, this adapter loads the exact backend source
    only through the "# Startup" boundary, registers that safe module in
    sys.modules as assistant.main, then performs the SAME initialization calls
    that the backend already performs before its terminal menu.

    All prompt routing, tools, memory, integrations, health, agent behavior,
    computer control, and voice functions remain the original backend code.
"""

from __future__ import annotations

import importlib
import io
import importlib.util
import json
import os
import sqlite3
import subprocess
import sys
import threading
import time
import types
from collections import deque
from pathlib import Path
from typing import Any, Callable

from .resource_paths import (
    application_dir,
    is_frozen,
    resource_path,
    runtime_path,
)


STARTUP_MARKER = (
    "# ---------------------------------------------------------------------------\n"
    "# Startup\n"
    "# ---------------------------------------------------------------------------\n"
)


class _TranscriptTee(io.TextIOBase):
    """
    Mirrors the backend listener's stdout to the original terminal while
    extracting only STT lifecycle/transcript lines for the desktop UI.

    This modifies no backend file.
    """

    def __init__(self, original, callback):
        super().__init__()
        self.original = original
        self.callback = callback
        self.buffer = ""

    def write(self, value):
        text = str(value or "")

        try:
            self.original.write(text)
            self.original.flush()
        except Exception:
            pass

        self.buffer += text

        while "\n" in self.buffer:
            line, self.buffer = self.buffer.split("\n", 1)
            self._parse_line(line.strip())

        return len(text)

    def flush(self):
        try:
            self.original.flush()
        except Exception:
            pass

    def _parse_line(self, line):
        if not line or self.callback is None:
            return

        if line.startswith("[Partial"):
            _, _, value = line.partition("] ")
            self.callback("partial", value.strip())
            return

        if line.startswith("[Final transcript"):
            _, _, value = line.partition("] ")
            self.callback("final", value.strip())
            return

        if line == "Speech detected.":
            self.callback("listening", "Listening…")
            return

        if line == "Speech complete.":
            self.callback("finalizing", "Finalizing transcription…")
            return

        if line == "Finalizing transcription...":
            self.callback("finalizing", "Finalizing transcription…")
            return

        if line == "[Transcript revised]":
            self.callback("revision", "")
            return


class BackendRuntime:
    def __init__(
        self,
        *,
        on_state: Callable[[str, str], None] | None = None,
        on_response: Callable[[str, str], None] | None = None,
        on_activity: Callable[[str, str], None] | None = None,
        on_error: Callable[[str], None] | None = None,
        on_transcript: Callable[[str, str], None] | None = None,
    ):
        self.on_state = on_state
        self.on_response = on_response
        self.on_activity = on_activity
        self.on_error = on_error
        self.on_transcript = on_transcript

        # Read-only source/bundle root. In a PyInstaller build this points
        # at _internal, where assistant/main.py is bundled as source data.
        self.project_root = (
            resource_path()
        )

        self.backend_main_path = (
            resource_path(
                "assistant",
                "main.py",
            )
        )

        # Runtime remains writable next to EVIE.exe. The installer uses a
        # per-user LocalAppData location, avoiding Program Files permissions.
        self.runtime_dir = (
            runtime_path()
        )

        self.display_project_root = (
            application_dir()
            if is_frozen()
            else self.project_root
        )

        self.display_project_name = (
            "E.V.I.E."
            if is_frozen()
            else self.project_root.name
        )

        self.module = None

        self.ready = False
        self.voice_running = False
        self.voice_enabled = True
        self.shutting_down = False

        # Desktop-only voice presentation state. This does not alter the
        # backend wake/session implementation; it only controls what the UI
        # is allowed to call "Listening".
        self._command_capture_active = False

        self._process_lock = threading.RLock()
        self._voice_thread = None
        self._voice_loop_lock = threading.Lock()

        self._response_history = deque(
            maxlen=40
        )

    # -----------------------------------------------------------------------
    # Backend load
    # -----------------------------------------------------------------------

    def initialize(self):
        self._state(
            "starting",
            "Loading backend modules and resident speech models...",
        )

        module = (
            self._load_frozen_main_without_cli()
        )

        self.module = module

        self._install_conversation_observer()
        self._install_playback_observer()

        # These are the same startup operations already present in
        # assistant/main.py. We call them here because the CLI startup block
        # was intentionally not executed.
        module.init_memory()

        self._state(
            "starting",
            "Preparing semantic memory...",
        )

        module.sync_memory_embeddings()

        module.start_background_prewarm(
            delay_seconds=1.0
        )

        module.start_tts_prewarm()

        self.ready = True

        self._activity(
            "Backend initialized",
            "now",
        )

        self._state(
            "starting",
            "Starting always-on wake runtime...",
        )

        self.ensure_voice_active()

    def _load_frozen_main_without_cli(self):
        if not self.backend_main_path.exists():
            raise RuntimeError(
                f"Backend not found: {self.backend_main_path}"
            )

        source = (
            self.backend_main_path.read_text(
                encoding="utf-8"
            )
        )

        if STARTUP_MARKER not in source:
            raise RuntimeError(
                "assistant/main.py startup boundary was not found. "
                "The backend file was not modified."
            )

        runtime_source = (
            source.split(
                STARTUP_MARKER,
                1,
            )[0]
        )

        # Preserve package-relative imports exactly as assistant.main expects.
        spec = (
            importlib.util.spec_from_file_location(
                "assistant.main",
                self.backend_main_path,
            )
        )

        module = (
            types.ModuleType(
                "assistant.main"
            )
        )

        module.__file__ = str(
            self.backend_main_path
        )
        module.__package__ = (
            "assistant"
        )
        module.__spec__ = spec

        # Backend modules that reference assistant.main will see this safe
        # runtime module instead of importing the CLI loop.
        sys.modules[
            "assistant.main"
        ] = module

        code = compile(
            runtime_source,
            str(
                self.backend_main_path
            ),
            "exec",
        )

        exec(
            code,
            module.__dict__,
        )

        return module

    # -----------------------------------------------------------------------
    # Conversation observer
    # -----------------------------------------------------------------------

    def _install_conversation_observer(self):
        """
        Observe the backend's existing save_conversation call in-memory.

        The original save function still executes unchanged. This only mirrors
        completed responses to the UI.
        """

        original = (
            self.module.save_conversation
        )

        runtime = self

        def observed_save_conversation(
            user_text,
            response,
        ):
            result = original(
                user_text,
                response,
            )

            user_value = str(
                user_text
                or ""
            ).strip()

            response_value = str(
                response
                or ""
            ).strip()

            runtime._response_history.append(
                {
                    "user_text":
                        user_value,

                    "response":
                        response_value,

                    "timestamp":
                        time.time(),
                }
            )

            if runtime.on_response:
                runtime.on_response(
                    user_value,
                    response_value,
                )

            return result

        self.module.save_conversation = (
            observed_save_conversation
        )


    def _install_playback_observer(self):
        """
        Mark UI speaking state whenever the existing main.py playback function
        is used. The original playback function remains authoritative.
        """

        original_play_audio = (
            self.module.play_audio
        )

        runtime = self

        def observed_play_audio(
            audio,
            sample_rate,
        ):
            runtime._state(
                "speaking",
                "Speaking…",
            )

            return original_play_audio(
                audio,
                sample_rate,
            )

        self.module.play_audio = (
            observed_play_audio
        )


    def _listen_with_ui_observer(self):
        """
        Execute the original backend listen() unchanged while mirroring its
        partial/final transcription output to the frontend.
        """

        if self.on_transcript is None:
            return self.module.listen()

        original_stdout = sys.stdout

        tee = _TranscriptTee(
            original_stdout,
            self._transcript,
        )

        try:
            sys.stdout = tee

            return self.module.listen()

        finally:
            try:
                if tee.buffer.strip():
                    tee._parse_line(
                        tee.buffer.strip()
                    )
            except Exception:
                pass

            sys.stdout = original_stdout


    # -----------------------------------------------------------------------
    # Text requests
    # -----------------------------------------------------------------------

    def execute_text(
        self,
        text: str,
    ):
        if not self.ready:
            raise RuntimeError(
                "E.V.I.E. backend is still loading."
            )

        value = str(
            text
            or ""
        ).strip()

        if not value:
            return

        with self._process_lock:
            self._state(
                "thinking",
                "Processing dashboard request...",
            )

            self._activity(
                value,
                "request",
            )

            started = (
                time.perf_counter()
            )

            try:
                # This IS the backend's original process_prompt function.
                # voice_streaming=False matches terminal typed requests.
                self.module.process_prompt(
                    value,
                    voice_streaming=False,
                )

            finally:
                elapsed = (
                    time.perf_counter()
                    - started
                )

                self._activity(
                    "Request completed",
                    f"{elapsed:.2f}s",
                )

                if self.voice_enabled:
                    self._state(
                        "listening",
                        "Wake word active.",
                    )

                else:
                    self._state(
                        "standing by",
                        "Voice wake is not active.",
                    )

        return elapsed

    # -----------------------------------------------------------------------
    # Always-on wake session
    # -----------------------------------------------------------------------

    def ensure_voice_active(self):
        if not self.ready:
            return False

        self.voice_enabled = True

        if (
            self._voice_thread is not None
            and self._voice_thread.is_alive()
        ):
            return True

        self._voice_thread = (
            threading.Thread(
                target=self._voice_loop,
                daemon=True,
                name="evie-desktop-wake-session",
            )
        )

        self._voice_thread.start()

        return True

    def _voice_loop(self):
        with self._voice_loop_lock:
            self.voice_running = True

            try:
                while (
                    not self.shutting_down
                    and self.voice_enabled
                ):
                    self._state(
                        "standing by",
                        "Online. Wake word armed.",
                    )

                    try:
                        result = (
                            self.module.run_voice_session(
                                listen_fn=
                                    self._listen_with_ui_observer,

                                process_prompt_fn=
                                    self._process_voice_prompt,

                                interrupt_speech_fn=
                                    self.module.stop_audio,

                                pause_speech_fn=
                                    self.module.pause_audio,

                                resume_speech_fn=
                                    self.module.resume_audio,

                                speech_started_fn=
                                    self.module.pause_audio,

                                require_wake=
                                    True,

                                wake_authenticate_fn=
                                    self.module.authenticate_last_wake_utterance,

                                wake_authenticated_fn=
                                    self._wake_authenticated,

                                wake_unrecognized_fn=
                                    self._wake_unrecognized,
                            )
                        )

                        if (
                            getattr(
                                result,
                                "quit_application",
                                False,
                            )
                        ):
                            self.voice_enabled = (
                                False
                            )
                            break

                    except Exception as error:
                        if self.shutting_down:
                            break

                        self._error(
                            f"Voice session: {type(error).__name__}: {error}"
                        )

                        time.sleep(
                            0.75
                        )

                    # The desktop app owns the lifecycle. If the legacy voice
                    # session returns to its old "mode selection", restart the
                    # wake listener automatically.
                    if (
                        self.voice_enabled
                        and not self.shutting_down
                    ):
                        time.sleep(
                            0.15
                        )

            finally:
                self.voice_running = (
                    False
                )

                if not self.shutting_down:
                    self._state(
                        "standing by",
                        "Wake session stopped.",
                    )

    def _process_voice_prompt(
        self,
        user_text,
    ):
        self._transcript(
            "final",
            str(
                user_text
                or ""
            ).strip(),
        )

        with self._process_lock:
            self._state(
                "thinking",
                "Processing voice request...",
            )

            try:
                return (
                    self.module.process_voice_prompt(
                        user_text
                    )
                )

            finally:
                if self.voice_enabled:
                    self._state(
                        "standing by",
                        "Online. Wake word armed.",
                    )

    def _wake_authenticated(self):
        self._state(
            "authenticated",
            "Wake word detected. Identity confirmed.",
        )

        self._state(
            "speaking",
            "Identity confirmed.",
        )

        result = (
            self.module.speak_authenticated_wake()
        )

        # From this point forward the next listen() belongs to the user's
        # actual request. This is the only state the desktop labels LISTENING.
        self._command_capture_active = True

        self._state(
            "listening",
            "Listening for your request...",
        )

        return result

    def _wake_unrecognized(self):
        self._command_capture_active = False

        self._state(
            "attention",
            "Voice identity was not recognized.",
        )

        self._state(
            "speaking",
            "Voice identity was not recognized.",
        )

        result = (
            self.module.speak_unrecognized_wake()
        )

        self._state(
            "standing by",
            "Online. Wake word armed.",
        )

        return result

    # -----------------------------------------------------------------------
    # Real data snapshot
    # -----------------------------------------------------------------------

    def snapshot(self):
        """
        Return only data we can actually verify from the runtime/project.

        Missing/unavailable data is None, never a fabricated placeholder.
        """

        now = time.time()

        data = {
            "updated_at":
                now,

            "updated_at_text":
                time.strftime(
                    "%H:%M:%S",
                    time.localtime(
                        now
                    ),
                ),

            "backend_online":
                bool(
                    self.ready
                ),

            "voice_running":
                bool(
                    self.voice_running
                ),

            "voice_enabled":
                bool(
                    self.voice_enabled
                ),

            "active_app":
                self._active_window_title(),

            "project":
                self.display_project_name,

            "project_path":
                str(
                    self.display_project_root
                ),

            "packaged":
                bool(
                    is_frozen()
                ),

            "git":
                self._git_snapshot(),

            "health":
                self._health_snapshot(),

            "tools":
                self._tool_snapshot(),

            "integrations":
                self._integration_snapshot(),

            "memory":
                self._memory_snapshot(),

            "performance":
                self._performance_snapshot(),

            "activity":
                self._telemetry_activity(),

            "response_history":
                list(
                    self._response_history
                ),

            "conversations":
                self._conversation_snapshot(),
        }

        return data

    def _health_snapshot(self):
        try:
            health = (
                importlib.import_module(
                    "assistant.system.health"
                )
            )

            results = (
                health.run_quick_health_check()
            )

            components = []

            for item in results:
                components.append(
                    {
                        "component":
                            item.component,

                        "status":
                            item.status,

                        "detail":
                            item.detail,
                    }
                )

            overall = (
                health.overall_health_status(
                    results
                )
            )

            return {
                "overall":
                    overall,

                "components":
                    components,
            }

        except Exception as error:
            return {
                "overall":
                    None,

                "components":
                    [],

                "error":
                    str(
                        error
                    ),
            }

    def _tool_snapshot(self):
        try:
            registry = (
                importlib.import_module(
                    "assistant.tools.registry"
                )
            )

            registry.load_default_tools()

            tools = (
                registry.list_tools()
            )

            return {
                "count":
                    len(
                        tools
                    ),

                "items":
                    [
                        {
                            "name":
                                item.name,

                            "category":
                                item.category,

                            "risk":
                                item.risk,

                            "description":
                                item.description,
                        }

                        for item
                        in tools
                    ],
            }

        except Exception as error:
            return {
                "count":
                    None,

                "items":
                    [],

                "error":
                    str(
                        error
                    ),
            }

    def _integration_snapshot(self):
        result = {
            "providers":
                None,

            "capabilities":
                None,

            "accounts":
                None,

            "account_items":
                [],
        }

        try:
            registry = (
                importlib.import_module(
                    "assistant.integrations.registry"
                )
            )

            registry.load_default_integrations(
                include_mock=False
            )

            summary = (
                registry.get_registry_summary()
            )

            result[
                "providers"
            ] = summary.get(
                "provider_count"
            )

            result[
                "capabilities"
            ] = summary.get(
                "capability_count"
            )

        except Exception as error:
            result[
                "registry_error"
            ] = str(
                error
            )

        try:
            connections = (
                importlib.import_module(
                    "assistant.integrations.connections"
                )
            )

            accounts = (
                connections.load_accounts()
            )

            result[
                "accounts"
            ] = len(
                accounts
            )

            result[
                "account_items"
            ] = [
                {
                    "provider":
                        item.provider,

                    "account_id":
                        item.account_id,

                    "display_name":
                        item.display_name,

                    "connected":
                        bool(
                            item.connected
                        ),

                    "authenticated":
                        bool(
                            item.authenticated
                        ),
                }

                for item
                in accounts
            ]

        except Exception as error:
            result[
                "accounts_error"
            ] = str(
                error
            )

        return result

    def _memory_snapshot(self):
        result = {
            "active_memories":
                None,

            "database":
                None,
        }

        try:
            database = (
                importlib.import_module(
                    "assistant.memory.database"
                )
            )

            db_path = Path(
                database.DB_PATH
            )

            result[
                "database"
            ] = str(
                db_path
            )

            memories = (
                database.get_active_memories()
            )

            result[
                "active_memories"
            ] = len(
                memories
            )

        except Exception as error:
            result[
                "error"
            ] = str(
                error
            )

        return result


    def _conversation_snapshot(self):
        """
        Read recent saved conversations without assuming one exact historic
        schema. This is read-only and exists only to populate the desktop chat.
        """

        try:
            database = importlib.import_module(
                "assistant.memory.database"
            )

            with database.get_connection() as conn:
                columns = [
                    row["name"]
                    for row in conn.execute(
                        "PRAGMA table_info(conversations)"
                    ).fetchall()
                ]

                if not columns:
                    return []

                order_column = None

                for candidate in (
                    "created_at",
                    "timestamp",
                    "updated_at",
                    "id",
                ):
                    if candidate in columns:
                        order_column = candidate
                        break

                sql = "SELECT * FROM conversations"

                if order_column:
                    sql += f" ORDER BY {order_column} DESC"

                sql += " LIMIT 30"

                rows = conn.execute(
                    sql
                ).fetchall()

            items = []

            for row in reversed(rows):
                values = dict(row)

                user_text = (
                    values.get("user_text")
                    or values.get("user")
                    or values.get("prompt")
                    or values.get("input")
                    or ""
                )

                response = (
                    values.get("response")
                    or values.get("assistant_text")
                    or values.get("assistant")
                    or values.get("output")
                    or ""
                )

                timestamp = (
                    values.get("created_at")
                    or values.get("timestamp")
                    or values.get("updated_at")
                    or ""
                )

                if user_text or response:
                    items.append(
                        {
                            "user_text": str(user_text or ""),
                            "response": str(response or ""),
                            "timestamp": str(timestamp or ""),
                        }
                    )

            return items

        except Exception:
            return []


    def _performance_snapshot(self):
        telemetry_dir = (
            self.runtime_dir
            / "telemetry"
        )

        if not telemetry_dir.exists():
            return {
                "latest_total_seconds":
                    None,

                "latest_first_sentence_seconds":
                    None,

                "latest_first_audio_seconds":
                    None,

                "recent_total_seconds":
                    [],
            }

        files = sorted(
            telemetry_dir.glob(
                "*.json"
            ),
            key=lambda item:
                item.stat().st_mtime,
            reverse=True,
        )

        totals = []

        latest = None

        for path in files[
            :20
        ]:
            try:
                payload = json.loads(
                    path.read_text(
                        encoding="utf-8"
                    )
                )

            except Exception:
                continue

            total = (
                payload.get(
                    "total_seconds"
                )
            )

            if isinstance(
                total,
                (
                    int,
                    float,
                ),
            ):
                totals.append(
                    float(
                        total
                    )
                )

            if latest is None:
                latest = payload

        latest = (
            latest
            or {}
        )

        marks = (
            latest.get(
                "marks"
            )
            or {}
        )

        return {
            "latest_total_seconds":
                latest.get(
                    "total_seconds"
                ),

            "latest_first_sentence_seconds":
                marks.get(
                    "first_authoritative_sentence"
                ),

            "latest_first_audio_seconds":
                (
                    marks.get(
                        "first_audio_started"
                    )
                    or marks.get(
                        "audio_playback_started"
                    )
                ),

            "recent_total_seconds":
                totals,
        }

    def _telemetry_activity(self):
        telemetry_dir = (
            self.runtime_dir
            / "telemetry"
        )

        if not telemetry_dir.exists():
            return []

        paths = sorted(
            telemetry_dir.glob(
                "*.json"
            ),
            key=lambda item:
                item.stat().st_mtime,
            reverse=True,
        )[
            :12
        ]

        activity = []

        for path in paths:
            try:
                payload = json.loads(
                    path.read_text(
                        encoding="utf-8"
                    )
                )

            except Exception:
                continue

            activity.append(
                {
                    "user_text":
                        str(
                            payload.get(
                                "user_text",
                                ""
                            )
                        ),

                    "total_seconds":
                        payload.get(
                            "total_seconds"
                        ),

                    "timestamp":
                        path.stat().st_mtime,
                }
            )

        return activity

    def _git_snapshot(self):
        if is_frozen():
            return {
                "branch":
                    "installed",

                "changed_count":
                    0,

                "changed_files":
                    [],

                "installed_build":
                    True,
            }

        result = {
            "branch":
                None,

            "changed_count":
                None,

            "changed_files":
                [],
        }

        try:
            branch = subprocess.run(
                [
                    "git",
                    "branch",
                    "--show-current",
                ],
                cwd=
                    self.project_root,
                capture_output=
                    True,
                text=
                    True,
                timeout=
                    3,
                check=
                    False,
                creationflags=(
                    subprocess.CREATE_NO_WINDOW
                    if os.name == "nt"
                    else 0
                ),
            )

            value = (
                branch.stdout.strip()
            )

            result[
                "branch"
            ] = (
                value
                or None
            )

            status = subprocess.run(
                [
                    "git",
                    "status",
                    "--porcelain",
                ],
                cwd=
                    self.project_root,
                capture_output=
                    True,
                text=
                    True,
                timeout=
                    3,
                check=
                    False,
                creationflags=(
                    subprocess.CREATE_NO_WINDOW
                    if os.name == "nt"
                    else 0
                ),
            )

            lines = [
                line.rstrip()
                for line
                in status.stdout.splitlines()
                if line.strip()
            ]

            result[
                "changed_count"
            ] = len(
                lines
            )

            result[
                "changed_files"
            ] = lines[
                :20
            ]

        except Exception as error:
            result[
                "error"
            ] = str(
                error
            )

        return result

    @staticmethod
    def _active_window_title():
        if os.name != "nt":
            return None

        try:
            import ctypes

            user32 = (
                ctypes.windll.user32
            )

            hwnd = (
                user32.GetForegroundWindow()
            )

            if not hwnd:
                return None

            length = (
                user32.GetWindowTextLengthW(
                    hwnd
                )
            )

            if length <= 0:
                return None

            buffer = (
                ctypes.create_unicode_buffer(
                    length
                    + 1
                )
            )

            user32.GetWindowTextW(
                hwnd,
                buffer,
                length
                + 1,
            )

            value = (
                buffer.value.strip()
            )

            return (
                value
                or None
            )

        except Exception:
            return None



    def _transcript(
        self,
        kind,
        text,
    ):
        normalized = str(
            kind
            or ""
        ).lower()

        value = str(
            text
            or ""
        ).strip()

        # ---------------------------------------------------------------
        # EARLY WAKE VISUAL HINT
        # ---------------------------------------------------------------
        # Before authenticated command capture begins, the wake listener
        # already emits partial/final STT text. Keep suppressing those wake
        # transcripts from the dashboard chat, but if the first recognized
        # word starts with "ev" emit a PRESENTATION-ONLY runtime state.
        #
        # This does NOT authenticate the wake word and does NOT alter
        # run_voice_session(), STT, TTS, or assistant/main.py.
        if (
            not self._command_capture_active
            and normalized in {
                "partial",
                "final",
            }
            and value
        ):
            wake_text = (
                value.lower()
                .replace(".", "")
                .replace(",", "")
                .replace("!", "")
                .replace("?", "")
                .strip()
            )

            words = wake_text.split()

            first_word = (
                words[0]
                if words
                else ""
            )

            # Covers partial recognition such as:
            #   "ev"
            #   "eve"
            #   "evie"
            #
            # The real backend wake/authentication path remains authoritative.
            if first_word.startswith("ev"):
                self._state(
                    "wake_heard",
                    "Wake word forming…",
                )

        # The listener also emits partial/final text while waiting for the
        # wake phrase. Suppress that phase from the desktop chat.
        # "Listening" remains reserved for post-wake command capture.
        if (
            normalized in {
                "partial",
                "final",
                "listening",
                "finalizing",
                "revision",
            }
            and not self._command_capture_active
        ):
            return

        if self.on_transcript:
            self.on_transcript(
                str(
                    kind
                    or ""
                ),
                value,
            )


    # -----------------------------------------------------------------------
    # Lifecycle
    # -----------------------------------------------------------------------

    def shutdown(self):
        self.shutting_down = True
        self.voice_enabled = False

        try:
            if (
                self.module is not None
            ):
                self.module.stop_audio()

        except Exception:
            pass

    # -----------------------------------------------------------------------
    # Event helpers
    # -----------------------------------------------------------------------

    def _state(
        self,
        state,
        detail,
    ):
        if self.on_state:
            self.on_state(
                state,
                detail,
            )

    def _activity(
        self,
        title,
        value,
    ):
        if self.on_activity:
            self.on_activity(
                title,
                value,
            )

    def _error(
        self,
        message,
    ):
        if self.on_error:
            self.on_error(
                message
            )
