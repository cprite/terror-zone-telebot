import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from bs4 import BeautifulSoup

from zones import ZONES


def get_terror_zone_info():

    driver = webdriver.Chrome()

    driver.get("https://www.d2emu.com/tz")

    page_source = driver.page_source

    driver.close()

    soup = BeautifulSoup(page_source, 'html.parser')

    span = soup.find_all("span", {"class": "terrorzone darkmode-ignore"})

    current = span[0]
    next = span[1]

    # Extract the raw HTML content inside the span
    raw_html_current = current.decode_contents()
    raw_html_next = next.decode_contents()

    # Split the content by <br/> tags
    zone_parts_current = raw_html_current.split('<br/>')
    zone_parts_next = raw_html_next.split('<br/>')

    # Remove any surrounding whitespace
    zone_parts_current = [text.strip() for text in zone_parts_current]
    zone_parts_next = [text.strip() for text in zone_parts_next]


    for zone in ZONES:
        if zone == " ".join(zone_parts_current):
            print(f"{zone} is a CURRENT terror zone")
        elif zone == " ".join(zone_parts_next):
            print(f"{zone} is a NEXT terror zone")



get_terror_zone_info()
