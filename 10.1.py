import requests
import pyttsx3
import json
import os
from vosk import Model, KaldiRecognizer
import sounddevice as sd
import queue
import webbrowser


class DictionaryAssistant:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)
        self.engine.setProperty('volume', 0.9)
        voices = self.engine.getProperty('voices')
        for voice in voices:
            if 'english' in voice.name.lower():
                self.engine.setProperty('voice', voice.id)
                break

        self.current_word = None
        self.current_data = None

        self.setup_voice_recognition()

    def setup_voice_recognition(self):

        if not os.path.exists("model-en"):
            print("English Vosk model not found! Download from https://alphacephei.com/vosk/models")
            return

        self.model = Model("model-en")
        self.samplerate = 16000
        self.device = 1
        self.q = queue.Queue()

    def speak(self, text):
        print(f"Assistant: {text}")
        self.engine.say(text)
        self.engine.runAndWait()

    def find_word(self, word):
        try:
            response = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}")

            if response.status_code == 404:
                self.speak(f"Word {word} not found in dictionary")
                return False

            response.raise_for_status()
            self.current_data = response.json()
            self.current_word = word

            self.speak(f"Found information for word {word}")
            return True

        except Exception as e:
            self.speak("Error fetching word information")
            return False

    def save_info(self):
        if not self.current_data:
            self.speak("First find a word using find command")
            return

        try:
            filename = f"{self.current_word}_dictionary.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Word: {self.current_word}\n")
                f.write("=" * 50 + "\n")

                for entry in self.current_data:
                    if 'meanings' in entry:
                        for meaning in entry['meanings']:
                            f.write(f"\nPart of speech: {meaning['partOfSpeech']}\n")
                            if 'definitions' in meaning:
                                for i, definition in enumerate(meaning['definitions'], 1):
                                    f.write(f"{i}. {definition['definition']}\n")
                                    if 'example' in definition:
                                        f.write(f"   Example: {definition['example']}\n")

            self.speak(f"Information saved to {filename}")

        except Exception as e:
            self.speak("Error saving information")

    def tell_meaning(self):
        if not self.current_data:
            self.speak("First find a word using find command")
            return

        try:
            meanings = []
            for entry in self.current_data:
                if 'meanings' in entry:
                    for meaning in entry['meanings']:
                        if 'definitions' in meaning and meaning['definitions']:
                            meanings.append(meaning['definitions'][0]['definition'])
                            break
                    if meanings:
                        break

            if meanings:
                self.speak(f"Meaning of {self.current_word}: {meanings[0]}")
            else:
                self.speak("No meanings found for this word")

        except Exception as e:
            self.speak("Error getting meaning")

    def open_link(self):
        if not self.current_data:
            self.speak("First find a word using find command")
            return

        try:
            webbrowser.open(f"https://dictionary.cambridge.org/dictionary/english/{self.current_word}")
            self.speak("Opened dictionary link in browser")

        except Exception as e:
            self.speak("Error opening browser")

    def tell_example(self):
        if not self.current_data:
            self.speak("First find a word using find command")
            return

        try:
            examples = []
            for entry in self.current_data:
                if 'meanings' in entry:
                    for meaning in entry['meanings']:
                        if 'definitions' in meaning:
                            for definition in meaning['definitions']:
                                if 'example' in definition:
                                    examples.append(definition['example'])

            if examples:
                self.speak(f"Example: {examples[0]}")
            else:
                self.speak("No examples found for this word")

        except Exception as e:
            self.speak("Error getting example")

    def process_command(self, command):
        command = command.lower()

        if command.startswith('find '):
            word = command[5:].strip()
            if word:
                self.find_word(word)
            else:
                self.speak("Please specify a word after find")

        elif 'save' in command:
            self.save_info()

        elif 'meaning' in command:
            self.tell_meaning()

        elif 'link' in command:
            self.open_link()

        elif 'example' in command:
            self.tell_example()

        elif any(word in command for word in ['exit', 'quit', 'stop', 'goodbye']):
            self.speak("Goodbye!")
            return False

        else:
            self.speak("Command not recognized. Available commands: find, save, meaning, link, example")

        return True

    def listen(self):
        self.speak("English dictionary assistant started. Say your commands")

        with sd.RawInputStream(samplerate=self.samplerate, blocksize=8000, device=self.device,
                               dtype='int16', channels=1, callback=self.audio_callback):
            rec = KaldiRecognizer(self.model, self.samplerate)

            while True:
                data = self.q.get()
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    command = result.get('text', '')

                    if command:
                        print(f"You: {command}")
                        if not self.process_command(command):
                            break

    def audio_callback(self, indata, frames, time, status):
        if status:
            print(status)
        self.q.put(bytes(indata))


if __name__ == "__main__":
    assistant = DictionaryAssistant()
    assistant.listen()