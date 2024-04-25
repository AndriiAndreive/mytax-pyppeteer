from pyppeteer import launch
from pyppeteer.errors import TimeoutError
import time
from src.payloads.account import Account
from src.controllers import BaseController
from src.helper.email_handler import EmailHandler
import os
import asyncio

class TaxController(BaseController):

    async def main(self, account):
        hasSent = False
        hasTimeout = False
        screenshot_path = 'taxstatus.png'
        # Launch the browser
        browser = await launch(headless=True)
        os.chmod('./chrome-win/chrome.exe', 0o777)
        # browser = await launch(executablePath='./chrome-win/chrome.exe', headless=False)
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
            await page.type('#Dc-a', account.password)
            await page.type('#Dc-8', account.name)

            # Click the validate button
            await page.click('button#Dc-c')

            # Wait for the search result element to load
            await page.waitForSelector('#caption2_Dc-j')
            
            time.sleep(10)
            # Capture screenshot
            await page.screenshot({'path': screenshot_path})

            # Send email
            hasSent = await EmailHandler().send_email(account.email, screenshot_path) 

        except TimeoutError:
            hasTimeout = True
        
        finally:
            await browser.close()
        
        if hasTimeout is True:
            return {"message": "Timeout error occurred."}
        elif hasSent is True:
            return {"message": "You has been sent the email successfully."}        
        else:
            return {"message": "An error occurred while sending screenshot via email."}
        
    async def get_status(self, account: Account):
        # loop = asyncio.get_event_loop()
        # loop.run_until_complete(self.main(account))
        await asyncio.sleep(1)
        await asyncio.get_event_loop().run_until_complete(self.main(account))
        

    