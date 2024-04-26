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
        os.chmod(screenshot_path, 0o777)
        # Set up email content
        msg = MIMEMultipart()
        msg['From'] = self.smtp_from
        msg['To'] = recipient_email
        msg['Subject'] = 'Tax Status Screenshot'
        # Attach screenshot
        with open(screenshot_path, 'rb') as fp:
            img = MIMEImage(fp.read())
            print(img)
            msg.attach(img)

        # Attach text message
        text = MIMEText('Screenshot of tax status.')
        msg.attach(text)
        print('ok')
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            print('ok1')
            server.login(self.smtp_username, self.smtp_password)
            print('ok2')
            server.send_message(msg)
            print('ok3')
            server.quit()
            return True
        
        except Exception as e:
            return False