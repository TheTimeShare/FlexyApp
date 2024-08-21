import pandas as pd
import os
import time
import pyautogui
from ics import Calendar, Event
from datetime import datetime, timedelta
import pytz
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from pynput.keyboard import Key, Controller

local_tz = pytz.timezone('Europe/Copenhagen')

options = Options()
options.headless = True  # Set to False for debugging (so you can see the browser)
options.add_argument("--no-sandbox")
# options.add_argument('headless')
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--disable-extensions")
options.add_argument("--disable-infobars")
options.add_argument("--disable-notifications")
options.add_argument("--remote-debugging-port=9222")
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--user-data-dir=/tmp/chrome")  # Use a temporary profile
options.add_argument("--no-first-run")  # Skip first run check
options.add_argument("--disable-default-apps")  # Disable default apps
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def login_and_scrape(email, password):
    try:
        # login_url = "https://v2.flexybox.com/app/log-ind/app/beskeder"
        data_url = "https://v2.flexybox.com/app/oversigt/vagtliste"

        keyboard = Controller()

        print("gg")
        driver.get(data_url)
        print("Page Title:", driver.title)
        print()

        print("0")
        # Wait for the email input field to be present
        try:
            email_field = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='UserName']")))
            time.sleep(1)
        except TimeoutException:
            print("Timed out waiting for email input field to load")
            return None

        email_field.send_keys(email)
        print("1")

        # Wait for the password input field to be present
        try:
            password_field = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='Password']")))
            time.sleep(1)
        except TimeoutException:
            print("Timed out waiting for password input field to load")
            return None

        print("2")
        password_field.send_keys(password)        
        time.sleep(1)
        password_field.submit()
        

        print("Logged in! Navigating to vagtplan...")
        print("Tryk på Sign in")
        print()

        print("3")
        time.sleep(3)

        # driver.get(data_url)

        print("Scraping data from the page")
        print("4")
        print()
        time.sleep(1)

        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "table")))  # Wait for the table to load

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        data = []
        for row in soup.select('table tr'):
            columns = row.find_all('td')
            if len(columns) > 1:
                datum = {
                    'Afdeling': columns[5].get_text(strip=True),
                    'Dato': columns[0].get_text(strip=True),
                    'Tidspunkt': columns[2].get_text(strip=True),
                    'Kommentar': columns[6].get_text(strip=True) if len(columns) > 3 else ''
                }
                data.append(datum)

        calendar = Calendar()

        def parse_time_range(date_str, time_range, tz):
            start_time_str, end_time_str = time_range.split(' – ')
            start = tz.localize(datetime.strptime(f"{date_str} {start_time_str}", '%d-%m-%Y %H:%M'))
            end = tz.localize(datetime.strptime(f"{date_str} {end_time_str}", '%d-%m-%Y %H:%M'))

            if end <= start:
                end += timedelta(days=1)

            return start, end

        for item in data:
            event = Event()
            event.name = f"Sport hos {item['Afdeling']}"

            start_date_str = item['Dato']

            start, end = parse_time_range(start_date_str, item['Tidspunkt'], local_tz)

            event.begin = start
            event.end = end
            event.description = item['Kommentar'] if item['Kommentar'] else ''

            print(f"Event: {event.name}")
            print(f"Start: {event.begin}")
            print(f"End: {event.end}")
            print(f"Description: {event.description}")
            print()

            calendar.events.add(event)

        ics_file_path = 'flexyvagter.ics'
        with open(ics_file_path, 'w') as f:
            f.writelines(calendar)

        print("iCalendar file 'flexyvagter.ics' has been created!")
        print(f"ICS file path: {os.path.abspath(ics_file_path)}")  # Print the full path to the ICS file
        print()

        return ics_file_path

    except Exception as e:
        print(f"Error: {e}")
        return None

    finally:
        driver.quit()

if __name__ == '__main__':
    email = input("Enter your email: ")
    password = input("Enter your password: ")
    ics_file_path = login_and_scrape(email, password)
    if ics_file_path:
        print(f"Your calendar has been saved to {ics_file_path}")
    else:
        print("Failed to generate iCalendar file.")
