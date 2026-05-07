import time
import random
import os
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager

from scrapper import get_product_data, get_site_label
from db.sheets import get_sheet, upload_to_sheets
from db.mongodb import get_collection, upload_to_mongo

load_dotenv()

URLS_FILE = os.getenv("URLS_FILE_PATH", "urls.txt")  # Default to urls.txt if not set
FIREFOX_PROFILE = os.getenv("FIREFOX_PROFILE_PATH")

with open(URLS_FILE, "r") as f:
    websites = [line.strip() for line in f if line.strip() and not line.startswith("#")]
print(f"✅ Loaded {len(websites)} URLs from {URLS_FILE}")

print("\n⚠️  Make sure Firefox is fully closed before continuing!")
input("Press ENTER when Firefox is closed...")
options = Options()
options.add_argument("-profile")
options.add_argument("FIREFOX_PROFILE")
options.set_preference("dom.webdriver.enabled", False)
options.set_preference("useAutomationExtension", False)
options.set_preference(
    "general.useragent.override",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0"
)
service = Service(GeckoDriverManager().install())
driver = webdriver.Firefox(service=service, options=options)
driver.minimize_window()
try:
    all_data = []
    for url in websites:
        print(f"\nProcessing: {url}")
        site = get_site_label(url)
        name, price = get_product_data(driver, url)
        all_data.append((site, url, name, price))
        time.sleep(random.uniform(1, 2))
finally:
    driver.quit()


sheet = get_sheet()
upload_to_sheets(sheet, all_data)

collection = get_collection()
upload_to_mongo(collection, all_data)