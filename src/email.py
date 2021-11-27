import logging
import google.auth

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email
from python_http_client.exceptions import HTTPError

from google.cloud import secretmanager

secrets = secretmanager.SecretManagerServiceClient()
_, project_id = google.auth.default()

sendgrid_api_key = secrets.access_secret_version(request={"name": "projects/" + project_id + "/secrets/sendgrid-api-key/versions/1"}).payload.data.decode("utf-8")
from_email = secrets.access_secret_version(request={"name": "projects/" + project_id + "/secrets/from-email/versions/1"}).payload.data.decode("utf-8")
to_email = secrets.access_secret_version(request={"name": "projects/" + project_id + "/secrets/to-email/versions/1"}).payload.data.decode("utf-8")


class EmailSender:

    def __init__(self, dataframe):
        self.dataframe = dataframe
        self.scopes = ['https://www.googleapis.com/auth/gmail.readonly']
        self.api_client = self.authenticate()
        self.send_email()

    def send_email(self):
        logging.info(f"Sending email")

        try:
            message = self.create_email_text("Testing", "<p>Hello, World!</p>")
            response = self.api_client.send(message)
            return f"email.status_code={response.status_code}"

        except HTTPError as error:
            logging.error(f"Error whilst trying to send email: {error}")

    def create_email_text(self, subject, message_text):
        logging.info(f"Creating email with data items of length: {len(self.dataframe)}")

        return Mail(
            to_emails=to_email,
            from_email=Email(from_email, "Christopher Philp"),
            subject=subject,
            html_content=message_text
        )

    @staticmethod
    def authenticate():
        logging.info(f"Authenticating user")
        return SendGridAPIClient(sendgrid_api_key)
