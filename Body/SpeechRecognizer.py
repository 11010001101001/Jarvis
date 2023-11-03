import time
import vosk
import sounddevice as sd
import queue
import pyaudio
from Tracer import Tracer
from vosk import SetLogLevel
from CONFIG import *


class SpeechRecognizer(Tracer):
    def __init__(self, commandsHandler, sound_manager):
        SetLogLevel(-1)
        super().__init__()
        self.model = vosk.Model(VOSK_MODEL_PATH)
        self.sample_rate = 16000
        self.device = sd.default.device[0]
        self.q = queue.Queue()
        self.commandsHandler = commandsHandler
        self.sound_manager = sound_manager

    def callback(self, indata, frames, time, state):
        self.q.put(bytes(indata))
        self.q.task_done()

    def start_recognizing(self, restart):
        self.sound_manager.play('answer')

        rec = vosk.KaldiRecognizer(self.model, self.sample_rate)
        stream = sd.RawInputStream(samplerate=self.sample_rate,
                                   blocksize=8000,
                                   device=self.device,
                                   dtype='int16',
                                   channels=1,
                                   callback=self.callback)

        try:
            with stream:
                while not stream.stopped:
                    data = self.q.get()
                    if rec.AcceptWaveform(data):
                        command = rec.Result()
                        self.commandsHandler.handle(command, restart, stream)
        except KeyboardInterrupt:
            pass
        except BaseException as e:
            flush = self.is_loading
            self.is_loading = False

            self.log_error(f'speechRecognizer exception error: {e}', flush=flush)
            stream.stop()
            self.log('speechRecognizer sleep...')
            time.sleep(COOL_DOWN)
            self.sound_manager.play('repair')
            self.start_recognizing(restart)
            self.log('speechRecognizer restarted ✅')
