import time
import logging
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)


class GameBrowser:
    def __init__(self, config):
        self.url = config["game"]["url"]
        options = Options()
        if config["game"].get("headless"):
            options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=options)

    def start(self):
        logger.info(f"Opening {self.url}")
        self.driver.get(self.url)
        # Wait for initial load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, 'parchment'))
        )

    def get_game_state(self) -> dict:
        """
        Scrapes the 'top-window' (Status Line) for the authoritative
        Room Name and Score.
        Returns: {'room': str, 'score': int}
        """
        state = {"room": "Unknown", "score": 0}

        try:
            # The status line is usually in a div with id='top-window'
            # Example Text: " Mountain Pool             1 of 7 "
            top_window = self.driver.find_elements(By.ID, "top-window")

            if top_window:
                raw_text = top_window[0].text.strip()

                # Regex to extract "Room Name" and "X of 7"
                # Matches: Any text (Group 1), followed by spaces, then a digit (Group 2), then "of 7"
                match = re.search(r"^(.*?)\s+(\d+)\s+of\s+7", raw_text)

                if match:
                    state["room"] = match.group(1).strip()
                    state["score"] = int(match.group(2))
                else:
                    # Fallback: If no score pattern, just take the text as the room name
                    # (Common during the intro screen)
                    if raw_text:
                        state["room"] = raw_text

            # Fallback: If top-window is empty, check main content for bold headers
            if state["room"] == "Unknown":
                content_div = self.driver.find_element(By.ID, "content")
                bolds = content_div.find_elements(By.CLASS_NAME, "z-bold")
                if bolds:
                    state["room"] = bolds[-1].text.strip()

        except Exception as e:
            # Fail gracefully so the agent keeps running even if stats are missing
            pass

        return state

    def get_observation(self) -> str:
        """Extracts only the new text from the game interface."""
        try:
            # Wait for content to update/exist
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'content'))
            )

            html = self.driver.find_element(By.ID, 'content').get_attribute('outerHTML')
            soup = BeautifulSoup(html, 'html.parser')

            # Logic to find text occurring after the last player command
            finished_inputs = soup.find_all(class_='finished-input')

            if not finished_inputs:
                return soup.get_text(separator=' ', strip=True)

            last_input = finished_inputs[-1]
            texts = []
            # Get all siblings after the last input
            for sibling in last_input.parent.find_next_siblings():
                texts.append(sibling.get_text(separator=' ', strip=True))

            return ' '.join(texts).strip()
        except Exception as e:
            logger.error(f"Browser Error: {e}")
            return "Error extracting game text."

    def send_command(self, command: str):
        """Types command into the game input field."""
        try:
            input_field = self.driver.find_element(By.XPATH, "//input[contains(@class, 'z-roman')]")
            input_field.clear()
            input_field.send_keys(command)
            input_field.submit()
            time.sleep(1.5)  # Wait for game to render response
        except Exception as e:
            logger.error(f"Input Error: {e}")

    def close(self):
        self.driver.quit()
