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
    driver.get('https://mytax.dc.gov/_/')

    try:
        linkButton = driver.find_element(By.CSS_SELECTOR, 'a.SessionMessageButton')
        linkButton.click()
        time.sleep(3)
    except NoSuchElementException:
        print('Session has not expired yet')

    max_attempts = 3  # Maximum number of attempts to find the link
    attempts = 0
    while attempts < max_attempts:
        try:
            # Try to find and click the initial link
            time.sleep(2)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            link = driver.find_element(By.CSS_SELECTOR, '#l_Df-1-15 span.ColIconText')
            link.click()
            break
        except NoSuchElementException:
            print(f"Attempt {attempts + 1}: Link not found, retrying...")
            attempts += 1

    if attempts == max_attempts:
        print("Link not found after maximum attempts.")
    else:
        print("Link found and clicked successfully.")

    time.sleep(5)

    try:

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

        driver.save_screenshot(screenshot_path)
        print("Captured the status of tax")

        time.sleep(6)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        issuedDateElement = WebDriverWait(driver, 60).until(EC.visibility_of_element_located((By.ID, 'Dc-h')))
        issuedDate = issuedDateElement.get_attribute('value')
        print("Got issued Date: ", issuedDate)

        issuedToElement = WebDriverWait(driver, 60).until(EC.visibility_of_element_located((By.ID, 'Dc-i')))
        issuedTo = issuedToElement.get_attribute('value')
        print("Got issued To: ", issuedTo)

        max_attempts = 3  # Maximum number of attempts to find the taxpayer
        attempts = 0
        taxpayer = ""
        while attempts < max_attempts:
            try:
                time.sleep(2)
                taxpayerElement = driver.find_element(By.XPATH, '//*[@id="caption2_Dc-j"]/span/span/span')
                taxpayer = taxpayerElement.text
                break
            except NoSuchElementException:
                print(f"Attempt {attempts + 1}: Taxpayer not found, retrying...")
                attempts += 1

        if attempts == max_attempts:
            print("Taxpayer not found after maximum attempts.")
        else:
            print("Taxpayer found.")

        return {
            "NoticeNumber": account.name,
            "Last4digitsOfTaxpayerID": account.password,
            "issuedDate": issuedDate,
            "IssuedTo": issuedTo,
            "taxpayer":  taxpayer
        }

        # hasSent = await EmailHandler().send_email(account.email, screenshot_path) 
        # if hasSent == True:
        #     return {"message": "You has been sent the email successfully."}
        # else:
        #     return {"message": "An error occurred while sending email"}
    except:
        traceback.print_exc()
        return {"message": "An error occurred while loading the element"}