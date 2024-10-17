import os
import csv
import time
import openai
import requests
import datetime
import traceback
from PIL import Image
from io import BytesIO
from xhtml2pdf import pisa
from bs4 import BeautifulSoup
from pydantic import Field, BaseModel
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from tenacity import retry, wait_random_exponential, stop_after_attempt
from email_handler import EmailHandler
from fastapi import FastAPI
from dotenv import load_dotenv
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

class TaxAccount(BaseModel):
    recipient_email: str = Field(..., description="recipient email")
    notice_number: str = Field(..., description="notice number")
    tax_payer_id: str = Field(..., description="4 digit tax payer id")

class Recipient(BaseModel):
    email: str = Field(..., description="recipient email")

class SamGovAccount(BaseModel):
    email: str = Field(..., description="user email")
    password: str = Field(..., description="user password")
    backup_code: str = Field(..., description="backup code")

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

def get_excluded_parties_content(title: str, header: str, main_content: str) -> str:
    """
    Function to generate HTML content from given parameters.
    """
    current_date = datetime.datetime.now().strftime("%m/%d/%Y %I:%M %p")
    url = 'https://ocp.dc.gov/page/excluded-parties-list'
    space1 = ""
    # Loop 100 times and append '&nbsp;' to the string
    for _ in range(174):
        space1 += "&nbsp;"

    space2 = ""
    # Loop 100 times and append '&nbsp;' to the string
    for _ in range(156):
        space2 += "&nbsp;"

    html_content = f"""
    <html>
    <head>
        <style>
            @page {{
                size: a4 portrait;
                @frame header_frame {{ /* Static Frame */
                    -pdf-frame-content: header_content;
                    left: 30pt; width: 532pt; top: 16pt; height: 40pt;
                }}
                @frame content_frame {{ /* Content Frame */
                    left: 30pt; width: 532pt; top: 50pt; height: 760pt;
                }}
                @frame footer_frame {{ /* Another static Frame */
                    -pdf-frame-content: footer_content;
                    left: 30pt; width: 532pt; top: 810pt; height: 20pt;
                }}
            }}
            table {{
                width: 100%;
            }}
            td {{
                padding: 4pt;
            }}
            th {{
                font-size: 4pt;
            }}
            h1 {{
                font-size: 20pt;
                text-align: center;
            }}
            h3 {{
                font-size: 14pt;
                text-align: left;
            }}
            #footer_content {{
                display: flex;
                justify-content: space-between; /* Aligns items to left and right */
                width: 500pt;
            }}
            thead td p {{
                font-size: 10pt;
            }}
            .views-row {{
                display: flex;
                justify-content: center;
            }}
        </style>
    </head>

    <body>
        <!-- Content for Static Frame 'header_frame' -->
        <div id="header_content">
            {current_date} 
            <span class="space">{space1}<span> 
            {header} | ocp
        </div>

        <!-- Content for Static Frame 'footer_frame' -->
        <div id="footer_content">
            <b>{url}</b>
            <span class="space">{space2}<span>
            <b>Page <pdf:pagenumber> of <pdf:pagecount></b>
        </div>

        <!-- HTML Content -->
        <div id="content_frame">
            <img src="./assets/dcgov_logo.jpg" width="100" />
            <h1>{title}</h1>
            <div>{main_content}</div>
            <h1><img src="./assets/BOW14_Winner.png" width="100" />&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<img src="./assets/BOW14_Winner.png" width="100" /></h1>
        </div>
    </body>
    </html>
    """
    return html_content

def create_pdf_from_html(title: str, header: str, main_content: str, pdf_file_path: str):
    # HTML content as a string
    html_content = get_excluded_parties_content(title, header, main_content)
    
    # File path to save the PDF
    generate_pdf(html_content, pdf_file_path)

def generate_pdf(pdf_data: str, output_filename: str):
    pdf = BytesIO()
    
    # Convert the HTML to PDF
    pisa_status = pisa.CreatePDF(BytesIO(pdf_data.encode('utf-8')), dest=pdf)

    # Save the PDF to a file
    with open(output_filename, "wb") as f:
        f.write(pdf.getvalue())
    
    return pisa_status.err

