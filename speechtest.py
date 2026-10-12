import subprocess
from faster_whisper import WhisperModel

print("Загружаю модель распознавания речи...")

model = WhisperModel(
    "tiny",
    device="cpu",
    compute_type="int8"
)

print("Wheatley готов! Говори в микрофон.")

while True:
    try:
        subprocess.run([
            "arecord",
            "-D", "plughw:2,0",
            "-d", "5",
            "-f", "S16_LE",
            "-r", "16000",
            "-c", "1",
            "speech.wav"
        ], check=True)

        segments, info = model.transcribe(
            "speech.wav",
            language="ru"
        )

        text = "".join(s.text for s in segments).strip()

        if text:
            print("Ты сказал:", text)
        else:
            print("Речь не распознана.")

    except KeyboardInterrupt:
        print("\nWheatley выключается.")
        break
    except Exception as error:
        print("Ошибка:", error)