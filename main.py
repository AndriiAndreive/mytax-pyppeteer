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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from email_handler import EmailHandler
import traceback
import os
load_dotenv('.env')

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

    driver = webdriver.Chrome(options=chrome_options)

    max_attempts = 3  # Maximum number of attempts to find the link
    attempts = 0
    while attempts < max_attempts:
        try:
            # Try to find and click the initial link
            driver.get('https://mytax.dc.gov/_/')
            time.sleep(4)
            link = driver.find_element(By.CSS_SELECTOR, '#l_Df-1-15 span.ColIconText')
            link.click()
            break
        except NoSuchElementException:
            print(f"Attempt {attempts + 1}: Link not found, retrying...")
            attempts += 1
            # If initial link not found, select another element
            # linkButton = driver.find_element(By.CSS_SELECTOR, 'a.SessionMessageButton')
            # linkButton.click()

    if attempts == max_attempts:
        print("Link not found after maximum attempts.")
    else:
        print("Link found and clicked successfully.")

    time.sleep(1)
    try:
        # Find the textbox by classname
        link = driver.find_element(By.CSS_SELECTOR, '#l_Df-1-15 span.ColIconText')
        link.click()
        print("Clicked a link")

        time.sleep(3)
        # Wait for the first textbox to be visible and enabled
        textbox1 = WebDriverWait(driver, 60).until(EC.visibility_of_element_located((By.ID, 'Dc-a')))
        textbox1.send_keys(account.password)
        print("Put password into textbox")

        # Wait for the second textbox to be visible and enabled
        textbox2 = WebDriverWait(driver, 60).until(EC.visibility_of_element_located((By.ID, 'Dc-8')))
        textbox2.send_keys(account.name)
        print("Put card name into textbox")

        # Wait for the button to be clickable
        button = WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.ID, 'Dc-c')))
        button.click()
        print("Clicked login button")
        time.sleep(1)
        # Scroll down the page using JavaScript
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        print("Scroll down")

        # Wait for the taxstatus element to be visible
        # taxstatus = WebDriverWait(driver, 60).until(EC.visibility_of_element_located((By.ID, 'caption2_Dc-j')))
        driver.save_screenshot(screenshot_path)
        print("Captured the status of tax")

        # # Get the location and size of the element
        # location = taxstatus.location_once_scrolled_into_view
        # size = taxstatus.size

        # # Take a screenshot of the element
        # screenshot = driver.get_screenshot_as_png()

        # # Calculate the coordinates for cropping the screenshot
        # left = location['x']
        # top = location['y']
        # right = location['x'] + size['width']
        # bottom = location['y'] + size['height']

        # image = Image.open(BytesIO(screenshot))
        # element_screenshot = image.crop((left, top, right, bottom))

        # # Save the cropped screenshot to a file
        # element_screenshot.save('element_screenshot.png')

        hasSent = await EmailHandler().send_email(account.email, screenshot_path) 
        if hasSent == True:
            return {"message": "You has been sent the email successfully."}
        else:
            return {"message": "An error occurred while sending email"}
    except:
        traceback.print_exc()
        return {"message": "An error occurred while openning Chrome"}