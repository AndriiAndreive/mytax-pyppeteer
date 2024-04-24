import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
from dotenv import load_dotenv

class EmailHandler:

    def __init__(self):
        load_dotenv()
        self.smtp_from = os.getenv('SMTP_FROM')
        self.smtp_server = os.getenv('SMTP_SERVER')
        self.smtp_port = os.getenv('SMTP_PORT')
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')

    async def send_email(self, recipient_email, screenshot_path):
        # Set up email content
        msg = MIMEMultipart()
        msg['From'] = self.smtp_from
        msg['To'] = recipient_email
        msg['Subject'] = 'Tax Status Screenshot'

        # Attach screenshot
        with open(screenshot_path, 'rb') as fp:
            img = MIMEImage(fp.read())
            msg.attach(img)

        # Attach text message
        text = MIMEText('Screenshot of tax status.')
        msg.attach(text)

        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)
            server.quit()
            return True
        
        except Exception as e:
            return False