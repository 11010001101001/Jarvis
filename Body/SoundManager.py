import sounddevice as sd
import torch
from playsound import playsound
import os
import random
from Tracer import Tracer
from googletrans import Translator
import inflect
from threading import Thread
from CONFIG import *


class SoundManager(Tracer):
    def __init__(self):
        super().__init__()
        language = 'ru'
        model_id = 'v4_ru'
        device = torch.device('cpu')
        self.speaker = 'xenia'
        self.sample_rate = 48000
        self.model, _ = torch.hub.load(repo_or_dir='snakers4/silero-models',
                                       model='silero_tts',
                                       language=language,
                                       speaker=model_id)
        self.model.to(device)
        self.audio = None
        self.inflect = inflect.engine()
        self.translator = Translator()
        self.thread = None
        self.need_log = None

    def numbers_to_str(self, string):
        def change(arg):
            res_en = self.inflect.number_to_words(arg)
            res_ru = self.translator.translate(res_en, 'ru').text
            return res_ru

        arr = string.split()
        strings = []
        for i in arr:
            res = change(i) if i.isnumeric() else i
            strings += ' ' + res
        return ''.join(strings)

    def cut(self, text):
        msg = text
        while len(msg) != 0:
            try:
                first_10 = msg[:MAX_SYMBOLS_COUNT]
                self.proceed(first_10, self.need_log)
                msg = msg[MAX_SYMBOLS_COUNT:]
            except BaseException as e:
                self.log_error(e)
                self.cut(msg)
                break

    def speak(self, text, need_log: bool = True):
        self.need_log = need_log
        self.thread = Thread(
            target=self.cut(text) if len(text) > MAX_SYMBOLS_COUNT else self.proceed(text, need_log))
        self.thread.start()

    def proceed(self, text, need_log: bool = True):
        if need_log:
            self.log(text)
        with_numbers_to_str_text = self.numbers_to_str(text)
        self.audio = self.model.apply_tts(text=with_numbers_to_str_text,
                                          speaker=self.speaker,
                                          sample_rate=self.sample_rate,
                                          put_accent=True,
                                          put_yo=True)
        sd.play(self.audio, self.sample_rate)
        sd.wait()
        sd.stop()

    def play(self, arg):
        def play_action():
            try:
                path = f'{SOUNDS_PATH}/{arg}'
                sounds = filter(lambda el: el != '.DS_Store', os.listdir(path))
                random_sound = random.choice(list(sounds))
                playsound(f'{path}/{random_sound}')
            except BaseException as e:
                self.log_error(e)

        self.thread = Thread(target=play_action)
        self.thread.start()
