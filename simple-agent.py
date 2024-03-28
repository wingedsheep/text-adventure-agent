import json

from openai import OpenAI
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

with open("settings.json") as f:
    settings = json.load(f)
    api_key = settings["openrouter"]["apiKey"]

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

# Game interaction service
class GameInteractionService:
    def __init__(self):
        self.driver = webdriver.Chrome()  # Assumes Chrome WebDriver is installed
        self.driver.get("https://eblong.com/zarf/zweb/dreamhold/")

    def get_game_output(self):
        # Wait for the parchment element to be present
        parchment_element = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, 'parchment'))
        )

        content_element = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, 'content'))
        )

        parchment_html = content_element.get_attribute('outerHTML')

        soup = BeautifulSoup(parchment_html, 'html.parser')
        content_element = soup.find('div', id='content')

        # Find all elements with class 'finished-input'
        finished_inputs = soup.find_all(class_='finished-input')

        if not finished_inputs:  # If there are no 'finished-input' elements
            result_text = soup.get_text(separator=' ', strip=True)
        else:
            # Select the last 'finished-input' element
            last_finished_input = finished_inputs[-1]

            # Navigate to the parent of the last 'finished-input' element
            parent_element = last_finished_input.parent

            # Initialize an empty list to collect texts
            texts_after_last_input = []

            # Get next siblings of the parent of the last 'finished-input' element
            for sibling in parent_element.find_next_siblings():
                texts_after_last_input.append(sibling.get_text(separator=' ', strip=True))

            result_text = ' '.join(texts_after_last_input)

        return result_text.strip()

    def send_command(self, command):
        input_element = self.driver.find_element(By.XPATH, "//input[@class='fg-default bg-default z-roman']")
        input_element.clear()
        input_element.send_keys(command)
        input_element.submit()

    def close(self):
        self.driver.quit()

# Game playing unit
class GamePlayingUnit:
    def __init__(self, game_interaction_service):
        self.game_interaction_service = game_interaction_service
        self.observation_command = []

    def play(self):
        while True:
            game_output = self.game_interaction_service.get_game_output()
            print(f"Game Output: {game_output}")

            # Add the observation and command to the list
            self.observation_command.append((game_output, None))

            # Convert all the observations and commands to a string
            observation_command_str = ""
            for i, (observation, command) in enumerate(self.observation_command):
                observation_command_str += f"Observation {i + 1}: {observation}\n"
                observation_command_str += f"Command {i + 1}: {command}\n"

            # Use OpenAI API to generate the next command
            prompt = f"""
            You are an AI agent playing a text adventure game called "Dreamhold".
            Your goal is to explore the game world, solve puzzles, and uncover the mysteries of the Dreamhold.
            You get rewarded with points for progressing in the game.

            Here are your observations and commands so far:
            {observation_command_str}
            
            Instructions:
            - Try not to repeat the same commands, if they don't work.
            - If you get stuck, try something new.
            
            Possible Commands:
            - "look" or "l": Look around the room -- repeat the description of everything you see.
            - "examine [thing]" or "x [thing]": Look more closely at something -- learn more about it.
            - "inventory" or "i": List everything you're carrying.
            - "north", "south", "east", "west", or their abbreviations "n", "s", "e", "w": Walk in the specified direction.
            - "help [command]": Get help information for a specific command.
            - "quit": Quit the game.

            Generate the next command to progress in the game. Output only the command.
            """

            response = client.chat.completions.create(
                model="anthropic/claude-3-sonnet:beta",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            reply = response.choices[0].message.content

            print("Next Command: ", reply)

            # Extract the next command from Claude-3's reply
            command = reply.strip()

            # Add the command to the list
            self.observation_command[-1] = (game_output, command)

            # Execute the command
            self.game_interaction_service.send_command(command)

# Main program
if __name__ == "__main__":
    game_interaction_service = GameInteractionService()
    game_playing_unit = GamePlayingUnit(game_interaction_service)
    game_playing_unit.play()
