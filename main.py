import time
import asyncio
from fastapi import FastAPI
from dotenv import load_dotenv
from pydantic import Field, BaseModel
from PIL import Image
from io import BytesIO
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from email_handler import EmailHandler
import traceback
import os
load_dotenv('.env')
os.chmod('./element_screenshot.png', 0o755)
os.chmod('./screenshot.png', 0o755)

class Account(BaseModel):
    email: str = Field(..., description="recipient email")
    name: str = Field(..., description="mytax name")
    password: str = Field(..., description="mytax password")

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/favicon.ico")
async def get_favicorn():
    return {"message": "This is favicorn"}

@app.post("/tax-status")
async def get_status(account: Account):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--remote-debugging-port=9222")
    screenshot_path = 'taxstatus.png'
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get('https://mytax.dc.gov/_/')
        driver.save_screenshot('screenshot.png')

        # Find the textbox by classname
        link = driver.find_element(By.CSS_SELECTOR, '#l_Df-1-15 span.ColIconText')
        link.click()

        time.sleep(3)
        # Input text "Cloudth" into the textbox

        textbox1 = driver.find_element(By.ID, '#Dc-a')
        textbox1.send_keys(account.password)

        textbox2 = driver.find_element(By.ID, '#Dc-8')
        textbox2.send_keys(account.name)


        button = driver.find_element(By.ID, '#Dc-c')
        button.click()

        time.sleep(5)

        # Find the taxstatus by ID
        taxstatus = driver.find_element(By.ID, '#caption2_Dc-j')
        time.sleep(10)

        # Scroll down the page using JavaScript
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        driver.save_screenshot(screenshot_path)

        # Get the location and size of the element
        location = taxstatus.location_once_scrolled_into_view
        size = taxstatus.size

        # Take a screenshot of the element
        screenshot = driver.get_screenshot_as_png()

        # Calculate the coordinates for cropping the screenshot
        left = location['x']
        top = location['y']
        right = location['x'] + size['width']
        bottom = location['y'] + size['height']

        image = Image.open(BytesIO(screenshot))
        element_screenshot = image.crop((left, top, right, bottom))

        # Save the cropped screenshot to a file
        element_screenshot.save('element_screenshot.png')

        hasSent = await EmailHandler().send_email(account.email, 'element_screenshot.png') 
        if hasSent == True:
            return {"message": "You has been sent the email successfully."}
        else:
            return {"message": "An error occurred while sending email"}
    except:
        traceback.print_exc()
        return {"message": "An error occurred while openning Chrome"}