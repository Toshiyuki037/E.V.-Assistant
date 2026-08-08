import os
import tempfile
from pathlib import Path

import sounddevice as sd
import soundfile as sf
from f5_tts.api import F5TTS


ROOT = Path(__file__).resolve().parent.parent

REF_AUDIO = ROOT / "eve-voice" / "references" / "eve-neutral.wav"
REF_TEXT_FILE = ROOT / "eve-voice" / "references" / "eve-neutral.txt"

REF_TEXT = REF_TEXT_FILE.read_text(encoding="utf-8").strip()


print("Loading E.V. voice model...")

tts = F5TTS(
    model="F5TTS_v1_Base"
)

print("E.V. voice ready.")


def speak(text: str):
    temp_path = None

    try:
        # Temporary file only — not stored in voice-output
        with tempfile.NamedTemporaryFile(
            suffix=".wav",
            delete=False
        ) as temp:
            temp_path = temp.name

        # Generate E.V.'s speech
        tts.infer(
            ref_file=str(REF_AUDIO),
            ref_text=REF_TEXT,
            gen_text=text,
            file_wave=temp_path,
        )

        # Read generated audio
        audio, sample_rate = sf.read(temp_path)

        # Play directly through speakers
        sd.play(audio, sample_rate)
        sd.wait()

    finally:
        # Remove temporary audio after playback
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


if __name__ == "__main__":
    speak("Good evening, Max. E.V. voice systems are operating normally.")