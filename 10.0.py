import requests
import pyttsx3
import json
import os
from vosk import Model, KaldiRecognizer
import sounddevice as sd
import queue
import wave
import pygame
import io
from PIL import Image


class DogAssistant:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)
        self.engine.setProperty('volume', 0.9)

        self.current_image_url = None
        self.current_image_data = None
        self.current_breed = None

        self.setup_voice_recognition()

    def setup_voice_recognition(self):
        if not os.path.exists("model"):
            print("Модель Vosk не найдена! Скачайте с https://alphacephei.com/vosk/models")
            return

        self.model = Model("model")
        self.samplerate = 16000
        self.device = 1
        self.q = queue.Queue()

    def speak(self, text):
        print(f"Ассистент: {text}")
        self.engine.say(text)
        self.engine.runAndWait()

    def get_dog_image(self):
        try:
            response = requests.get("https://dog.ceo/api/breeds/image/random")
            response.raise_for_status()
            data = response.json()

            self.current_image_url = data['message']
            self.current_breed = self.extract_breed_from_url(self.current_image_url)

            image_response = requests.get(self.current_image_url)
            image_response.raise_for_status()
            self.current_image_data = image_response.content

            return True
        except Exception as e:
            self.speak("Ошибка при загрузке изображения собаки")
            return False

    def extract_breed_from_url(self, url):
        parts = url.split('/')
        breed = parts[-2]
        return breed.replace('-', ' ').title()

    def show_image(self):
        if not self.current_image_data:
            if not self.get_dog_image():
                return

        try:
            image = Image.open(io.BytesIO(self.current_image_data))
            image.show()
            self.speak("Вот изображение собаки")
        except Exception as e:
            self.speak("Не удалось показать изображение")

    def save_image(self):
        if not self.current_image_data:
            self.speak("Сначала загрузите изображение командой показать")
            return

        try:
            breed = self.current_breed.replace(' ', '_')
            filename = f"{breed}_dog.jpg"

            with open(filename, 'wb') as f:
                f.write(self.current_image_data)

            self.speak(f"Изображение сохранено как {filename}")
        except Exception as e:
            self.speak("Ошибка при сохранении изображения")

    def next_image(self):
        if self.get_dog_image():
            self.speak("Загружено новое изображение собаки")

    def tell_breed(self):
        if not self.current_breed:
            self.speak("Сначала загрузите изображение командой показать")
            return

        self.speak(f"Порода собаки: {self.current_breed}")

    def tell_resolution(self):
        if not self.current_image_data:
            self.speak("Сначала загрузите изображение командой показать")
            return

        try:
            image = Image.open(io.BytesIO(self.current_image_data))
            width, height = image.size
            self.speak(f"Разрешение изображения: {width} на {height} пикселей")
        except Exception as e:
            self.speak("Не удалось определить разрешение")

    def process_command(self, command):
        command = command.lower()

        if any(word in command for word in ['показать', 'show', 'открой', 'открыть']):
            self.show_image()

        elif any(word in command for word in ['сохранить', 'save', 'скачать']):
            self.save_image()

        elif any(word in command for word in ['следующ', 'next', 'друг', 'новы']):
            self.next_image()

        elif any(word in command for word in ['порода', 'breed', 'назван']):
            self.tell_breed()

        elif any(word in command for word in ['разрешен', 'resolution', 'пиксел', 'размер']):
            self.tell_resolution()

        elif any(word in command for word in ['выход', 'exit', 'стоп', 'stop']):
            self.speak("До свидания!")
            return False

        else:
            self.speak("Не распознал команду. Попробуйте еще раз")

        return True

    def listen(self):
        self.speak("Голосовой ассистент запущен. Скажите команду")

        with sd.RawInputStream(samplerate=self.samplerate, blocksize=8000, device=self.device,
                               dtype='int16', channels=1, callback=self.audio_callback):
            rec = KaldiRecognizer(self.model, self.samplerate)

            while True:
                data = self.q.get()
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    command = result.get('text', '')

                    if command:
                        print(f"Вы: {command}")
                        if not self.process_command(command):
                            break

    def audio_callback(self, indata, frames, time, status):
        if status:
            print(status)
        self.q.put(bytes(indata))


if __name__ == "__main__":
    assistant = DogAssistant()
    assistant.listen()