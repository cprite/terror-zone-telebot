import requests
import os
import time


def ping():
    while True:

        try:

            url = os.getenv('URL')
            response = requests.get(url)
            print(f"Server status: {response.status_code}")

        except Exception as e:
            print(f"Error: {e}")

        time.sleep(60)


if __name__ == "__main__":
    ping()