def convert_image_to_rgba(image_path: str, output_path: str):
    # Open the image
    img = Image.open(image_path)
    
    # Convert the image to RGBA if it has a palette
    if img.mode == 'P':
        img = img.convert("RGBA")
    
    # Save the converted image
    img.save(output_path)

def get_tax_content(tax_payer_id: str, notice_number: str, issuedTo: str) -> str:
    convert_image_to_rgba('./assets/OTRGray.png', './assets/OTRGray.png')
    current_date = datetime.datetime.now().strftime("%B %#d, %Y")
    html_content = f"""
        <html>
        <head>
            <style>
                @page {{
                    size: a4 portrait;
                    background-color: lightgray;
                    background-image: url('./assets/OTRGray.png');
                    background-object-position: 50px 300px;
                    background-width: 680px;
                    background-height: 400px;
                    @frame header_frame {{ /* Static Frame */
                        -pdf-frame-content: header_content;
                        left: 30pt; width: 532pt; top: 36pt; height: 70pt;
                    }}
                    @frame content_frame {{ /* Content Frame */
                        left: 30pt; width: 532pt; top: 90pt; height: 740pt;
                    }}
                    @frame footer_frame {{ /* Another static Frame */
                        -pdf-frame-content: footer_content;
                        left: 30pt; width: 532pt; top: 810pt; height: 40pt;
                    }}
                }}
                * {{
                    font-family: serif;
                }}
                table {{
                    width: 100%;
                }}
                td {{
                    vertical-align: bottom;
                    padding: 1px;
                }}
                h1 {{
                    font-size: 20pt;
                    text-align: center;
                }}
                h3 {{
                    font-size: 11pt;
                    text-align: center;
                }}
                #footer_content {{
                    display: flex;
                    justify-content: space-between; /* Aligns items to left and right */
                    width: 500pt;
                }}
                p {{
                    font-size: 12pt;
                }}
                .views-row {{
                    display: flex;
                    justify-content: center;
                }}
                hr {{
                    height: 1px;
                    border: none;  /* Remove any default border */
                    background-color: black;  /* Set the color */
                    margin: 2pt 0 5px;  /* Optional: remove default margin if necessary */
                }}
                .content {{
                    padding: 10px;
                }}
                #content_frame td {{
                    font-size: 11pt;
                }}
                #content_frame {{
                    background: url('./assets/OTRGray.png')
                }}
            </style>
        </head>

        <body>
            <!-- Content for Static Frame 'header_frame' -->
            <div id="header_content">
                <table>
                    <tr>
                        <td style="width:90px; padding-left: 10px"><img src="./assets/dcgov_logo_transparent.png" class="logo" width="70" /></td>
                        <td style="padding-left: 4px">Government of the District of Columbia<br />Office of the Chief Financial Officer<br />Office of Tax and Revenue</td>
                        <td style="width:130px">1101 4<sup>th</sup> Street, SW<br />Washington, DC 20024</td>
                    </tr>
                </table>
                <hr />
            </div>

            <!-- Content for Static Frame 'footer_frame' -->
            <div id="footer_content">
                <hr />
                <center>1101 4th Street SW, Suite W270, Washington, DC 20024/Phone: (202) 724-5045/MyTax.DC.gov</center>
            </div>

            <!-- HTML Content -->
            <div id="content_frame">
                <br />
                <table>
                    <tr>
                        <td>Date of Notice: {current_date}<br /></td>
                        <td>Notice Number: {notice_number}<br /></td>
                        <td rowspan="2" style="width: 30px; vertical-align: middle;"><img src="./assets/symbol.png" /></td>
                    </tr>
                    <tr>
                        <td>{issuedTo}<br />150 CLOVE RD STE 11<br />LITTLE FALLS NJ 07424-2140</td>
                        <td>FEIN: **-***{tax_payer_id}<br />Case ID: 18267406</td>
                    </tr>
                </table>
                <br />
                <div style="padding: 30px">
                    <table style="margin: 30px">
                        <tr>
                            <td><h3><center><b><u>CERTIFICATE OF CLEAN HANDS</u></b></center></h3></td>
                        </tr>
                        <tr>
                            <td>
                                <p style="margin-top: 20px">As reported in the Clean Hands system, the above referenced individual/entity has no outstanding liability with the District of Columbia Office of Tax and Revenue or the Department of Employment Services. As of the date above, the individual/entity has complied with DC Code § 47-2862, therefore this Certificate of Clean Hands is issued.</p>
                            </td>
                        </tr>
                        <tr>
                            <td>
                                <h3 style="text-align: center; margin-top: 30px; font-weight: initial;">
                                    TITLE 47. TAXATION, LICENSING, PERMITS, ASSESSMENTS, AND FEES<br />
                                    CHAPTER 28 GENERAL LICENSE<br />
                                    SUBCHAPTER II. CLEAN HANDS BEFORE RECEIVING A LICENSE OR PERMIT<br />
                                    D.C. CODE § 47-2862 (2006)<br />
                                    § 47-2862 PROHIBITION AGAINST ISSUANCE OF LICENSE OR PERMIT
                                </h3>
                            </td>
                        </tr>
                    </table>
                </div>
                <br /><br /><br /><br /><br /><br /><br /><br /><br /><br />
                <div style="padding: 30px">
                    <table style="margin: 30px">
                        <tr>
                            <td><img src="./assets/signature.png" width="210" /></td>
                        </tr>
                        <tr>
                            <td><p>Authorized By Melinda Jenkins<br />Branch Chief, Collection and Enforcement Administration</p><br /><br /><br /></td>
                        </tr>
                        <tr>
                            <td><p>To validate this certificate, please visit MyTax.DC.gov. On the MyTax DC homepage, click the “Validate a Certificate of Clean Hands” hyperlink under the Clean Hands section.</p></td>
                        </tr>
                    </table>
                </div>
            </div>
        </body>
        </html>
        """
    return html_content

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
                if companyName.text.lower() in str(element[0]).lower():
                    isExist = True
                    data.append(str(element[0]))

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

