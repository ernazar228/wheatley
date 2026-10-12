
import subprocess
from faster_whisper import WhisperModel

MICROPHONE = "plughw:2,0"
AUDIO_FILE = "/tmp/wheatley_speech.wav"

print("Загрузка модели распознавания...")

model = WhisperModel(
    "tiny",
    device="cpu",
    compute_type="int8"
)

print("Wheatley готов!")
print("Говори в микрофон. Для остановки нажми Ctrl+C.\n")

try:
    while True:
        print("Слушаю 5 секунд...")

        subprocess.run(
            [
                "arecord",
                "-D", MICROPHONE,
                "-d", "5",
                "-f", "S16_LE",
                "-r", "16000",
                "-c", "1",
                "-t", "wav",
                AUDIO_FILE
            ],
            check=True,
            stdout=subprocess.DEVNULL
        )

        segments, _ = model.transcribe(
            AUDIO_FILE,
            language="ru",
            beam_size=1,
            vad_filter=True
        )

        text = " ".join(
            segment.text.strip()
            for segment in segments
        ).strip()

        if text:
            print(f"Ты сказал: {text}\n")
        else:
            print("Речь не распознана.\n")

except KeyboardInterrupt:
    print("\nWheatley остановлен.")

except Exception as error:
    print(f"Ошибка: {error}")
