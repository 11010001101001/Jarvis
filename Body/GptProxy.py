import time
import requests
import openai as novaai
from Tracer import Tracer
from googletrans import Translator
import re
from Texts import *
from CONFIG import *


class GptProxy(Tracer):
    def __init__(self, sound_manager):
        super().__init__()
        novaai.api_base = NOVAAI_API_BASE
        self.translator = Translator()
        self.sound_manager = sound_manager
        self.headers = {
            "Authorization": f"Bearer {NOVA_KEY}",
            "Content-type": "application/json"
        }
        self.context_messages = [ROLE]
        self.attempt = 0

    def proceed(self, msg):
        self.is_loading = True
        self.start_loading()

        msg_to_en = self.translator.translate(msg, 'en').text

        if len(self.context_messages) > CONTEXT_LENGTH:
            self.context_messages = self.context_messages[3:]
            if ROLE not in self.context_messages:
                self.context_messages.insert(0, ROLE)

        usr_context_msg = {"role": "user", "content": f"{msg_to_en}"}
        if usr_context_msg not in self.context_messages:
            self.context_messages.append(usr_context_msg)

        payload = {
            "model": "gpt-3.5-turbo",
            "messages": self.context_messages,
            "temperature": 0.7
        }

        try:
            response = requests.post(URL, json=payload, headers=self.headers)
            match response.status_code:
                case 200:
                    self.handle_success(response)
                case _:
                    self.handle_error(response=response, msg=msg)

        except BaseException as e:
            self.handle_error(e=e, msg=msg)

    def handle_error(self, response=None, e=None, msg=None):
        self.is_loading = False
        self.attempt += 1

        if response:
            self.log_error(f'⛔️ status code: {response.status_code}, text: {response.text}', flush=True)
        else:
            self.log_error(f'⛔️ error e: {e}', flush=True)

        if self.attempt <= NUMBER_OF_ATTEMPTS:
            self.log(f'Cool down ❄️...attempt № {self.attempt} of {NUMBER_OF_ATTEMPTS} in {TIMEOUT} seconds')
            time.sleep(TIMEOUT)
            self.proceed(msg)
        else:
            self.attempt = 0
            self.log_error(f'🫠 nope, try again later')
            self.sound_manager.speak(error_message_gpt, False)

    def handle_success(self, response):
        choices = response.json()['choices']
        has_choices = len(choices) > 0

        if has_choices:
            self.attempt = 0

        answer = choices[0]['message']['content']

        assistant_context_msg = {"role": "assistant", "content": f"{answer}"}
        if assistant_context_msg not in self.context_messages:
            self.context_messages.append(assistant_context_msg)

        answer_to_rus = self.translator.translate(answer, 'ru').text

        self.is_loading = False
        self.log(f'{answer_to_rus}', flush=True)

        no_spaces = re.sub(' +', ' ', answer_to_rus)
        no_new_lines = no_spaces.replace('\n', '')
        self.sound_manager.speak(no_new_lines, False)
