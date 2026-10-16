import json
import math
import queue
import random
import subprocess
import threading
import time
from urllib.request import Request, urlopen

import pygame
from faster_whisper import WhisperModel

# Optional: use the project's existing voice.py if available.
try:
    from voice import WheatleyVoice
    voice = WheatleyVoice()
except Exception as error:
    print(f"Voice module unavailable; text answers will still work: {error}")
    voice = None


# ---------- SETTINGS ----------
MICROPHONE = "plughw:2,0"       # The working Raspberry Pi microphone
AUDIO_FILE = "/tmp/wheatley_speech.wav"
WHISPER_SIZE = "tiny"           # Lightweight for Raspberry Pi 5
OLLAMA_MODEL = "qwen3:4b-instruct"
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
RECORD_SECONDS = 5

WIDTH, HEIGHT = 800, 480
BG = (3, 5, 8)
WHITE = (230, 245, 255)
BLUE = (70, 170, 255)
DARK_BLUE = (15, 55, 110)
METAL = (135, 143, 150)
DARK_METAL = (48, 54, 62)

messages = queue.Queue()
busy = False
status = "Ready — press M to speak"
last_answer = ""
gesture = "neutral"
gesture_start = 0.0
gaze_x = 0.0
gaze_y = 0.0
target_x = 0.0
target_y = 0.0
next_blink = time.monotonic() + random.uniform(2.5, 5.0)
blink_until = 0.0
whisper = None


SYSTEM_PROMPT = """
You are Wheatley, a friendly, enthusiastic, slightly nervous robot inspired
by Portal 2. Reply naturally and briefly, usually in 1-3 sentences. Use the
same language as the user. No stage directions or emojis.
Return only JSON with this structure:
{"answer":"spoken response","gesture":"yes"}
gesture must be exactly "yes", "no", or "neutral".
Use "yes" for an affirmative answer, "no" for a negative answer, and
"neutral" for other questions.
"""


def ask_qwen(question):
    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "format": "json",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
        "options": {"temperature": 0.7, "num_predict": 140},
    }
    request = Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=180) as response:
        data = json.loads(response.read().decode("utf-8"))

    raw = data["message"]["content"]
    try:
        parsed = json.loads(raw)
        answer = str(parsed.get("answer", raw)).strip()
        move = str(parsed.get("gesture", "neutral")).lower()
        if move not in ("yes", "no", "neutral"):
            move = "neutral"
        return answer or raw, move
    except (json.JSONDecodeError, AttributeError):
        return raw.strip(), "neutral"