@app.post("/get-tax-document")
async def get_status(account: TaxAccount):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument('--disable-webgl')
    chrome_options.add_argument('--disable-webrtc')
    chrome_options.add_argument("--remote-debugging-port=9222")

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

        # Wait for the first inputbox to be visible and enabled
        taxPayerBox = WebDriverWait(driver, 60).until(EC.visibility_of_element_located((By.ID, 'Dc-a')))
        taxPayerBox.send_keys(account.tax_payer_id)
        print("Put tax payer id into inputbox")

        # Wait for the second inputbox to be visible and enabled
        notiveNumberBox = WebDriverWait(driver, 60).until(EC.visibility_of_element_located((By.ID, 'Dc-8')))
        notiveNumberBox.send_keys(account.notice_number)
        print("Put Notice number into inputbox")

        # Wait for the button to be clickable
        button = WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.ID, 'Dc-c')))
        button.click()
        print("Clicked login button")
        time.sleep(1)
        # Scroll down the page using JavaScript
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        print("Scroll down")

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        issuedDateElement = WebDriverWait(driver, 60).until(EC.visibility_of_element_located((By.ID, 'Dc-h')))
        issuedDate = issuedDateElement.get_attribute('value')
        print("Got issued Date: ", issuedDate)

        issuedToElement = WebDriverWait(driver, 60).until(EC.visibility_of_element_located((By.ID, 'Dc-i')))
        issuedTo = issuedToElement.get_attribute('value')
        print("Got issued To: ", issuedTo)

        pdf_file_path = 'report.pdf'
        html_content = get_tax_content(account.tax_payer_id, account.notice_number, issuedTo)
        generate_pdf(html_content, pdf_file_path)
        print('Generated a pdf file successfully!')
        # return {"message": "Generated a pdf file successfully!"}

        # Recipient email and path to pdf
        subject = 'Certificate Document'
        pdf_title = 'Please check the attached PDF document to see tax payer status.'
        hasSent = await EmailHandler().send_email_with_pdf(account.recipient_email, pdf_file_path, subject, pdf_title)
        if hasSent == True:
            return {"message": "You has been sent the email successfully."}
        else:
            return {"message": "An error occurred while sending email"}

    except:
        traceback.print_exc()
        return {"message": "An error occurred while loading the element"}

