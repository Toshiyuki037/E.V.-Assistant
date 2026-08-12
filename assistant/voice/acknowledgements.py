"""E.V.I.E. Phase 14A.5 cached acknowledgement playback."""
from __future__ import annotations
import random
import threading
from pathlib import Path
import sounddevice as sd
import soundfile as sf

ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = ROOT / "runtime" / "voice_cache"
ACK_FILES = {
    "on_it": "on_it.wav",
    "got_it": "got_it.wav",
    "checking": "checking.wav",
    "working": "working_on_it.wav",
    "one_moment": "one_moment.wav",
    "yes_boss": "yes_boss.wav",
    "got_it_boss": "got_it_boss.wav",
}
DEFAULT_ACKS = ("on_it", "got_it", "checking", "yes_boss")
_play_lock = threading.Lock()

def acknowledgement_path(name: str) -> Path:
    return CACHE_DIR / ACK_FILES.get(name, name)

def acknowledgement_available(name: str) -> bool:
    return acknowledgement_path(name).is_file()

def available_acknowledgements() -> list[str]:
    return [name for name in ACK_FILES if acknowledgement_available(name)]

def _play_wav(path: Path) -> None:
    try:
        audio, sample_rate = sf.read(str(path))
        with _play_lock:
            sd.play(audio, sample_rate)
            sd.wait()
    except Exception as exc:
        print(f"[Voice acknowledgement warning] {exc}")

def play_acknowledgement(name: str | None = None, *, asynchronous: bool = True) -> bool:
    if name is None:
        choices = [x for x in DEFAULT_ACKS if acknowledgement_available(x)]
        if not choices:
            return False
        name = random.choice(choices)

    path = acknowledgement_path(name)
    if not path.is_file():
        return False

    if asynchronous:
        threading.Thread(
            target=_play_wav,
            args=(path,),
            daemon=True,
            name="evie-acknowledgement",
        ).start()
    else:
        _play_wav(path)
    return True

def choose_acknowledgement(*, long_task: bool = False, checking: bool = False) -> str | None:
    if checking:
        preferred = ("checking", "on_it", "got_it")
    elif long_task:
        preferred = ("on_it", "working", "got_it")
    else:
        preferred = DEFAULT_ACKS
    choices = [x for x in preferred if acknowledgement_available(x)]
    return random.choice(choices) if choices else None
