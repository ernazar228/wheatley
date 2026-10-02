import asyncio
import os
import tempfile

import edge_tts
import pygame


class WheatleyVoice:
    def __init__(self):
        pygame.mixer.init()

        # Пока используем естественный мужской английский голос.
        self.voice = "en-GB-RyanNeural"

        self.rate = "+0%"
        self.volume = "+0%"
        self.pitch = "+0Hz"

    def speak(self, text):
        asyncio.run(self._speak(text))

    async def _speak(self, text):
        temp_file = tempfile.NamedTemporaryFile(
            suffix=".mp3",
            delete=False
        )
        temp_file.close()

        try:
            communicate = edge_tts.Communicate(
                text=text,
                voice=self.voice,
                rate=self.rate,
                volume=self.volume,
                pitch=self.pitch
            )

            await communicate.save(temp_file.name)

            pygame.mixer.music.load(temp_file.name)
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(20)

        finally:
            try:
                os.remove(temp_file.name)
            except PermissionError:
                pass