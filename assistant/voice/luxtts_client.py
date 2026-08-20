from __future__ import annotations

import atexit
import base64
import json
import subprocess
import threading
import time
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent.parent.parent
LUX_ROOT = ROOT / "voice_benchmarks" / "LuxTTS"
LUX_SERVER = LUX_ROOT / "evie_luxtts_server.py"

LUX_PYTHON = Path(
    r"C:\Users\patro\miniconda3\envs\luxtts\python.exe"
)


class LuxTTSClient:
    def __init__(self):
        self._lock = threading.RLock()
        self._process = None
        self._stderr_thread = None
        self._closed = False

    @property
    def is_running(self) -> bool:
        process = self._process
        return process is not None and process.poll() is None

    def _stderr_worker(self, process):
        stream = process.stderr
        if stream is None:
            return

        try:
            for line in stream:
                line = line.rstrip()
                if line:
                    print(line)
        except Exception:
            pass

    def _read_response(self):
        process = self._process

        if process is None:
            raise RuntimeError("LuxTTS worker is not running.")

        stdout = process.stdout

        if stdout is None:
            raise RuntimeError("LuxTTS worker stdout is unavailable.")

        while True:
            line = stdout.readline()

            if not line:
                raise RuntimeError(
                    "LuxTTS worker stopped unexpectedly. "
                    f"Exit code: {process.poll()}"
                )

            line = line.strip()
            if not line:
                continue

            try:
                response = json.loads(line)
            except json.JSONDecodeError:
                print(f"[LuxTTS worker] {line}")
                continue

            if isinstance(response, dict):
                return response

    def start(self):
        with self._lock:
            if self._closed:
                raise RuntimeError("LuxTTS client is closed.")

            if self.is_running:
                return

            if not LUX_PYTHON.exists():
                raise FileNotFoundError(
                    f"LuxTTS Python environment not found: {LUX_PYTHON}"
                )

            if not LUX_SERVER.exists():
                raise FileNotFoundError(
                    f"LuxTTS worker not found: {LUX_SERVER}"
                )

            print("Loading E.V.I.E. LuxTTS voice...")

            self._process = subprocess.Popen(
                [
                    str(LUX_PYTHON),
                    "-u",
                    str(LUX_SERVER),
                ],
                cwd=str(LUX_ROOT),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                creationflags=(
                    subprocess.CREATE_NO_WINDOW
                    if hasattr(subprocess, "CREATE_NO_WINDOW")
                    else 0
                ),
            )

            self._stderr_thread = threading.Thread(
                target=self._stderr_worker,
                args=(self._process,),
                daemon=True,
                name="evie-luxtts-stderr",
            )
            self._stderr_thread.start()

            response = self._read_response()

            if response.get("type") != "ready":
                self.stop()
                raise RuntimeError(
                    f"LuxTTS failed to initialize: {response}"
                )

            print("E.V.I.E. LuxTTS voice ready.")

    def _send(self, payload):
        process = self._process

        if process is None or process.stdin is None:
            raise RuntimeError("LuxTTS worker stdin is unavailable.")

        process.stdin.write(
            json.dumps(payload, separators=(",", ":")) + "\n"
        )
        process.stdin.flush()

    def synthesize(self, text: str):
        text = str(text or "").strip()

        if not text:
            return None, 0

        with self._lock:
            if not self.is_running:
                self.start()

            started = time.monotonic()

            self._send(
                {
                    "command": "synthesize",
                    "text": text,
                }
            )

            response = self._read_response()
            response_type = response.get("type")

            if response_type == "error":
                raise RuntimeError(
                    response.get("error", "Unknown LuxTTS error.")
                )

            if response_type != "audio":
                raise RuntimeError(
                    f"Unexpected LuxTTS response: {response}"
                )

            sample_rate = int(
                response.get("sample_rate", 0)
            )

            encoded = response.get("audio", "")

            if not encoded:
                return None, sample_rate

            audio = np.frombuffer(
                base64.b64decode(encoded),
                dtype=np.float32,
            ).copy()

            print(
                "[LuxTTS] "
                f"{len(text)} chars synthesized in "
                f"{time.monotonic() - started:.3f}s"
            )

            return audio, sample_rate

    def prewarm(self):
        self.start()

    def stop(self):
        with self._lock:
            process = self._process
            self._process = None

            if process is None:
                return

            if process.poll() is None:
                try:
                    if process.stdin is not None:
                        process.stdin.write(
                            json.dumps({"command": "shutdown"}) + "\n"
                        )
                        process.stdin.flush()
                except Exception:
                    pass

                try:
                    process.wait(timeout=2.0)
                except subprocess.TimeoutExpired:
                    try:
                        process.terminate()
                        process.wait(timeout=1.0)
                    except Exception:
                        try:
                            process.kill()
                        except Exception:
                            pass


CLIENT = LuxTTSClient()
atexit.register(CLIENT.stop)
