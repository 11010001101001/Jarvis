import json
import random
import time
import geocoder
import wikipedia
import os
import subprocess
import requests
import re
from Texts import *
from functools import wraps
from googletrans import Translator
from fuzzywuzzy import process
from Tracer import Tracer
from CONFIG import *
from threading import Thread


def wrapper(method):
    @wraps(method)
    def func(self, *method_args, **method_kwargs):
        try:
            self.th = Thread(target=method(self, *method_args, **method_kwargs))
            self.th.start()
        except Exception as e:
            if e:
                self.log_error(e)
                self.sound_manager.speak(error_message)
                pass

    return func


class CommandsHandler(Tracer):
    def __init__(self, sound_manager, gpt_proxy):
        super().__init__()
        self.sound_manager = sound_manager
        self.gpt_proxy = gpt_proxy
        self.translator = Translator()
        self.recognized_str = None
        self.restart = None
        self.commands = None
        self.th = None
        self.await_answer_delay = 0
        self.configure_commands()
        wikipedia.set_lang('ru')

    def configure_commands(self):
        self.commands = {
            'режим работы': self.enable_work_mode,
            'режим отдыха': self.enable_rest_mode,
            'спящий режим': self.enable_sleep_mode,
            'перезагрузка': self.reboot_system,
            'выключение': self.shut_down_system,
            'блокировка': self.block_screen,
            'пока': self.turn_off,
            'запуск мать': self.run_mr_mother,
            'стоп мать': self.stop_mr_mother,
            'айпи адрес': self.get_ip,
            # 'что такое': self.get_definition, gptProxy for now 
            'поиск': self.open_search,
            'погода': self.get_weather,
            'спасибо': self.thank,
            'крипта': self.get_wallets,
            'ожидание': self.wait,
        }

    def start_speechRecognizer(self, stream):
        self.await_answer_delay = 0
        stream.start()
        self.sound_manager.play('answer')

    def restart_wakeWordDetector(self, restart_sound: str = None):
        self.await_answer_delay = 0
        self.restart(restart_sound)

    def thank(self):
        answer = random.choice(welcome_answers)
        self.sound_manager.speak(answer)
        self.restart_wakeWordDetector()

    def get_best_choice(self, current_command):
        if len(current_command) > 0:
            choices = self.commands.keys()
            best_obj = process.extractOne(current_command, choices)
            best = best_obj[0]
            weight = best_obj[1]
            commands = weight > 70
            return best if commands else current_command
        else:
            return current_command

    def handle(self, command, restart, stream):
        self.restart = restart
        res = json.loads(command)
        self.recognized_str = res['text']
        best = self.get_best_choice(self.recognized_str)
        current_command = best if len(best) > 0 else self.recognized_str

        self.await_answer_delay += 1
        if self.await_answer_delay == 4:
            stream.stop()
            self.restart_wakeWordDetector('answer_negative')
        elif len(current_command) > 0:
            stream.stop()
            self.log_user('Yaroslav', self.recognized_str)
            if current_command in self.commands:
                job = self.commands[current_command]
                job()
            else:
                self.gpt_proxy.proceed(self.recognized_str)
            self.start_speechRecognizer(stream)

    @wrapper
    def enable_work_mode(self):
        def update_branches():
            self.log(f'обновляю master и release...')
            os.chdir(f'{WORKING_DIR}')
            for b in ['release', 'master']:
                os.system(f'git checkout {b}')
                os.system('git fetch')
                os.system('git pull')
            os.chdir(f'{ROOT_DIR}')
            self.log(f'готово 🤙🏼')

        work_apps = [
            'Xcode',
            'Simulator',
            'Telegram',
            "Google Chrome",
            "OpenVPN Connect",
            "Mail",
            "Cisco Jabber"
        ]

        for app in work_apps:
            os.system(f'open -a "{app.strip()}"')
            self.log(f'открываю {app.strip()}...')
            time.sleep(1)

        update_branches()
        self.sound_manager.speak('рабочий режим активирован ✅')

    @wrapper
    def enable_rest_mode(self):
        cmd = """osascript -e 'tell application "System Events" to get name of (processes where background only is false)'"""
        opened_apps = os.popen(cmd).read()

        for app in opened_apps.split(sep=', '):
            if 'Terminal' not in app:
                os.system(f'pkill -x "{app.strip()}"')
                self.log(f'закрываю {app.strip()}...')
        self.sound_manager.speak('рабочий отдыха активирован ✅')

    @wrapper
    def open_search(self):
        query = str(self.recognized_str).removeprefix('поиск ')
        count = len(query.split(sep=" "))
        prepared = query.replace(" ", "+")
        final = prepared if count > 1 else query
        self.log(f'ищу: {final}')
        search_request = (f'https://www.google.com/search?q={final}&oq={final}&aqs='
                          f'chrome..69i57j46i433i512j0i433i512j46i433i512l'
                          f'3j46i512j0i433i512j46i512j46i433i512.4476j0j7&sourceid=chrome&ie=UTF-8')
        os.system(f'open -a Safari {search_request}')

    def enable_sleep_mode(self):
        self.sound_manager.speak('включаю режим сна')
        os.system('pmset sleepnow')

    def reboot_system(self):
        self.sound_manager.speak('перезагрузка начнется через минуту')
        subprocess.call(['osascript', '-e', 'tell app "loginwindow" to «event aevtrrst»'])
        self.sound_manager.play('confirmation')
        self.turn_off()

    def shut_down_system(self):
        self.sound_manager.speak('выключение произойдет через минуту')
        subprocess.call(['osascript', '-e', 'tell app "loginwindow" to «event aevtrsdn»'])
        self.stop_mr_mother()
        self.sound_manager.play('confirmation')
        self.turn_off()

    @wrapper
    def block_screen(self):
        self.sound_manager.play('lock')
        os.system('pmset displaysleepnow')

    def turn_off(self):
        self.sound_manager.speak('чаао')
        pid = os.getpid()
        os.system(f'kill {pid}')

    @wrapper
    def get_weather(self):
        my_geo = geocoder.ip('me')
        city = my_geo.geojson['features'][0]['properties']['city']
        address = my_geo.geojson['features'][0]['properties']['address']
        url = f'http://api.weatherstack.com/current?access_key={WEATHER_KEY}\({city})'
        weather_data = requests.get(url).json()
        temp = round(weather_data['current']['temperature'])
        temp_right_ending = self.get_ending(str(temp), 'градус')
        feels_like = str(round(weather_data['current']['feelslike']))
        feels_like_prepared = feels_like.replace('-', 'минус ') if '-' in feels_like else feels_like
        common_en = weather_data['current']['weather_descriptions']
        common_ru = self.translator.translate(common_en[0], 'ru').text.lower()
        self.sound_manager.speak(
            f'📍 {address} \nСейчас {common_ru}, {temp_right_ending}, ощущается как {feels_like_prepared}')

    def get_ending(self, num: str, root: str):
        last = num[-1:]
        twenties = abs(int(num)) in range(10, 21)

        if twenties:
            ending = 'ов'
        else:
            if last == '1':
                ending = ''
            elif last in map(lambda el: str(el), list(range(2, 5))):
                ending = 'а'
            else:
                ending = 'ов'

        return f'{num} {root}{ending}'

    @wrapper
    def run_mr_mother(self):
        os.system('open -a MrMotherlauncher')

    @wrapper
    def get_ip(self):
        ip = os.popen('ipconfig getifaddr en0').read()
        self.log(ip)

    @wrapper
    def stop_mr_mother(self):
        def get_mr_mother_pid():
            with open('/Users/yaroslav/Desktop/MrMother/pid.txt', 'r') as f:
                p = f.read()
                return p

        pid = get_mr_mother_pid()
        os.system(f'kill {pid}')

    @wrapper
    def get_definition(self):
        def search(attemt: int = 0):
            wikipedia.set_lang('ru')
            end = len(self.recognized_str.split()) - 1
            try:
                query = ' '.join(self.recognized_str.split()[attemt + 1:])
                self.log(f'ищу: {query}')
                search_result = wikipedia.summary(query, sentences=5, auto_suggest=False, redirect=True)
                no_spaces = re.sub(' +', ' ', search_result)
                no_new_lines = no_spaces.replace('\n', '')
                self.sound_manager.speak(no_new_lines, False)
            except wikipedia.exceptions.PageError:
                if attemt <= end:
                    search(attemt + 1)
                    pass

        search()

    @wrapper
    def get_wallets(self):
        self.log(CRYPTO)

    @wrapper
    def wait(self):
        self.sound_manager.speak('режим ожидания активирован на 30 минут ✅')
        old_time = time.time()
        ten_min = 600
        twenty_min = ten_min * 2
        thirty_min = ten_min * 3

        while True:
            current_time = time.time()
            dif = round(current_time - old_time)

            if dif == ten_min:
                self.log('в ожидании 10 минут...💤')
            elif dif == twenty_min:
                self.log('в ожидании 20 минут, скоро пробуждение...🌻')
            elif dif == thirty_min:
                self.sound_manager.speak('и я снова тут ✅')
                self.restart_wakeWordDetector()
                break

            time.sleep(1)
