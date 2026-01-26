import os
import time
import random
import requests
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from openpyxl import Workbook
import speech_recognition as sr
from pydub import AudioSegment
from langchain_core.tools import tool

@tool
def add_tool(x: int, y: int):
    "add both provided integers"
    return x + y

# --- CONFIGURATION ---
SEARCH_QUERY = 'Latest "AI Agents" Research paper in PDF'
TARGET_RESULTS = 10
EXCEL_FILENAME = "ai_research_results_pdf.xlsx"

# --- SETUP & DEPENDENCIES ---
def check_dependencies():
    """Ensures FFmpeg is present in the current folder."""
    current_dir = os.getcwd()
    ffmpeg_path = os.path.join(current_dir, "ffmpeg.exe")
    
    if not os.path.exists(ffmpeg_path):
        print("CRITICAL ERROR: 'ffmpeg.exe' not found in this folder.")
        exit()
    
    # Configure Pydub to use our local FFmpeg
    AudioSegment.converter = ffmpeg_path
    return current_dir

def get_driver():
    """Launches Undetected Chrome with anti-hang fixes."""
    print("Launching Browser...")
    options = uc.ChromeOptions()
    # use_subprocess=True fixes the 'hanging' issue on startup
    return uc.Chrome(options=options, use_subprocess=True)

# --- CAPTCHA SOLVER ENGINE ---
def solve_audio_challenge(driver, current_dir):
    """Handles the Google Audio Captcha loop until solved."""
    print("--- Solving Captcha (Auto-Retry Mode) ---")
    
    while True:
        time.sleep(2)
        driver.switch_to.default_content()
        
        # 1. Find the Challenge Frame
        challenge_frame = None
        for frame in driver.find_elements(By.TAG_NAME, "iframe"):
            if "bframe" in frame.get_attribute("src") or "recaptcha" in frame.get_attribute("title"):
                challenge_frame = frame
                break
        
        # If no challenge frame exists, we are done!
        if not challenge_frame:
            print("SUCCESS: Captcha solved or gone.")
            return True

        driver.switch_to.frame(challenge_frame)

        try:
            # 2. Click Audio Button (if visible)
            try:
                WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.ID, "recaptcha-audio-button"))).click()
                time.sleep(2)
            except: pass

            # 3. Download Audio
            print("Getting audio...")
            try:
                src = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "audio-source"))).get_attribute("src")
            except:
                print("Audio missing. Reloading...")
                driver.find_element(By.ID, "recaptcha-reload-button").click()
                continue 

            mp3_path = os.path.join(current_dir, "audio.mp3")
            wav_path = os.path.join(current_dir, "audio.wav")
            
            # Use cookies to prevent download blocks
            cookies = {c['name']: c['value'] for c in driver.get_cookies()}
            with open(mp3_path, "wb") as f:
                f.write(requests.get(src, cookies=cookies).content)

            # 4. Convert & Transcribe
            try:
                AudioSegment.from_mp3(mp3_path).export(wav_path, format="wav")
            except:
                continue # Bad download, retry

            recognizer = sr.Recognizer()
            with sr.AudioFile(wav_path) as source:
                recognizer.adjust_for_ambient_noise(source)
                try:
                    text = recognizer.recognize_google(recognizer.record(source))
                    print(f"Decoded: '{text}'")
                except:
                    print("Audio garbled. Reloading...")
                    driver.find_element(By.ID, "recaptcha-reload-button").click()
                    continue

            # 5. Submit
            input_box = driver.find_element(By.ID, "audio-response")
            input_box.clear()
            input_box.send_keys(text.lower())
            time.sleep(1)
            driver.find_element(By.ID, "recaptcha-verify-button").click()
            time.sleep(3)

            # 6. Verify Success
            driver.switch_to.default_content()
            if len(driver.find_elements(By.XPATH, "//iframe[contains(@src,'bframe')]")) == 0:
                return True
            
        except Exception as e:
            # If anything crashes inside the loop, just reload and try again
            driver.switch_to.default_content()
            continue

# --- MAIN LOGIC ---
def main():
    current_dir = check_dependencies()
    driver = get_driver()
    
    # Excel Setup
    wb = Workbook()
    ws = wb.active
    ws.append(["Title", "Link"])

    # Start Search
    driver.get(f"https://www.google.com/search?q={SEARCH_QUERY}")
    time.sleep(3)

    results_count = 0
    page = 1

    while results_count < TARGET_RESULTS:
        print(f"--- Processing Page {page} ---")

        # 1. Check for Captcha
        if "sorry/index" in driver.current_url or len(driver.find_elements(By.CSS_SELECTOR, "iframe[src*='recaptcha']")) > 0:
            print("CAPTCHA Found!")
            # Try to click the checkbox first
            try:
                for frame in driver.find_elements(By.TAG_NAME, "iframe"):
                    if "anchor" in frame.get_attribute("src"):
                        driver.switch_to.frame(frame)
                        WebDriverWait(driver, 4).until(EC.element_to_be_clickable((By.ID, "recaptcha-anchor"))).click()
                        driver.switch_to.default_content()
                        time.sleep(3)
                        break
            except: pass
            
            # Run Solver
            solve_audio_challenge(driver, current_dir)

        # 2. Scrape Results (Broad Strategy)
        headers = driver.find_elements(By.TAG_NAME, "h3")
        for h3 in headers:
            if results_count >= TARGET_RESULTS: break
            
            try:
                # Get parent <a> tag from the <h3> title
                parent_link = h3.find_element(By.XPATH, "./..")
                title = h3.text
                link = parent_link.get_attribute("href")

                if title and link and "http" in link:
                    ws.append([title, link])
                    results_count += 1
                    print(f"[{results_count}/{TARGET_RESULTS}] SAVED: {title[:40]}...")
            except:
                continue

        # 3. Next Page Logic
        if results_count >= TARGET_RESULTS:
            print("Target reached.")
            break

        try:
            next_btn = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "pnnext")))
            driver.execute_script("arguments[0].scrollIntoView();", next_btn)
            next_btn.click()
            page += 1
            time.sleep(random.uniform(3, 5))
        except:
            print("No more pages.")
            break

    # Cleanup
    wb.save(EXCEL_FILENAME)
    print(f"Done! Saved {results_count} links to '{EXCEL_FILENAME}'")
    driver.quit()

if __name__ == "__main__":
    main()