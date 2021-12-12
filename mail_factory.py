import os
import smtplib
import ssl

from dotenv import load_dotenv

load_dotenv()


class SMTPEmail:
    SENDER_USERNAME = os.getenv('SENDER_USERNAME')
    SENDER_EMAIL = os.getenv('SENDER_EMAIL')
    SENDER_PASS = os.getenv('SENDER_PASS')
    SUBJECT = 'Probably nothing...'
    PORT = 465

    def __init__(self, receivers):
        self.receivers = receivers

    def send_email(self, msg):
        context = ssl.create_default_context()
        mail_msg = 'Subject: {}\n\n{}'.format(self.SUBJECT, msg)
        for receiver in self.receivers:
            with smtplib.SMTP_SSL("smtp.gmail.com", self.PORT, context=context) as server:
                server.login(self.SENDER_USERNAME, self.SENDER_PASS)
                server.sendmail(self.SENDER_EMAIL, receiver, mail_msg)