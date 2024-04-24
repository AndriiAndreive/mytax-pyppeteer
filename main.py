import asyncio
from pyppeteer import launch
from pyppeteer.errors import TimeoutError
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
import time
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

async def main():
    # Launch the browser
    browser = await launch(executablePath='./chrome-win/chrome.exe', headless=False)
    page = await browser.newPage()
    await page.setViewport({'width': 1920, 'height': 1080})

    try:
        # Navigate to the website
        await page.goto('https://mytax.dc.gov/_/')

        # Wait for the page to load
        await page.waitForSelector('#l_Df-1-15 span.ColIconText')

        # Click the span containing the specified text
        await page.click('#l_Df-1-15 span.ColIconText')
        
        # Input data
        # Input "hello" into the input box with id "Dc-a"
        await page.waitForSelector('#Dc-8')
        time.sleep(1)
        await page.waitForSelector('#Dc-a')
        await page.type('#Dc-a', os.getenv('MYTAX_PASSWORD'))
        await page.type('#Dc-8', os.getenv('MYTAX_USERNAME'))

        # Click the validate button
        await page.click('button#Dc-c')

        # Wait for the search result element to load
        await page.waitForSelector('#caption2_Dc-j')
        
        time.sleep(10)
        # Capture screenshot
        await page.screenshot({'path': 'taxstatus.png'})

        # Send email
        await send_email(os.getenv('RECIPIENT_EMAIL'), 'taxstatus.png') # Replace by the recipient's email instead of os.getenv('RECIPIENT_EMAIL')

    except TimeoutError:
        print('Timeout error occurred.')
    finally:
        await browser.close()

async def send_email(recipient_email, screenshot_path):
    # Set up email content
    msg = MIMEMultipart()
    msg['From'] = os.getenv('SMTP_FROM')
    msg['To'] = recipient_email
    msg['Subject'] = 'Tax Status Screenshot'

    # Attach screenshot
    with open(screenshot_path, 'rb') as fp:
        img = MIMEImage(fp.read())
        msg.attach(img)

    # Attach text message
    text = MIMEText('Screenshot of tax status.')
    msg.attach(text)

    # Send email
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = os.getenv('SMTP_PORT')
    smtp_username = os.getenv('SMTP_USERNAME')
    smtp_password = os.getenv('SMTP_PASSWORD')

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
        print('Email sent successfully.')
    except Exception as e:
        print(f'Error sending email: {e}')

# Run the main function
asyncio.get_event_loop().run_until_complete(main())
