from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager

import time
import os

""""""

def terror_zone_loop():

    first_run = True

    while True:

        current_time = time.localtime()

        if current_time.tm_min == 5 or first_run:

            chrome_options = webdriver.ChromeOptions()
            chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
            print("____________________________________10")
            chrome_options.add_argument("start-maximized")
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--no-sandbox")

            # service = Service(executable_path=os.environ.get("CHROMEDRIVER_PATH"))
            print("____________________________________11")

            # driver = webdriver.Chrome(service=service, options=chrome_options)
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

            print("____________________________________12")

            driver.get("https://www.d2emu.com/tz")

            print("____________________________________13")

            page_source = driver.page_source

            driver.close()

            soup = BeautifulSoup(page_source, 'html.parser')

            span = soup.find_all("span", {"class": "terrorzone darkmode-ignore"})

            print(span)

            # current = span[0]
            next = span[1]

            # Extract the raw HTML content inside the span
            # raw_html_current = current.decode_contents()
            raw_html_next = next.decode_contents()

            # Split the content by <br/> tags
            # zone_parts_current = raw_html_current.split('<br/>')
            zone_parts_next = raw_html_next.split('<br/>')

            # Remove any surrounding whitespace
            # zone_parts_current = [text.strip() for text in zone_parts_current]
            zone_parts_next = [text.strip() for text in zone_parts_next]

            with open("../data/next_zone.txt", "w") as file:
                for part in zone_parts_next:
                    file.write(part + "\n")

            first_run = False

        time.sleep(60)


if __name__ == "__main__":
    terror_zone_loop()
