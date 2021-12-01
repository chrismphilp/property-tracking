import logging
import google.auth

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email
from python_http_client.exceptions import HTTPError

from google.cloud import secretmanager

secrets = secretmanager.SecretManagerServiceClient()
_, project_id = google.auth.default()

sendgrid_api_key = secrets.access_secret_version(request={"name": f"projects/{project_id}/secrets/sendgrid-api-key/versions/latest"}).payload.data.decode("utf-8")
from_email = secrets.access_secret_version(request={"name": f"projects/{project_id}/secrets/from-email/versions/latest"}).payload.data.decode("utf-8")
to_email = secrets.access_secret_version(request={"name": f"projects/{project_id}/secrets/to-email/versions/latest"}).payload.data.decode("utf-8")


class EmailSender:

    def __init__(self, dataframe):
        self.dataframe = dataframe
        self.api_client = self.authenticate()
        self.send_email()

    def send_email(self):
        logging.info(f"Processing email with {len(self.dataframe)} items")

        if len(self.dataframe) > 0:
            try:
                date = self.dataframe.iloc[0]["added_on"]
                message = self.generate_mail(f"Properties for {date}", self.create_email_text())
                response = self.api_client.send(message)
                return f"email.status_code={response.status_code}"

            except HTTPError as error:
                logging.error(f"HTTPError trying to send email: {error}")

    def create_email_text(self):
        email_message_start = "<table border='1' style='text-align: left; width:100%'>" \
                              "<tr>" \
                              "<th>Address</th>" \
                              "<th>Link</th>" \
                              "</tr>"
        content = ""
        for index, row in self.dataframe.iterrows():
            content += "<tr>" \
                       f"<td>{row['address']}</td>" \
                       f"<td><a href='{row['url']}'>{row['url']}</a></td>" \
                       "</tr>"

        email_message_end = "</table>"

        return email_message_start + content + email_message_end

    def generate_mail(self, subject, message_text):
        logging.info(f"Creating email with data items of length: {len(self.dataframe)}")

        return Mail(
            to_emails=self.generate_recipients(),
            from_email=Email(from_email, "Christopher Philp"),
            subject=subject,
            html_content=message_text
        )

    @staticmethod
    def generate_recipients():
        recipients = []
        for email in str(to_email).split(","):
            recipients.append(Email(email))
        return recipients

    @staticmethod
    def authenticate():
        logging.info(f"Authenticating user")
        return SendGridAPIClient(sendgrid_api_key)
