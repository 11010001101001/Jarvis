import os
from Tracer import Tracer
from CONFIG import *


class ReqInstaller(Tracer):
    def __init__(self):
        super().__init__()

    def check_req_installed(self):
        try:
            with open(f'{BASE_DIR}req_installed.txt', 'r') as f:
                state = f.read()
                f.close()
                return state == 'Req_installed'
        except BaseException as e:
            if e:
                with open(f'{BASE_DIR}req_installed.txt', 'x') as file:
                    file.close()
                    self.check_req_installed()

    def install_requirements(self):
        req_installed = self.check_req_installed()

        if not req_installed:
            try:
                os.system(f'pip install -r {BASE_DIR}requirements.txt')
            finally:
                with open(f'{BASE_DIR}req_installed.txt', 'w+') as f:
                    f.write('Req_installed')
                    f.close()
