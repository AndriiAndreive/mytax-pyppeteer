import time
import json
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
# from email_handler import EmailHandler
import traceback
import openai
from tenacity import retry, wait_random_exponential, stop_after_attempt
import requests
import csv
import os
load_dotenv('.env')

API_KEY = os.getenv('OPENAI_API_KEY')
openai.api_key = API_KEY
GPT_MODEL = os.getenv('GPT_MODEL')
endpoint = 'https://api.openai.com/v1/chat/completions'

class Account(BaseModel):
    # email: str = Field(..., description="recipient email")
    name: str = Field(..., description="mytax name")
    password: str = Field(..., description="mytax password")

class Question(BaseModel):
    text: str = Field(..., description="the question of the requester")

class CompanyName(BaseModel):
    text: str = Field(..., description="the name of the company")

# Define a class to hold the data
class EXCLUDED_PARTIES_LIST_BY_INDIVIDUAL:
    def __init__(self):
        self.nameOfIndividual = None
        self.principalAddress = None
        self.actionDate = None
        self.expirationDate = None
        self.agencyInstitutingTheAction = None
        self.reasonForTheAction = None

class EXCLUDED_PARTIES_LIST_BY_COMPANY:
    def __init__(self):
        self.nameOfCompany = None
        self.principalAddress = None
        self.actionDate = None
        self.expirationDate = None
        self.agencyInstitutingTheAction = None
        self.reasonForTheAction = None

class PAST_EXCLUDED_PARTIES_LIST_BY_INDIVIDUAL:
    def __init__(self):
        self.nameOfIndividual = None
        self.principalAddress = None
        self.actionDate = None
        self.terminationDate = None

class PAST_EXCLUDED_PARTIES_LIST_BY_COMPANY:
    def __init__(self):
        self.nameOfCompany = None
        self.principalAddress = None
        self.principals = None
        self.actionDate = None
        self.terminationDate = None

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/favicon.ico")
async def get_favicon():
    return {"message": "This is favicon"}

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

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        issuedDateElement = WebDriverWait(driver, 60).until(EC.visibility_of_element_located((By.ID, 'Dc-h')))
        issuedDate = issuedDateElement.get_attribute('value')
        print("Got issued Date: ", issuedDate)

        issuedToElement = WebDriverWait(driver, 60).until(EC.visibility_of_element_located((By.ID, 'Dc-i')))
        issuedTo = issuedToElement.get_attribute('value')
        print("Got issued To: ", issuedTo)

        # compliance taxpayer.
        max_attempts = 3  # Maximum number of attempts to find the taxpayer
        attempts = 0
        taxpayer = ""
        while attempts < max_attempts:
            try:
                time.sleep(1)
                taxpayerElement = driver.find_element(By.XPATH, '//*[@id="caption2_Dc-j"]/span/span/span')
                taxpayer = taxpayerElement.text
                break
            except NoSuchElementException:
                print(f"Attempt {attempts + 1}: Taxpayer not found, retrying...")
                attempts += 1
        
        if attempts == max_attempts:
            print("Taxpayer not found after maximum attempts.")
        else:
            print("Taxpayer found.", taxpayer)

        if taxpayer == "":
            # not in compliance taxpayer
            max_attempts = 3  # Maximum number of attempts to find the taxpayer
            attempts = 0
            while attempts < max_attempts:
                try:
                    time.sleep(1)
                    taxpayerElement = driver.find_element(By.XPATH, '//*[@id="caption2_Dc-k"]/span/span/span')
                    taxpayer = taxpayerElement.text
                    break
                except NoSuchElementException:
                    print(f"Attempt {attempts + 1}: Taxpayer not found, retrying...")
                    attempts += 1
            
            if attempts == max_attempts:
                print("Taxpayer not found after maximum attempts.")
            else:
                print("Taxpayer found.", taxpayer)

        return {
            "NoticeNumber": account.name,
            "Last4digitsOfTaxpayerID": account.password,
            "IssuedDate": issuedDate,
            "IssuedTo": issuedTo,
            "Taxpayer":  taxpayer
        }

        # hasSent = await EmailHandler().send_email(account.email, screenshot_path) 
        # if hasSent == True:
        #     return {"message": "You has been sent the email successfully."}
        # else:
        #     return {"message": "An error occurred while sending email"}
    except:
        traceback.print_exc()
        return {"message": "An error occurred while loading the element"}
    
