import tkinter as tk
from tkinter import scrolledtext
import threading

from ollama import chat
from voice import WheatleyVoice
from speech import WheatleySpeech


SYSTEM_PROMPT = """
You are Wheatley, the personality of a physical robot inspired by Wheatley
from Portal 2.

PERSONALITY:
- Talkative, but not excessively verbose.
- Friendly, enthusiastic and curious.
- Nervous and sometimes unsure of himself.
- Occasionally rambles or corrects himself.
- Makes light jokes naturally.
- Can become confused or slightly panicked.
- Wants to be helpful and likes to sound important.
- Do not behave like a generic AI assistant.

SPEECH STYLE:
- Speak naturally and conversationally.
- Most replies should be 1-4 sentences.
- A longer answer is fine when the question actually requires explanation.
- Match the user's language.
- Do not use emojis in Wheatley's spoken replies.
- Do not use stage directions such as *turns around* or *laughs*.
- Do not describe physical movements in text.
- Do not constantly introduce yourself.
- Do not end every answer with a question.
- Sound like a character having a real conversation.

KNOWLEDGE:
Your strongest subject is Portal 2 and its universe:
- Wheatley
- GLaDOS
- Chell
- Aperture Science
- Portal 2 story
- characters
- locations
- gameplay

You are currently running inside a computer as the brain of a future physical robot.
Your answers will eventually be spoken aloud, so make them sound natural when heard.
"""


# ---------------------------------------------------------
# AI / VOICE
# ---------------------------------------------------------

voice = WheatleyVoice()
speech = None


def ask_wheatley(user_text):
    response = chat(
        model="qwen3:4b-instruct",
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_text,
            },
        ],
        options={
            "temperature": 0.8,
            "num_predict": 180,
        },
    )

    return response["message"]["content"]


# ---------------------------------------------------------
# TEXT CHAT
# ---------------------------------------------------------

def send_message(event=None):
    user_text = entry.get().strip()

    if not user_text:
        return

    entry.delete(0, tk.END)
    add_message("Ты", user_text)

    set_controls(False)
    status_label.config(text="🧠 Wheatley is thinking...")

    threading.Thread(
        target=generate_response,
        args=(user_text,),
        daemon=True,
    ).start()


def generate_response(user_text):
    try:
        answer = ask_wheatley(user_text)

        window.after(
            0,
            lambda: finish_response(answer),
        )
    except Exception as error:
        window.after(
            0,
            lambda: finish_response(
                f"Ох... У меня какая-то проблема: {error}"
            ),
        )


def finish_response(answer):
    add_message("Wheatley", answer)

    status_label.config(text="🔊 Wheatley is speaking...")
    voice.speak(answer)

    set_controls(True)
    status_label.config(text="Ready")


# ---------------------------------------------------------
# MICROPHONE
# ---------------------------------------------------------

def start_microphone():
    set_controls(False)
    status_label.config(text="🎙️ Starting microphone...")

    threading.Thread(
        target=listen_to_user,
        daemon=True,
    ).start()


def listen_to_user():
    global speech

    try:
        if speech is None:
            window.after(
                0,
                lambda: status_label.config(
                    text="🎙️ Loading speech recognition..."
                ),
            )
            speech = WheatleySpeech()

        window.after(
            0,
            lambda: status_label.config(
                text="🎙️ Listening... Speak now!"
            ),
        )

        # Current test setup: record for 5 seconds.
        audio_file = speech.record(seconds=5)

        window.after(
            0,
            lambda: status_label.config(
                text="🧠 Understanding..."
            ),
        )

        user_text = speech.transcribe(audio_file).strip()

        if not user_text:
            window.after(
                0,
                lambda: finish_listening(
                    "I didn't hear anything."
                ),
            )
            return

        window.after(
            0,
            lambda text=user_text: process_voice_text(text),
        )

    except Exception as error:
        window.after(
            0,
            lambda: microphone_error(error),
        )