def listen_and_reply():
    global whisper

    try:
        messages.put(("status", "Loading speech model..."))
        if whisper is None:
            whisper = WhisperModel(
                WHISPER_SIZE,
                device="cpu",
                compute_type="int8",
            )

        messages.put(("status", f"Listening for {RECORD_SECONDS} seconds..."))
        subprocess.run(
            [
                "arecord", "-D", MICROPHONE,
                "-d", str(RECORD_SECONDS),
                "-f", "S16_LE",
                "-r", "16000",
                "-c", "1",
                "-t", "wav",
                AUDIO_FILE,
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            timeout=RECORD_SECONDS + 10,
        )

        messages.put(("status", "Recognizing speech..."))
        segments, _ = whisper.transcribe(
            AUDIO_FILE,
            language="ru",
            beam_size=1,
            vad_filter=True,
        )
        question = " ".join(s.text.strip() for s in segments).strip()
        if not question:
            messages.put(("status", "Didn't catch that — press M to retry"))
            return

        messages.put(("question", question))
        messages.put(("status", "Wheatley is thinking..."))
        answer, move = ask_qwen(question)
        messages.put(("answer", answer, move))

        if voice is not None:
            try:
                voice.speak(answer)
            except Exception as error:
                messages.put(("status", f"Voice error: {error}"))

    except Exception as error:
        messages.put(("error", str(error)))
    finally:
        messages.put(("finished",))


def start_listening():
    global busy, status
    if busy:
        return
    busy = True
    status = "Starting microphone..."
    threading.Thread(target=listen_and_reply, daemon=True).start()


def begin_gesture(move):
    global gesture, gesture_start, status, target_x, target_y
    gesture = move
    gesture_start = time.monotonic()
    if move == "yes":
        status = "Wheatley says YES"
    elif move == "no":
        status = "Wheatley says NO"
    else:
        status = "Wheatley answered"


def handle_messages():
    global busy, status, last_answer
    while True:
        try:
            msg = messages.get_nowait()
        except queue.Empty:
            break

        if msg[0] == "status":
            status = msg[1]
        elif msg[0] == "question":
            print(f"You: {msg[1]}")
        elif msg[0] == "answer":
            last_answer = msg[1]
            print(f"Wheatley: {last_answer}")
            begin_gesture(msg[2])
        elif msg[0] == "error":
            status = f"Error: {msg[1]}"[:90]
            print(status)
        elif msg[0] == "finished":
            busy = False
            if status.startswith(("Listening", "Recognizing", "Wheatley is thinking")):
                status = "Ready — press M to speak"


def draw_eye(surface, t):
    global gesture, gaze_x, gaze_y, target_x, target_y, next_blink, blink_until

    w, h = surface.get_size()
    cx, cy = w // 2, h // 2 - 12
    base = min(w, h)
    outer = int(base * 0.34)
    ring = int(base * 0.285)
    black = int(base * 0.235)
    lens = int(base * 0.17)

    # Idle gaze drifts gently. YES and NO override it temporarily.
    elapsed = t - gesture_start
    if gesture == "yes" and elapsed < 1.35:
        target_x = 0.0
        target_y = math.sin(elapsed * math.pi * 3) * 0.24
    elif gesture == "no" and elapsed < 1.35:
        target_x = math.sin(elapsed * math.pi * 3) * 0.42
        target_y = 0.0
    else:
        if gesture in ("yes", "no") and elapsed >= 1.35:
            gesture = "neutral"
        if random.random() < 0.008:
            target_x = random.uniform(-0.25, 0.25)
            target_y = random.uniform(-0.15, 0.15)

    smooth = 0.16
    gaze_x += (target_x - gaze_x) * smooth
    gaze_y += (target_y - gaze_y) * smooth

    if t >= next_blink:
        blink_until = t + 0.16
        next_blink = t + random.uniform(2.5, 5.0)

    pygame.draw.circle(surface, METAL, (cx, cy), outer)
    pygame.draw.circle(surface, DARK_METAL, (cx, cy), int(outer * 0.88))
    pygame.draw.circle(surface, (200, 207, 212), (cx, cy), ring, max(2, base // 150))
    pygame.draw.circle(surface, (12, 15, 20), (cx, cy), black)

    # Three simple bolts and radial marks.
    for i in range(18):
        a = 2 * math.pi * i / 18
        p1 = (int(cx + math.cos(a) * ring * 0.78),
              int(cy + math.sin(a) * ring * 0.78))
        p2 = (int(cx + math.cos(a) * ring * 0.94),
              int(cy + math.sin(a) * ring * 0.94))
        pygame.draw.line(surface, (82, 90, 98), p1, p2, max(1, base // 280))

    for degrees in (30, 150, 270):
        a = math.radians(degrees)
        bx = int(cx + math.cos(a) * ring * 0.78)
        by = int(cy + math.sin(a) * ring * 0.78)
        pygame.draw.circle(surface, (30, 34, 40), (bx, by), max(4, base // 90))
        pygame.draw.circle(surface, (150, 157, 163), (bx, by), max(2, base // 125))

    lx = int(cx + gaze_x * lens * 0.62)
    ly = int(cy + gaze_y * lens * 0.62)
    pygame.draw.circle(surface, DARK_BLUE, (lx, ly), int(lens * 1.08))
    pygame.draw.circle(surface, (20, 90, 175), (lx, ly), lens)
    pygame.draw.circle(surface, BLUE, (lx, ly), int(lens * 0.72))
    pygame.draw.circle(surface, (150, 225, 255), (lx, ly), int(lens * 0.35))
    pygame.draw.circle(surface, WHITE, (lx - int(lens * 0.22),
                                       ly - int(lens * 0.25)),
                       max(2, int(lens * 0.09)))

    if t < blink_until:
        lid_h = int(base * 0.24)
        pygame.draw.rect(surface, BG, (cx - outer, cy - outer, outer * 2, lid_h))
        pygame.draw.rect(surface, BG, (cx - outer, cy + outer - lid_h, outer * 2, lid_h))


def main():
    global status

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Wheatley")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 25)
    small_font = pygame.font.Font(None, 20)
    fullscreen = False
    running = True

    print("Wheatley ready. Press M to ask a question; ESC to quit.")

    while running:
        t = time.monotonic()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_m:
                    start_listening()
                elif event.key == pygame.K_SPACE:
                    global blink_until
                    blink_until = t + 0.16
                elif event.key == pygame.K_F11:
                    fullscreen = not fullscreen
                    screen = pygame.display.set_mode(
                        (0, 0) if fullscreen else (WIDTH, HEIGHT),
                        pygame.FULLSCREEN if fullscreen else pygame.RESIZABLE,
                    )

        handle_messages()
        screen.fill(BG)
        draw_eye(screen, t)

        status_text = small_font.render(status[:95], True, (190, 220, 240))
        screen.blit(status_text, (12, screen.get_height() - 27))

        hint = font.render("M: Speak   SPACE: Blink   ESC: Quit", True, (125, 155, 180))
        screen.blit(hint, (12, 10))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