@app.get("/companies")
async def get_companies():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--remote-debugging-port=9222")

    driver = webdriver.Chrome(options=chrome_options)
    # Create a dictionary with the custom header
    headers = {
        "Origin": "*"
    }

    # Send the custom header using Chrome DevTools Protocol
    driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {'headers': headers})

    driver.get('https://ocp.dc.gov/page/excluded-parties-list')
    time.sleep(3)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    csv_file = 'companies.csv'
    companyNames = []
    excludedPartiesListByIndividual = []
    excludedPartiesListByCompany = []
    pastExcludedPartiesListByIndividual = []
    pastExcludedPartiesListByCompany = []
    try:
        tables = driver.find_elements(By.CSS_SELECTOR, '#section-content table tbody')
        
        rows = tables[0].find_elements(By.TAG_NAME, 'tr')
        for row in rows:
            data = EXCLUDED_PARTIES_LIST_BY_INDIVIDUAL()
            cells = row.find_elements(By.TAG_NAME, 'td')
            data.nameOfIndividual = cells[0].text
            data.principalAddress = cells[1].text
            data.actionDate = cells[2].text
            data.expirationDate = cells[3].text
            data.agencyInstitutingTheAction = cells[4].text
            data.reasonForTheAction = cells[5].text
            excludedPartiesListByIndividual.append(data.__dict__)
            companyNames.append([cells[0].text])

        rows = tables[1].find_elements(By.TAG_NAME, 'tr')
        for row in rows:
            data = EXCLUDED_PARTIES_LIST_BY_COMPANY()
            cells = row.find_elements(By.TAG_NAME, 'td')
            data.nameOfCompany = cells[0].text
            data.principalAddress = cells[1].text
            data.actionDate = cells[2].text
            data.expirationDate = cells[3].text
            data.agencyInstitutingTheAction = cells[4].text
            data.reasonForTheAction = cells[5].text
            excludedPartiesListByCompany.append(data.__dict__)
            companyNames.append([cells[0].text])

        rows = tables[2].find_elements(By.TAG_NAME, 'tr')
        for row in rows:
            data = PAST_EXCLUDED_PARTIES_LIST_BY_INDIVIDUAL()
            cells = row.find_elements(By.TAG_NAME, 'td')
            data.nameOfIndividual = cells[0].text
            data.principalAddress = cells[1].text
            data.actionDate = cells[2].text
            data.terminationDate = cells[3].text
            pastExcludedPartiesListByIndividual.append(data.__dict__)
            companyNames.append([cells[0].text])

        rows = tables[3].find_elements(By.TAG_NAME, 'tr')
        for row in rows:
            data = PAST_EXCLUDED_PARTIES_LIST_BY_COMPANY()
            cells = row.find_elements(By.TAG_NAME, 'td')
            data.nameOfCompany = cells[0].text
            data.principalAddress = cells[1].text
            data.principals = cells[2].text
            data.actionDate = cells[3].text
            data.terminationDate = cells[4].text
            pastExcludedPartiesListByCompany.append(data.__dict__)
            companyNames.append([cells[0].text])
        
        # Write data to the CSV file
        with open(csv_file, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(companyNames)

    except NoSuchElementException:
        return {"message": "Unfortunately, we couldn't find table elements"}

    return [
        {
            "title": "EXCLUDED PARTIES LIST BY INDIVIDUAL",
            "data": excludedPartiesListByIndividual
        },
        {
            "title": "EXCLUDED PARTIES LIST BY COMPANY",
            "data": excludedPartiesListByCompany
        },
        {
            "title": "PAST EXCLUDED PARTIES LIST BY INDIVIDUAL",
            "data": pastExcludedPartiesListByIndividual
        },
        {
            "title": "PAST EXCLUDED PARTIES LIST BY COMPANY",
            "data": pastExcludedPartiesListByCompany
        }
    ]

@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
def chat_completion_request(messages, model=GPT_MODEL):
    json_data = {
        "model": model,
        "messages": messages,
        "temperature": 0
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + API_KEY
    }

    try:
        response = requests.post(endpoint, headers=headers, json=json_data)
        return response
    
    except Exception as e:
        print('Unable to generate ChatCompletion response')
        print(f"Exception {e}")
        return e

@app.post("/generate")
async def generate_answer(question: Question):

    messages = []
    messages.append({'role': 'system', 'content': 'You are a helpful assistant'})
    messages.append({'role': 'user', 'content': question.text})

    response = chat_completion_request(messages, GPT_MODEL)
    
    if 'error' in response.json():
        return response.json()['error']
    else:
        return {
            "data": response.json()['choices'][0]['message']['content']
        }
    
@app.post("/search")
async def is_exist_company(companyName: CompanyName):
    data = []
    # Specify the CSV file to read
    csv_file = 'companies.csv'
    isExist = False

    if os.path.exists(csv_file):
        pass
    else:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--remote-debugging-port=9222")

        driver = webdriver.Chrome(options=chrome_options)
        # Create a dictionary with the custom header
        headers = {
            "Origin": "*"
        }

        # Send the custom header using Chrome DevTools Protocol
        driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {'headers': headers})

        driver.get('https://ocp.dc.gov/page/excluded-parties-list')
        time.sleep(3)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        companyNames = []
        try:
            tables = driver.find_elements(By.CSS_SELECTOR, '#section-content table tbody')
            
            rows = tables[0].find_elements(By.TAG_NAME, 'tr')
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, 'td')
                companyNames.append([cells[0].text])

            rows = tables[1].find_elements(By.TAG_NAME, 'tr')
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, 'td')
                companyNames.append([cells[0].text])

            rows = tables[2].find_elements(By.TAG_NAME, 'tr')
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, 'td')
                companyNames.append([cells[0].text])

            rows = tables[3].find_elements(By.TAG_NAME, 'tr')
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, 'td')
                companyNames.append([cells[0].text])
            
            # Write data to the CSV file
            with open(csv_file, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerows(companyNames)
                file.close()
            
            for element in companyNames:
                if companyName.text.lower() in element:
                    isExist = True
                    data.append(row[0])
                    break

            if isExist:
                return {
                    "message": "Exist",
                    "companies": data
                }
            else:
                return {
                    "message": "Not found"
                }

        except NoSuchElementException:
            return {"message": "Unfortunately, we couldn't create csv file"}

    try:
        # Read data from the CSV file
        with open(csv_file, mode='r') as file:
            reader = csv.reader(file)
            for row in reader:
                if companyName.text.lower() in row[0].lower():
                    isExist = True
                    data.append(row[0])
            file.close()

    except Exception as e:
        return {
            "message": "not found"
        }
    
    if isExist:
        return {
            "message": "Exist",
            "companies": data
        }
    else:
        return {
            "message": "Not found"
        }