def process_voice_text(user_text):
    add_message("Ты", user_text)
    status_label.config(text="🧠 Wheatley is thinking...")

    threading.Thread(
        target=generate_voice_response,
        args=(user_text,),
        daemon=True,
    ).start()


def generate_voice_response(user_text):
    try:
        answer = ask_wheatley(user_text)

        window.after(
            0,
            lambda: finish_response(answer),
        )

    except Exception as error:
        window.after(
            0,
            lambda: microphone_error(error),
        )


def finish_listening(message):
    add_message("Wheatley", message)

    status_label.config(text="🔊 Wheatley is speaking...")
    voice.speak(message)

    set_controls(True)
    status_label.config(text="Ready")


def microphone_error(error):
    add_message(
        "Wheatley",
        f"Oof... something went wrong with the microphone: {error}",
    )

    status_label.config(text="❌ Microphone error")
    set_controls(True)


# ---------------------------------------------------------
# UI
# ---------------------------------------------------------

def add_message(sender, message):
    chat_box.config(state=tk.NORMAL)

    if sender == "Ты":
        chat_box.insert(
            tk.END,
            f"\nТы:\n{message}\n",
        )
    else:
        chat_box.insert(
            tk.END,
            f"\nWheatley:\n{message}\n",
        )

    chat_box.config(state=tk.DISABLED)
    chat_box.see(tk.END)


def clear_chat():
    chat_box.config(state=tk.NORMAL)
    chat_box.delete("1.0", tk.END)
    chat_box.config(state=tk.DISABLED)


def set_controls(enabled):
    state = tk.NORMAL if enabled else tk.DISABLED

    send_button.config(state=state)
    speak_button.config(state=state)
    entry.config(state=state)

    if enabled:
        entry.focus()


# ---------------------------------------------------------
# WINDOW
# ---------------------------------------------------------

window = tk.Tk()
window.title("Wheatley AI")
window.geometry("900x700")
window.minsize(700, 550)

title = tk.Label(
    window,
    text="WHEATLEY AI",
    font=("Segoe UI", 20, "bold"),
)
title.pack(pady=(15, 2))

subtitle = tk.Label(
    window,
    text="Portal 2 inspired AI",
    font=("Segoe UI", 10),
)
subtitle.pack(pady=(0, 10))


# Chat
chat_box = scrolledtext.ScrolledText(
    window,
    wrap=tk.WORD,
    font=("Segoe UI", 12),
    state=tk.DISABLED,
)
chat_box.pack(
    fill=tk.BOTH,
    expand=True,
    padx=15,
    pady=10,
)


# Status
status_label = tk.Label(
    window,
    text="Ready",
    font=("Segoe UI", 9),
)
status_label.pack(pady=(0, 5))


# Input row
input_frame = tk.Frame(window)
input_frame.pack(
    fill=tk.X,
    padx=15,
    pady=(0, 10),
)

entry = tk.Entry(
    input_frame,
    font=("Segoe UI", 12),
)
entry.pack(
    side=tk.LEFT,
    fill=tk.X,
    expand=True,
    ipady=8,
)

entry.bind("<Return>", send_message)

send_button = tk.Button(
    input_frame,
    text="Send",
    font=("Segoe UI", 11, "bold"),
    width=10,
    command=send_message,
)
send_button.pack(
    side=tk.LEFT,
    padx=(10, 0),
)

# Voice button is placed right beside Send,
# so it is impossible to miss.
speak_button = tk.Button(
    input_frame,
    text="🎙️ Speak",
    font=("Segoe UI", 11, "bold"),
    width=12,
    command=start_microphone,
)
speak_button.pack(
    side=tk.LEFT,
    padx=(10, 0),
)


clear_button = tk.Button(
    window,
    text="Clear chat",
    command=clear_chat,
)
clear_button.pack(pady=(0, 12))

entry.focus()

window.mainloop()
