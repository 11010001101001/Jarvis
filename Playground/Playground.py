import time
import requests
import os
import sys
import re

sys.path.append('/Users/yaroslav/Desktop/Jarvis/VoiceAssistant/Body')
from CONFIG import *
from pynput.keyboard import Key, Controller

keyboard = Controller()
