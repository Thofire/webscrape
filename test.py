import re
import gspread
from google.oauth2.service_account import Credentials
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# -------------------------------
# Scrape Product Data (Multi-Site)
# -------------------------------
def get_product_data(driver, url):
    driver.get(url)
    # wait until body is loaded
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    time.sleep(1.5)  # small buffer for JS to finish rendering

    name = "ERROR"
    price = "ERROR"
    source = driver.page_source

    try:
        if "homedepot.com" in url:
            # Name
            name_match = re.search(r'"productLabel"\s*:\s*"([^"]+)"', source)
            if name_match:
                name = name_match.group(1)

            # Price — target the large price number span HD uses
            try:
                price_container = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((
                        By.XPATH,
                        "//div[contains(@class,'sui-flex') and .//span[contains(@class,'sui-text-9xl')]]"
                    ))
                )
                dollar = price_container.find_element(
                    By.XPATH, ".//span[contains(@class,'sui-text-9xl')]"
                ).text.strip()
                cents_els = price_container.find_elements(
                    By.XPATH, ".//span[contains(@class,'sui-text-3xl')]"
                )
                cents = cents_els[1].text.strip() if len(cents_els) >= 2 else "00"
                price = f"${dollar}.{cents}"
            except:
                # Fallback to JSON
                price_match = re.search(r'"value"\s*:\s*([\d.]+)', source)
                if price_match:
                    price = f"${price_match.group(1)}"

        elif "lowes.com" in url:
            # Name
            try:
                name_el = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "h1.product-brand-description"))
                )
                name = name_el.text.strip()
            except:
                name_match = re.search(r'"productTitle"\s*:\s*"([^"]+)"', source)
                if name_match:
                    name = name_match.group(1).strip()

            # Price
            try:
                price_el = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='main-price']"))
                )
                raw = price_el.text.replace("Now", "").strip()
                price_match = re.search(r'\$([\d,.]+)', raw)
                if price_match:
                    price = f"${price_match.group(1)}"
            except:
                dollar_match = re.search(r'<span class="item-price-dollar"[^>]*>([\d]+)<\/span>', source)
                cent_match = re.search(r'<div class="item-price-cent[^"]*"[^>]*>(\.[\d]+)<\/div>', source)
                if dollar_match and cent_match:
                    price = f"${dollar_match.group(1)}{cent_match.group(1)}"
                elif dollar_match:
                    price = f"${dollar_match.group(1)}.00"
        elif "amazon.com" in url:
    # Name
            try:
                name_el = WebDriverWait(driver, 8).until(
                    EC.presence_of_element_located((By.ID, "productTitle"))
                )
                name = name_el.text.strip()
            except:
                name_match = re.search(r'<span id="productTitle"[^>]*>([^<]+)<', source)
                if name_match:
                    name = name_match.group(1).strip()

            # Price — Amazon has several price locations depending on product type
            try:
                # Primary price location
                price_el = driver.find_element(By.CSS_SELECTOR, "span.a-price.aok-align-center span.a-offscreen")
                price = price_el.get_attribute("innerHTML").strip()
            except:
                try:
                    # Secondary location (used on some listings)
                    price_el = driver.find_element(By.CSS_SELECTOR, "#corePrice_feature_div span.a-offscreen")
                    price = price_el.get_attribute("innerHTML").strip()
                except:
                    try:
                        # Third fallback
                        price_el = driver.find_element(By.CSS_SELECTOR, "#apex_desktop span.a-offscreen")
                        price = price_el.get_attribute("innerHTML").strip()
                    except:
                        price_match = re.search(r'"price"\s*:\s*"?\$?([\d.]+)"?', source)
                        if price_match:
                            price = f"${price_match.group(1)}"

        else:
            name_match = re.search(r'"name"\s*:\s*"([^"]+)"', source)
            price_match = re.search(r'"price"\s*:\s*"?([\d.]+)"?', source)
            if name_match:
                name = name_match.group(1)
            if price_match:
                price = f"${price_match.group(1)}"

    except Exception as e:
        print(f"  ⚠️ Error parsing page: {e}")

    print(f"  Name: {name}")
    print(f"  Price: {price}")
    return name, price

# -------------------------------
# Helper functions
# -------------------------------
def get_site_label(url):
    if "homedepot.com" in url:
        return "Home Depot"
    elif "lowes.com" in url:
        return "Lowe's"
    elif "amazon.com" in url:
        return "Amazon"
    else:
        return "Other"

# -------------------------------
# Google Sheets Setup
# -------------------------------
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_file("credentials.json.env", scopes=scope)
client = gspread.authorize(creds)
sheet = client.open("Prices").sheet1
sheet.clear()
sheet.append_row(['Site', 'URL', 'Item', 'Price'])

# -------------------------------
# Input URLs
# -------------------------------
URLS_FILE = r"C:\Users\Thofire\Desktop\webscrape\urls.txt"

with open(URLS_FILE, "r") as f:
    websites = [line.strip() for line in f if line.strip() and not line.startswith("#")]

print(f"✅ Loaded {len(websites)} URLs from {URLS_FILE}")
for url in websites:
    print(f"   - {url}")
# -------------------------------
# Setup Profile
# -------------------------------
print("\n⚠️  Make sure Firefox is fully closed before continuing!")
input("Press ENTER when Firefox is closed...")

FIREFOX_PROFILE = r"C:\Users\Thofire\Desktop\webscrape\firefox_profile"

# -------------------------------
# Selenium Firefox Setup
# -------------------------------
options = Options()
options.add_argument("--start-maximized")
options.add_argument("-profile")
options.add_argument(FIREFOX_PROFILE)
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
    # Step 1: Visit homepages to establish sessions
    all_data = []
    # Step 3: Scrape
    for url in websites:
        print(f"\nProcessing: {url}")
        site = get_site_label(url)
        name, price = get_product_data(driver, url)
        all_data.append((site, url, name, price))
        time.sleep(random.uniform(1, 2))

finally:
    driver.quit()

# -------------------------------
# Upload to Google Sheets
# -------------------------------
for row in all_data:
    sheet.append_row(list(row))

print("\n✅ Done! Data uploaded to Google Sheets.")