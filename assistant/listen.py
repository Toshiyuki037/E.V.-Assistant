import tempfile
import wave

import sounddevice as sd
from faster_whisper import WhisperModel


SAMPLE_RATE = 16000
CHANNELS = 1
RECORD_SECONDS = 5

print("Loading Whisper...")

model = WhisperModel(
    "small.en",
    device="cuda",
    compute_type="float16",
)

print("Whisper ready.")


def listen():
    print("Listening...")

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
    ) as temp_file:

        with wave.open(temp_file.name, "wb") as wav:
            wav.setnchannels(CHANNELS)
            wav.setsampwidth(2)
            wav.setframerate(SAMPLE_RATE)
            wav.writeframes(audio.tobytes())

        segments, info = model.transcribe(
            temp_file.name,
            beam_size=5,
        )

        text = " ".join(
            segment.text.strip()
            for segment in segments
        )

    return text


if __name__ == "__main__":
    text = listen()
    print("You said:", text)