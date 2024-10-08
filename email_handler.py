import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
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
            msg.attach(img)

        # Attach text message
        text = MIMEText('Screenshot of tax status.')
        msg.attach(text)
        print('Image data is:')
        print(msg)
        print('Created a message template')

        try:
            print('Connecting...')
            print(self.smtp_server, self.smtp_port)
            print('Connecting...')
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            print('Connected...')
            print(self.smtp_username, self.smtp_password)
            print('Enable TLS encryption')
            server.starttls()  # Enable TLS encryption
            print('Logining...')
            server.login(self.smtp_username, self.smtp_password)
            print('Logged in smtp server.')
            server.send_message(msg)
            print('Message sent!')
            print('Closing smtp server client...')
            server.quit()
            print('Closed!')
            return True
        
        except Exception as e:
            return False
        
    async def send_email_with_pdf(self, recipient_email: str, pdf_path: str, document_name: str, title: str):
        os.chmod(pdf_path, 0o777)
        # Set up email content
        msg = MIMEMultipart()
        msg['From'] = self.smtp_from
        msg['To'] = recipient_email
        msg['Subject'] = document_name
        # Attach pdf
        with open(pdf_path, 'rb') as f:
            pdf = MIMEApplication(f.read(), _subtype='pdf')
            pdf.add_header('Content-Disposition', 'attachment', filename='result.pdf')
            msg.attach(pdf)

        # Attach text message
        text = MIMEText(title)
        msg.attach(text)

        try:
            print('Connecting...')
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            print('Connected...')
            # server.starttls()  # Enable TLS encryption
            print('Logining...')
            server.login(self.smtp_username, self.smtp_password)
            print('Logged in')
            print('Sending')
            server.send_message(msg)
            print('Sent an email')
            server.quit()

            if os.path.exists(pdf_path):
                os.remove(pdf_path)
            else:
                print("The file does not exist")

            return True
        
        except Exception as e:
            return False