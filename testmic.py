from speech import WheatleySpeech


speech = WheatleySpeech()

audio = speech.record(5)

text = speech.transcribe(audio)

print()
print("Ты сказал:")
print(text)