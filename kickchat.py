import sys
import os
import signal
import threading
import time
import json
from datetime import datetime
import pytz
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, WebDriverException
import re

# Global flag to control parsing
stop_parsing = False

def setup_driver():
    chrome_options = Options()
    # Non-headless for debugging
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-logging")
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def convert_timestamp(raw_timestamp):
    if not raw_timestamp:
        edt_tz = pytz.timezone("America/New_York")
        local_time = datetime.now(edt_tz)
        return local_time.strftime("%I:%M %p").lstrip("0")
    try:
        # Parse the raw timestamp (e.g., "10:46") as a time on today's date
        today = datetime.now(pytz.UTC).date()
        parsed_time = datetime.strptime(f"{today} {raw_timestamp}", "%Y-%m-%d %H:%M")
        
        # Assume the raw timestamp is already in EDT (since it matches local time)
        # Localize it as EDT directly
        edt_tz = pytz.timezone("America/New_York")
        parsed_time = edt_tz.localize(parsed_time)
        
        # Format in 12-hour format
        return parsed_time.strftime("%I:%M %p").lstrip("0")
    except ValueError as e:
        print(f"Error converting timestamp '{raw_timestamp}': {e}")
        return raw_timestamp

def validate_url(url):
    if not re.match(r'^https?://', url):
        return False
    if 'kicktools.app/fusion_chat' not in url:
        return False
    return True

def parse_chat(url, output_file="chat_messages.json"):
    global stop_parsing

    if not validate_url(url):
        print(f"Error: Invalid URL '{url}'. It must start with 'http://' or 'https://' and contain 'kicktools.app/fusion_chat'.")
        return

    driver = None
    try:
        driver = setup_driver()
        print(f"Attempting to load Fusion Chat overlay: {url}")
        driver.get(url)
        print(f"Loaded Fusion Chat overlay: {url}")

        messages_data = []
        seen_message_ids = set()
        container_found = False

        while not stop_parsing:
            try:
                chat_container = driver.find_elements(By.CSS_SELECTOR, "#chat")
                if not chat_container:
                    print("Chat container not found, continuing to monitor...")
                    time.sleep(1)
                    continue
                if not container_found:
                    print("Chat container found")
                    container_found = True

                message_elements = driver.find_elements(By.CSS_SELECTOR, ".message-item")
                if not message_elements:
                    time.sleep(0.1)
                    continue

                for message in message_elements:
                    message_id = message.get_attribute("id") or hash(message.text)
                    if message_id in seen_message_ids:
                        continue
                    seen_message_ids.add(message_id)

                    # Log raw HTML for debugging
                    raw_html = message.get_attribute("innerHTML")
                    print(f"Raw HTML: {raw_html[:200]}...")

                    message_data = {}
                    # Timestamp with retries
                    raw_timestamp = ""
                    for _ in range(5):
                        try:
                            raw_timestamp = message.find_element(By.CSS_SELECTOR, ".timestamp").text.strip()
                            if raw_timestamp:
                                break
                        except NoSuchElementException:
                            raw_timestamp = ""
                            break
                        time.sleep(0.1)
                    print(f"Raw timestamp: '{raw_timestamp}'")
                    message_data["timestamp"] = convert_timestamp(raw_timestamp)

                    # Username with retries
                    username = None
                    for _ in range(5):
                        try:
                            username = message.find_element(By.CSS_SELECTOR, ".username, .username.kick").text.strip()
                            if username:
                                break
                        except NoSuchElementException:
                            username = None
                            break
                        time.sleep(0.1)
                    message_data["username"] = username
                    print(f"Raw username: '{username}'")

                    # Message with retries
                    message_text = None
                    for _ in range(5):
                        try:
                            message_text = message.find_element(By.CSS_SELECTOR, ".message").text.strip()
                            if message_text:
                                break
                        except NoSuchElementException:
                            message_text = None
                            break
                        time.sleep(0.1)
                    message_data["message"] = message_text
                    print(f"Raw message: '{message_text}'")

                    if message_data["message"] and message_data["username"]:
                        messages_data.append(message_data)
                        print(f"Parsed: {message_data}")
                        with open(output_file, "w", encoding="utf-8") as f:
                            json.dump(messages_data, f, indent=2, ensure_ascii=False)

            except Exception as e:
                print(f"Error parsing messages: {e}")

            time.sleep(0.1)

    except WebDriverException as e:
        print(f"Error loading URL '{url}': {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if driver:
            driver.quit()
        print(f"Stopped parsing for URL: {url}")
        if messages_data:
            print(f"Saved {len(messages_data)} messages to {output_file}")
        else:
            print("No messages parsed")

def signal_handler(sig, frame):
    global stop_parsing
    print("Received stop signal, shutting down...")
    stop_parsing = True

def check_stop_file():
    global stop_parsing
    stop_file = "stop.txt"
    while not stop_parsing:
        if os.path.exists(stop_file):
            print(f"Found {stop_file}, shutting down...")
            stop_parsing = True
            os.remove(stop_file)
            break
        time.sleep(1)

def main():
    if len(sys.argv) != 2:
        print("Usage: python kickchat.py <fusion_chat_url>")
        print("Example: python kickchat.py \"https://kicktools.app/fusion_chat/fusion-chat.html?kick=communitycontroller&twitch=&font=Inter&fontSize=Large&fontShadow=shadow-na&fontColor=%23ffffff&theme=basic&fontCase=none×tamp=on&userBadges=on&fadeTime=1\"")
        sys.exit(1)

    url = sys.argv[1]
    print(f"Starting chat parsing for URL: {url}")

    signal.signal(signal.SIGINT, signal_handler)

    parse_thread = threading.Thread(target=parse_chat, args=(url,), daemon=True)
    parse_thread.start()

    check_stop_file()

    parse_thread.join()

if __name__ == "__main__":
    main()