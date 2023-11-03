import time
import pvporcupine
from pvrecorder import PvRecorder
from Texts import default_answers
import random
from Tracer import Tracer
from CONFIG import *


class WakeWordDetector(Tracer):
    def __init__(self, sound_manager, speech_recognizer):
        super().__init__()
        self.porcupine = pvporcupine.create(access_key=WAKEWORDDETECTOR_ACCESS_KEY, keywords=['jarvis'])
        self.recoder = PvRecorder(device_index=-1, frame_length=self.porcupine.frame_length)
        self.speech_recognizer = speech_recognizer
        self.sound_manager = sound_manager

    def start_recognition(self, restart_sound: str = None):
        try:
            self.recoder.start()
            self.sound_manager.play(restart_sound if restart_sound else 'answer')

            while self.recoder.is_recording:
                keyword_index = self.porcupine.process(self.recoder.read())
                if keyword_index >= 0:
                    self.recoder.stop()
                    self.log_user(USER_NAME, 'Джарвис!')
                    answer = random.choice(default_answers)
                    self.sound_manager.speak(answer)
                    self.speech_recognizer.start_recognizing(self.start_recognition)
                    break
        except KeyboardInterrupt:
            pass
        except BaseException as e:
            flush = self.is_loading
            self.is_loading = False

            self.log_error(f'wakeWordDetector exception error: {e}', flush=flush)
            self.recoder.stop()
            self.log('wakeWordDetector sleep...')
            time.sleep(COOL_DOWN)
            self.sound_manager.play('repair')
            self.log('wakeWordDetector restarted ✅')
            self.start_recognition()

