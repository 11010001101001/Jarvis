import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from Tracer import Tracer
from CONFIG import *


class GmailManager(Tracer):
    creds = None

    def __init__(self, sound_manager):
        super().__init__()
        self.sound_manager = sound_manager

    def log_in(self):
        global creds
        if os.path.exists(f'{BASE_DIR}token.json'):
            creds = Credentials.from_authorized_user_file(f'{BASE_DIR}token.json', SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    f'{BASE_DIR}credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)

            with open(f'{BASE_DIR}token.json', 'w') as token:
                token.write(creds.to_json())

    def clear(self):
        self.log_in()

        try:
            service = build('gmail', 'v1', credentials=creds)
            results = service.users().messages().list(userId='me',
                                                      labelIds=['INBOX', 'SENT'],
                                                      includeSpamTrash=True).execute()
            messages = results.get('messages', [])

            if not messages:
                self.sound_manager.speak("Пока не нашла входящих сообщений 💁‍♀️")
                return

            msg_ids = list(map(lambda obj: obj['id'], messages))
            service.users().messages().batchDelete(userId="me", body={"ids": msg_ids}).execute()
            self.sound_manager.speak(f'{len(msg_ids)} входящих сообщений, удалила ✅')

        except HttpError as error:
            self.log_error(error)
            self.sound_manager.speak(error_message)