@app.post("/get-companies-list")
async def get_companies(recipient: Recipient):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument('--disable-webgl')
    chrome_options.add_argument('--disable-webrtc')
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

    # Find the element with id 'block-system-main'
    try:
        header = 'Excluded Parties List'
        title = 'Office of Contracting and Procurement'

        # Locate the main block
        system_main = driver.find_element(By.CSS_SELECTOR, "#block-views-agency-information-block")

        # Locate the child element
        content_html = system_main.find_element(By.CSS_SELECTOR, ".view-agency-information-details").get_attribute('innerHTML')
        
        # Assume content_html contains your HTML content
        soup = BeautifulSoup(content_html, 'html.parser')
        # Remove all <a> tags
        for a in soup.find_all('a'):
            img = a.find('img')
            if 'mailto' not in a.get('class', []) and (img is None or img.get('src', '').startswith('/')):
                a.decompose()  # Remove the <a> tag if it doesn't have the class "mailto"

        # Get the modified HTML without <a> tags
        modified_html = '<h3>Office of Contracting and Procurement</h3>'
        modified_html += '''
            <div style="width: 100%">
                <table style="width: 100%; border-collapse: collapse; border: none;">
                    <tr>
                        <td style="width: 200px; border: none; vertical-align: top;">
                            <img src="./assets/OCPLOGO.png" width="200" />
                        </td>
                        <td style="border: none; vertical-align: top;">
                            ''' + soup.prettify() + '''
                        </td>
                    </tr>
                </table>
            </div>
            '''

        system_main = driver.find_element(By.ID, "block-system-main")
        modified_html += system_main.get_attribute('innerHTML')

        pdf_file_path = 'report.pdf'
        create_pdf_from_html(title, header, modified_html, pdf_file_path)
        print('Generated a pdf file successfully!')
        # return {"message": "Generated a pdf file successfully!"}

        # Recipient email and path to pdf
        subject = 'Excluded Parties List'
        pdf_title = 'Please check the attached PDF document to see excluded parties list.'
        hasSent = await EmailHandler().send_email_with_pdf(recipient.email, pdf_file_path, subject, pdf_title) 
        if hasSent == True:
            return {"message": "You has been sent the email successfully."}
        else:
            return {"message": "An error occurred while sending email"}

    except Exception as e:
        return {"message": f"Error finding element: {str(e)}"}

