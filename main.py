import os
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

load_dotenv('.env')

class Account(BaseModel):
    email: str = Field(..., description="recipient email")
    name: str = Field(..., description="mytax name")
    password: str = Field(..., description="mytax password")

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/favicorn.ico")
async def get_favicorn():
    return {"message": "This is favicorn"}

@app.post("/tax-status")
async def get_status(account: Account):
    print(account.email)
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://sandbox.oxylabs.io/products')
    driver.save_screenshot('screenshot.png')

    # Find the textbox by classname
    textbox = driver.find_element(By.CLASS_NAME, 'egbpcqk1')

    # Input text "Cloudth" into the textbox
    textbox.send_keys("Tetris Effect: Connected")


    # Find the image by classname
    image = driver.find_element(By.CLASS_NAME, 'egbpcqk0')

    # Click on the image
    image.click()

    time.sleep(3)

    # Scroll down the page using JavaScript
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    driver.save_screenshot('screenshot.png')

    # Find the element you want to capture (replace 'element_id' with the actual ID, class name, XPath, etc.)
    element = driver.find_element(By.CLASS_NAME, 'e1kord973')

    # Get the location and size of the element
    location = element.location_once_scrolled_into_view
    size = element.size

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