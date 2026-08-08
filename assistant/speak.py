from pathlib import Path
from f5_tts.api import F5TTS

ROOT = Path(__file__).resolve().parent.parent

REF_AUDIO = ROOT / "eve-voice" / "references" / "eve-neutral.wav"
REF_TEXT_FILE = ROOT / "eve-voice" / "references" / "eve-neutral.txt"

REF_TEXT = REF_TEXT_FILE.read_text(encoding="utf-8").strip()

print("Loading EVE voice model...")

tts = F5TTS(
    model="F5TTS_v1_Base"
)

print("EVE voice model ready.")


def speak(text: str):
    output = ROOT / "voice-output" / "latest.wav"
    output.parent.mkdir(exist_ok=True)

    tts.infer(
        ref_file=str(REF_AUDIO),
        ref_text=REF_TEXT,
        gen_text=text,
        file_wave=str(output),
    )

    return output