@app.post("/get-exclusions-document")
async def get_exclusions(account: SamGovAccount):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument('--disable-webgl')
    chrome_options.add_argument('--disable-webrtc')
    chrome_options.add_argument("--remote-debugging-port=9222")
    
    # Get the project root directory (current working directory)
    project_root = os.getcwd()

    chrome_prefs = {
        "download.default_directory": project_root,  # Set download directory to project root
        "download.prompt_for_download": False,       # Do not prompt for download
        "download.directory_upgrade": True,          # Automatically overwrite old downloads
        "safebrowsing.enabled": True                 # Enable safe browsing to avoid popups
    }
    chrome_options.add_experimental_option('prefs', chrome_prefs)
    # chrome_options.add_argument('--kiosk-printing')

    driver = webdriver.Chrome(options=chrome_options)
    
    # Create a dictionary with the custom header
    headers = {
        "Origin": "*"
    }

    # Send the custom header using Chrome DevTools Protocol
    driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {'headers': headers})

    driver.get('https://sam.gov/content/home')
    time.sleep(3)

    # Now simulate the 'Close Modal' button press
    closeModalButton = WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="sds-dialog-0"]/button')))
    closeModalButton.click()
    time.sleep(1)

    try:
        # Find login link on top coner
        loginLink = WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="signIn"]/span')))
        loginLink.click()
        time.sleep(1)

        # Click agree button
        agreeButton = WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="sds-dialog-1"]/ng-component/div[4]/button[2]')))
        agreeButton.click()
        time.sleep(1)

        # Scroll down the page using JavaScript
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        print("Scroll down")

        userInputBox = WebDriverWait(driver, 60).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="user_email"]')))
        # Check if the element is enabled
        if userInputBox.is_enabled():
            # Now you can interact with the input box
            userInputBox.send_keys(account.email)
            print("Put user's email into inputbox")
        else:
            print("The input box is not enabled.")

        passwordInputBox = WebDriverWait(driver, 60).until(EC.visibility_of_element_located((By.XPATH, '//*[starts-with(@id, "password-toggle-input-")]')))
        # Check if the element is enabled
        if passwordInputBox.is_enabled():
            # Now you can interact with the input box
            passwordInputBox.send_keys(account.password)
            print("Put user's password into passwordbox")
        else:
            print("The input box is not enabled.")

        loginButton = WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="new_user"]/lg-submit-button/button')))
        loginButton.click()
        print("Clicked login button")
        time.sleep(2)

        backupCodeInputBox = WebDriverWait(driver, 60).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="backup_code_verification_form_backup_code"]')))
        # Check if the element is enabled
        if backupCodeInputBox.is_enabled():
            # Now you can interact with the input box
            backupCodeInputBox.send_keys(account.backup_code)
            print("Put user's backup code into inputbox")
        else:
            print("The input box is not enabled.")        
        
        submitButton = WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="new_backup_code_verification_form"]/lg-submit-button/button')))
        submitButton.click()
        print("Clicked submit backup code button")
        time.sleep(2)
        
        # try:
        #     # Wait for the element to be visible
        #     validateMessage = WebDriverWait(driver, 2).until(EC.visibility_of_element_located((By.XPATH, '//*[starts-with(@id, "validated-field-error-")]')))
        #     driver.quit()
        #     # If we reach this point, the element was found
        #     return {"message": validateMessage.text}
        # except (TimeoutException, NoSuchElementException) as e:
        #     # Handle the case where the element was not found within the timeout
        #     print("Element not found within the given time.")

        # Navigate to the specific URL
        target_url = 'https://sam.gov/entities/view/G2DYNCVB75U9/exclusionInfo?status=Active&emrKeyValue=2519528~1724323876123673'
        driver.get(target_url)
        print("Redirected to exclusions page")

        # Give it some time to load
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        print("Scroll down")

        actionButton = WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="subheaderContent"]/div/div/sds-subheader/div/div/div[4]/sds-subheader-actions/span[1]/button')))
        actionButton.click()
        print("Clicked Action menu")

        downloadLink = WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="cdk-overlay-0"]/div/div/button[1]')))
        downloadLink.click()
        time.sleep(1)

        filenameInputBox = WebDriverWait(driver, 60).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="formly_5_input_fileName_2"]')))
        # Check if the element is enabled
        if filenameInputBox.is_enabled():
            # Clear the original value in the input box
            filenameInputBox.clear()
            filenameInputBox.send_keys('report')
            print("Put pdf file name into inputbox")
        else:
            print("The input box is not enabled.")

        downloadButton = WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="sds-dialog-0"]/sds-formly-dialog/form/div[3]/button[2]')))
        downloadButton.click()
        time.sleep(2)

        pdf_file_path = 'report.pdf'
        # return {"message": "Downloaded a pdf file successfully!"}

        # Recipient email and path to pdf
        subject = 'Exclusions'
        pdf_title = 'Please check the attached PDF document to see exclusions.'
        hasSent = await EmailHandler().send_email_with_pdf(account.email, pdf_file_path, subject, pdf_title) 
        if hasSent == True:
            driver.quit()
            return {"message": "You has been sent the email successfully."}
        else:
            return {"message": "An error occurred while sending email"}

    except Exception as e:
        return {"message": f"Error finding element: {str(e)}"}
