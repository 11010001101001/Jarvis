import time
from WakeWordDetector import WakeWordDetector
from CommandsHandler import CommandsHandler
from SpeechRecognizer import SpeechRecognizer
from SoundManager import SoundManager
from GptProxy import GptProxy
from ReqInstaller import ReqInstaller
from Tracer import Tracer
from CONFIG import *


class Assembly(ReqInstaller, Tracer):
    def __init__(self):
        super().__init__()

    def build(self):
        sound_manager = SoundManager()
        gpt_proxy = GptProxy(sound_manager)
        commands_handler = CommandsHandler(sound_manager, gpt_proxy)
        speech_recognizer = SpeechRecognizer(commands_handler, sound_manager)
        wake_word_detector = WakeWordDetector(sound_manager, speech_recognizer)
        commands_handler.wake_word_detector = wake_word_detector
        wake_word_detector.commands_handler = commands_handler

        def run():
            self.is_loading = True
            self.install_requirements()
            sound_manager.play('start')
            greeting = self.get_greeting()
            sound_manager.speak(greeting, False)
            self.clear()
            self.log(greeting)
            self.is_loading = False
            wake_word_detector.start_recognition()

        self.start_loading(run)
