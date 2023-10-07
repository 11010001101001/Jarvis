import time
from itertools import cycle
import datetime
from datetime import datetime
from CONFIG import *
from threading import Thread


class Tracer:
    def __init__(self):
        self.is_loading = None

    def get_greeting(self):
        hour = self.get_current_hour()
        if hour in range(18, 24):
            return f'добрый вечер, {USER_NAME_RUS}'
        elif hour in range(0, 12):
            return f'доброе утро, {USER_NAME_RUS}'
        elif hour in range(12, 18):
            return f'добрый день, {USER_NAME_RUS}'

    def get_current_hour(self):
        return datetime.now().hour

    def clear(self):
        self.log(CLEAR)

    def log_debug(self, msg, flush: bool = None):
        if flush:
            print(f'\r{YELLOW}[{datetime.now().strftime("%H:%M:%S")}]{YELLOW} Debug: {msg}', end='\n',
                  flush=flush)
        else:
            print(f'{YELLOW}[{datetime.now().strftime("%H:%M:%S")}]{YELLOW} Debug: {msg}')

    def log(self, msg, flush: bool = None):
        if flush:
            print(f'\r{WHITE}[{datetime.now().strftime("%H:%M:%S")}]{CYAN} Jarvis: {msg}', end='\n',
                  flush=flush)
        else:
            print(f'{WHITE}[{datetime.now().strftime("%H:%M:%S")}]{CYAN} Jarvis: {msg}')

    def log_loading(self, step):
        print(f'\r{WHITE}[{datetime.now().strftime("%H:%M:%S")}]{CYAN} Jarvis: {step}', end=" ", flush=True)

    def log_user(self, user, msg):
        print(f'{WHITE}[{datetime.now().strftime("%H:%M:%S")}]{MAGENTA} {user}: {msg}')

    def log_error(self, msg, flush: bool = None):
        if flush:
            print(f'\r{WHITE}[{datetime.now().strftime("%H:%M:%S")}]{RED} ошибка: {msg}', end='\n',
                  flush=flush)
        else:
            print(f'{WHITE}[{datetime.now().strftime("%H:%M:%S")}]{RED} ошибка: {msg}')

    def start_loading(self, run=None):
        def show_loader():
            for step in cycle(STEPS):
                if not self.is_loading:
                    break

                if run:
                    self.clear()
                    self.log(f'{step}')
                else:
                    self.log_loading(step)
                time.sleep(0.07)

        if run:
            th = Thread(target=run)
            th.start()

        th = Thread(target=show_loader)
        th.start()
