import scrapy
from ICP_UAE.items import Product
from lxml import html
import json
import asyncio
from datetime import datetime
from scrapy.http import HtmlResponse
from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright
from scrapy_playwright.page import PageMethod
import os
import base64
import requests
import ast
import pandas as pd
import time


url = 'https://smartservices.icp.gov.ae/echannels/web/client/default.html#/login'
API_KEY = 'a661689231b7cd6552be2b7cce88cd52'  # <- Replace with your actual 2Captcha API key

def solve_recaptcha(sitekey, pageurl, API_KEY):
    # Submit CAPTCHA to 2Captcha
    payload = {
        'key': API_KEY,
        'method': 'userrecaptcha',
        'googlekey': sitekey,
        'pageurl': pageurl,
        'json': 1
    }

    try:
        response = requests.post('http://2captcha.com/in.php', data=payload)
        result = response.json()
        if result.get('status') != 1:
            print("2Captcha submission error:", result)
            return None
        request_id = result.get('request')
    except Exception as e:
        print("Request submission failed:", e)
        return None

    # Poll for result
    fetch_url = f"http://2captcha.com/res.php?key={API_KEY}&action=get&id={request_id}&json=1"
    for _ in range(20):  # wait up to ~100 seconds
        time.sleep(5)
        try:
            response = requests.get(fetch_url)
            result = response.json()
            if result.get('status') == 1:
                print("CAPTCHA solved.")
                return result.get('request')
            elif result.get('request') != 'CAPCHA_NOT_READY':
                print("2Captcha error:", result)
                return None
        except Exception as e:
            print("Polling failed:", e)
            return None

    print("CAPTCHA solve timeout.")
    return None


country_list = {
    'INDIA': 25,
    'PAKISTAN': 24,
    'PHILIPPINES': 40,
}

