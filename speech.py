import tempfile
from pathlib import Path

import sounddevice as sd
from scipy.io.wavfile import write
from faster_whisper import WhisperModel


class WheatleySpeech:
    def __init__(self):
        print("Загрузка модели распознавания речи...")

        self.model = WhisperModel(
            "base",
            device="cpu",
            compute_type="int8"
        )

        print("Модель речи готова.")

    def record(self, seconds=8):
        sample_rate = 16000

        print("🎙️ Говори...")

        audio = sd.rec(
            int(seconds * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype="int16"
        )

        sd.wait()

        temp_file = tempfile.NamedTemporaryFile(
            suffix=".wav",
            delete=False
        )

        temp_file.close()

        write(
            temp_file.name,
            sample_rate,
            audio
        )

        return temp_file.name

    def transcribe(self, audio_path):
        segments, info = self.model.transcribe(
            audio_path,
            beam_size=5,
            vad_filter=True
        )

        text = " ".join(
            segment.text.strip()
            for segment in segments
        )

        Path(audio_path).unlink(
            missing_ok=True
        )

        return text.strip()