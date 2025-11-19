import time
import logging
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