class Icp_uaeSpider(scrapy.Spider):
    name = "ICP_UAE"
    # allowed_domains = ["smartservices.icp.gov.ae"]
    # start_urls = ["https://smartservices.icp.gov.ae/echannels/web/client/default.html#/login"]
    allowed_domains = ['example.com']
    start_urls = ['https://www.example.com/']

    def parse(self, response):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.abspath(os.path.join(base_dir, '..', 'output_part_5.csv'))

        self.logger.info(f"Looking for CSV at: {csv_path}")

        if not os.path.exists(csv_path):
            self.logger.error(f"CSV file does not exist: {csv_path}")
            return
        df = pd.read_csv(csv_path).to_dict('records')

        import chompjs
        site_key = '6Lfj6nIUAAAAAD76VheUIK0jYhKYxJRdQF8eG7lh'
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json;charset=UTF-8',
            'Origin': 'https://smartservices.icp.gov.ae',
            'Referer': 'https://smartservices.icp.gov.ae/echannels/web/client/default.html',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
            'languageId': '2',
            'sec-ch-ua': '"Not.A/Brand";v="99", "Chromium";v="136"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
            'skipCaptcha': 'true',
            # 'Cookie': 'cookiesession1=678B28688263A39145FBA488EC2C60EC; fp=6796e327850f5b9c8c7697b0cfb34fdc; cookieAccepted=true',
        }

        request_headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'CURRENT_PORTAL': 'ICA',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json;charset=UTF-8',
            'Origin': 'https://smartservices.icp.gov.ae',
            'Referer': 'https://smartservices.icp.gov.ae/echannels/web/client/default.html',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
            'languageId': '2',
            'sec-ch-ua': '"Not.A/Brand";v="99", "Chromium";v="136"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
            # 'Cookie': 'cookiesession1=678B28688263A39145FBA488EC2C60EC; fp=6796e327850f5b9c8c7697b0cfb34fdc; cookieAccepted=true',
        }

        request_json_data = {
            'requestNumber': '0101107642022023427186602',
            'nationality': 25,
            'dateOfBirth': '1999/04/24',
        }
        c = 0
        for i in df:
            c += 1
            pipl = i.get('pipl')
            json_data = chompjs.parse_js_object(pipl)
            customer_details = chompjs.parse_js_object(json_data.get('input_data'))
            name = customer_details.get('Name', '')
            nationality = customer_details.get('Nationality', '')
            emirates_id = customer_details.get('Emiratesid', '').replace('-', '').replace(' ', '')
            date_of_birth = customer_details.get('Birth Date', '')
            
            if '_DUPL' in emirates_id:
                emirates_id = emirates_id.split('_DUPL_')[0].strip()

            if '00:' in date_of_birth:
                date_of_birth = date_of_birth.split(' ')[0].strip()
            try:
                date_obj = datetime.strptime(date_of_birth, "%Y-%m-%d")
                formatted_date = date_obj.strftime("%Y/%m/%d")
            except Exception as error:
                print(error)
                date_obj = ''
            # 1999/04/24 .strftime("%d/%m/%Y")
            # print(date_of_birth)
            if 'Pakistani' in nationality.lower() or 'pak' in nationality.lower() or 'pakistan' in nationality.lower():
                nationality = 'PAKISTAN'
            if 'Indian' in nationality.capitalize() or 'ind' in nationality.lower() or 'india' in nationality.lower():
                nationality = 'INDIA'
            if 'Filipino' in nationality.capitalize() or 'Philippines' in nationality.lower() or 'philippines' in nationality.lower():
                nationality = 'PHILIPPINES'
            try:
                emirates_id = int(emirates_id)
            except Exception as error:
                print(error)
                emirates_id = None
            national_id = country_list.get(nationality, '')
            if (isinstance(emirates_id, int) and emirates_id and len(str(emirates_id)) > 12) and (date_obj and len(str(date_obj))>3) and (nationality and len(nationality) > 2) and national_id:

                # print('hi', emirates_id)
                #(isinstance(emirates_id, int) and emirates_id and len(str(emirates_id))>4) and (date_obj and len(str(date_obj))>3) and nationality
                json_data = {
                    'requestDraftNumber': '784199988788123',
                    'requestType': 1,
                    'isValidCaptcha': True,
                    'recaptchaResponse': '',
                }
                captcha_token = solve_recaptcha(site_key, url, API_KEY)
                json_data['recaptchaResponse'] = f'{captcha_token}'
                json_data['requestDraftNumber'] = f'{emirates_id}'

                response = requests.post(
                    'https://smartservices.icp.gov.ae/echannels/api/api/landing/getRequestInfoQuickSearch',
                    headers=headers,
                    json=json_data,
                )
                request_token = response.json().get('requestDratftDto', {}).get('requestNumber', '')
                request_json_data['requestNumber'] = request_token
                request_json_data['dateOfBirth'] = formatted_date
                request_json_data['nationality'] = national_id
                res = requests.post(
                    'https://smartservices.icp.gov.ae/echannels/api/api/landing/downloadEid',
                    # cookies=cookies,
                    headers=request_headers,
                    json=request_json_data,
                )
                
                pdf_output_dir = os.path.abspath(os.path.join(base_dir, '..', 'pdfs'))
                os.makedirs(pdf_output_dir, exist_ok=True)
                try:
                    base64_string = str(res.json().get('byteArrayBase64String'))
                    base64_string = base64_string.strip()
                    pdf_path = os.path.join(pdf_output_dir, f"{emirates_id}.pdf")
                    with open(pdf_path, "wb") as pdf_file:
                        pdf_file.write(base64.b64decode(base64_string))
                except Exception as e:
                    print('=========================================================')
                    print(e)
                    print(res.json())
                    print('=========================================================')
                
                    
                # break
                # data = {
                #     'customer_name': str(name),
                #     'nationality': str(nationality),
                #     'emirates_id': str(emirates_id),
                #     'date_of_birth': date_of_birth,
                #     'pdf_data': str(base64.b64decode(base64_string))
                    
                # }
                # yield Product(**data)
                # if c == 3:
                #     break