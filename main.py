import tkinter as tk
from tkinter import scrolledtext
import threading
from voice import WheatleyVoice

from ollama import chat


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
- A longer answer is okay when the question actually requires explanation.
- Match the user's language.
- Do not use emojis.
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

You are currently running inside a computer as the brain
of a future physical robot.
"""
voice = WheatleyVoice()

def ask_wheatley(user_text):
    response = chat(
        model="qwen3:4b-instruct",
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": user_text
            }
        ],
        options={
            "temperature": 0.8,
            "num_predict": 180
        }
    )

    return response["message"]["content"]


def send_message(event=None):
    user_text = entry.get().strip()

    if not user_text:
        return

    entry.delete(0, tk.END)

    add_message("Ты", user_text)

    send_button.config(state=tk.DISABLED)
    entry.config(state=tk.DISABLED)

    thread = threading.Thread(
        target=generate_response,
        args=(user_text,),
        daemon=True
    )
    thread.start()


def generate_response(user_text):
    try:
        answer = ask_wheatley(user_text)

        window.after(
            0,
            lambda: finish_response(answer)
        )

    except Exception as e:
        window.after(
            0,
            lambda: finish_response(
                f"Ох... у меня какая-то проблема: {e}"
            )
        )


def finish_response(answer):
    add_message("Wheatley", answer)

    voice.speak(answer)

    send_button.config(state=tk.NORMAL)
    entry.config(state=tk.NORMAL)
    entry.focus()

def add_message(sender, message):
    chat_box.config(state=tk.NORMAL)

    if sender == "Ты":
        chat_box.insert(tk.END, f"\nТы:\n{message}\n")
    else:
        chat_box.insert(tk.END, f"\nWheatley:\n{message}\n")

    chat_box.config(state=tk.DISABLED)
    chat_box.see(tk.END)


def clear_chat():
    chat_box.config(state=tk.NORMAL)
    chat_box.delete("1.0", tk.END)
    chat_box.config(state=tk.DISABLED)


# -----------------------------
# WINDOW
# -----------------------------

window = tk.Tk()

window.title("Wheatley AI")
window.geometry("900x650")
window.minsize(700, 500)

# Header
title = tk.Label(
    window,
    text="WHEATLEY AI",
    font=("Segoe UI", 20, "bold")
)

title.pack(pady=(15, 5))

subtitle = tk.Label(
    window,
    text="Portal 2 inspired AI",
    font=("Segoe UI", 10)
)

subtitle.pack(pady=(0, 10))

# Chat
chat_box = scrolledtext.ScrolledText(
    window,
    wrap=tk.WORD,
    font=("Segoe UI", 12),
    state=tk.DISABLED
)

chat_box.pack(
    fill=tk.BOTH,
    expand=True,
    padx=15,
    pady=10
)

# Input frame
input_frame = tk.Frame(window)

input_frame.pack(
    fill=tk.X,
    padx=15,
    pady=(0, 15)
)

entry = tk.Entry(
    input_frame,
    font=("Segoe UI", 12)
)

entry.pack(
    side=tk.LEFT,
    fill=tk.X,
    expand=True,
    ipady=8
)

entry.bind("<Return>", send_message)

send_button = tk.Button(
    input_frame,
    text="Send",
    font=("Segoe UI", 11, "bold"),
    command=send_message,
    width=10
)

send_button.pack(
    side=tk.LEFT,
    padx=(10, 0)
)

clear_button = tk.Button(
    window,
    text="Clear chat",
    command=clear_chat
)

clear_button.pack(pady=(0, 10))

entry.focus()

window.mainloop()