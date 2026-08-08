import tempfile
import wave

import sounddevice as sd
from faster_whisper import WhisperModel

SAMPLE_RATE = 16000
CHANNELS = 1
RECORD_SECONDS = 6

print("Loading speech recognition...")

whisper = WhisperModel(
    "small.en",
    device="cuda",
    compute_type="float16",
)

print("Speech recognition ready.")


def listen():
    print("\nListening...")

    audio = sd.rec(
        int(RECORD_SECONDS * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="int16",
    )

    sd.wait()

    with tempfile.NamedTemporaryFile(
        suffix=".wav",
        delete=False,
    ) as temp:
        filename = temp.name

    with wave.open(filename, "wb") as wav:
        wav.setnchannels(CHANNELS)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(audio.tobytes())

    segments, _ = whisper.transcribe(
        filename,
        language="en",
        beam_size=5,
    )

    text = " ".join(
        segment.text.strip()
        for segment in segments
    ).strip()

    return text