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
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from flask import Flask, render_template, send_file

app = Flask(__name__)

local_tz = pytz.timezone('Europe/Copenhagen')

options = Options()
options.headless = True  # Set to False for debugging (so you can see the browser)
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def login_and_scrape(email, password):
    try:
        login_url = "https://v2.flexybox.com/app/log-ind/app/beskeder"
        data_url = "https://v2.flexybox.com/app/oversigt/vagtliste"

        driver.get(login_url)
        print("Page Title:", driver.title)
        print()

        login_credentials = {
            "mail": email,
            "password": password
        }

        email_field = driver.find_element(By.CSS_SELECTOR, "input[name='UserName']")
        email_field.send_keys(login_credentials['mail'])

        password_field = driver.find_element(By.CSS_SELECTOR, "input[name='Password']")
        password_field.send_keys(login_credentials['password'])
        password_field.submit()

        print("Logged in! Navigating to duty schedule...")
        print()

        time.sleep(1)

        driver.get(data_url)

        print("Scraping data from the page")
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
        print()

        return ics_file_path

    except Exception as e:
        print(f"Error: {e}")
        return None

    finally:
        driver.quit()

@app.route('/download/<email>/<password>')
def download_ics(email, password):
    ics_file_path = login_and_scrape(email, password)
    if ics_file_path:
        return send_file(ics_file_path, as_attachment=True)
    else:
        return "Failed to generate iCalendar file."

if __name__ == '__main__':
    app.run(debug=True)