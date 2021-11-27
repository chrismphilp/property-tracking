import base64
import logging
import os
from email.mime.text import MIMEText

import google.auth

from google.cloud import secretmanager
from googleapiclient import errors
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

secrets = secretmanager.SecretManagerServiceClient()
_, project_id = google.auth.default()

GMAIL_ACCESS_JSON = secrets.access_secret_version(request={"name": "projects/" + project_id + "/secrets/gmail-token/versions/1"}).payload.data.decode("utf-8")
SENDER_EMAIL = secrets.access_secret_version(request={"name": "projects/" + project_id + "/secrets/sender-email/versions/1"}).payload.data.decode("utf-8")
TO_EMAIL = secrets.access_secret_version(request={"name": "projects/" + project_id + "/secrets/to-email/versions/1"}).payload.data.decode("utf-8")


class GMail:

    def __init__(self, dataframe):
        self.dataframe = dataframe
        self.scopes = ['https://www.googleapis.com/auth/gmail.readonly']
        self.service = self.authenticate()
        self.send_email("me")

    def send_email(self, user_id):
        logging.info(f"Sending email")

        try:
            email_body = self.create_email_text("Test Email", "Hello, World!")
            return self.service.users().messages().send(userId=user_id, body=email_body).execute()
        except errors.HttpError as error:
            logging.error(f"Error whilst trying to send email: {error}")

    def create_email_text(self, subject, message_text):
        logging.info(f"Creating email with data items of length: {len(self.dataframe)}")

        message = MIMEText(message_text)
        message['to'] = TO_EMAIL
        message['from'] = SENDER_EMAIL
        message['subject'] = subject

        return {'raw': base64.urlsafe_b64encode(message.as_bytes())}

    def authenticate(self):
        logging.info(f"Authenticating user")
        credentials = Credentials.from_authorized_user_file(GMAIL_ACCESS_JSON, self.scopes)
        return build('gmail', 'v1', credentials=credentials)
