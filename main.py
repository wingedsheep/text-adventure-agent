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


class ReflectionUnit:
    def __init__(self):
        pass

    def get_reflection(self, game_state, observations_commands_reflections, game_output):
        observations_commands_reflections_str = "\n\n".join([str(ocr) for ocr in observations_commands_reflections])

        # Generate the prompt for Claude-3
        prompt = f"""
        You are the reflection unit of an AI agent playing a text adventure game called "Dreamhold". Your task is to reflect on the last command executed and its outcome, and provide a concise reflection.
        
        Game State:
        {game_state}

        Latest Observations, Commands, and Reflections:
        {observations_commands_reflections_str}
        
        Latest observation after the last command:
        {game_output}

        Instructions:
        - Analyze the last command executed and its outcome based on the game output and state.
        - Reflect on whether the command was successful in progressing towards the current goal or not.
        - Identify any new information or insights gained from the command's outcome.
        - Consider if the command led to any unexpected results or dead-ends.
        - Provide suggestions for future actions or strategies based on the reflection.
        - If the command resulted in repetition or no progress, suggest alternative approaches.
        - Keep the reflection concise and focused on key insights and actionable suggestions.
        - Be critical and constructive in your reflection to improve the AI agent's performance.
        - Exploration and experimentation are encouraged to find the most effective strategies.

        Reflection:
        """

        # Use OpenAI API to generate the reflection
        response = client.chat.completions.create(
            model="anthropic/claude-3-sonnet:beta",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Retry if response is NoneType (sometimes the API returns None)
        while response is None:
            response = client.chat.completions.create(
                model="anthropic/claude-3-sonnet:beta",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

        # Extract the reflection from the response
        self.reflection = response.choices[0].message.content.strip()
        return self.reflection


class StateUnit:
    def __init__(self):
        self.game_state = {}

    def update_state(self, observation_command_reflections):
        string_observation_command_reflections = "\n\n".join([str(ocr) for ocr in observation_command_reflections])
        # Generate the prompt for Claude-3
        prompt = f"""
        You are the state unit of an AI agent playing a text adventure game called "Dreamhold". Your task is to maintain and update the game state based on the game output.

        Latest observations, commands, and reflections:
        {string_observation_command_reflections}
        
        Current Game State:
        {self.game_state}

        Instructions:
        - Analyze the game output and extract relevant information to update the game state.
        - Take into account the current game state, and keep any existing information that is still valid and relevant.
        - Locations should include exits and where they lead, and notes that might be relevant. Only include exits that we know about.
          Keep track of all the locations visited so far. You can use this information to navigate back to previous locations.
        - Inventory should list all items the player is carrying, including their descriptions and any notes.
        - Progress should be a complete list of actions taken (successful or unsuccessful), puzzles solved, items collected, and any other relevant steps.
          It should be maintained in chronological order, and not pruned so that it can be used for reflection.
        - Notes should capture any additional information that doesn't fit into the other categories. They can include hints, clues, or observations that may be useful later.
        - Output should always be a valid JSON object.
        - Avoid duplicating information that is already present in the game state, and remove any outdated or irrelevant data.
        - Use the reflection to update the game state based on the insights gained from the last command executed, if useful.
        - Capture any additional observations in the notes section for future reference, such as:
          - Interesting things you noticed but couldn't interact with yet
          - Commands you tried but didn't work
          - Specific actions that led to scoring points
        - Update the game state in the following JSON format:
          {{
            "current_location": "location_name",
            "locations": {{
                "location1": {{
                    "notes": ["note1", "note2", ...],
                    "exits": ["north": {{ "leads_to": "location2", notes: ["note1", "note2", ...] }}, ...]
                }},
                ...
            }},
            "inventory": [
            {{
                "item": {{
                    "name": "item1",
                    "description": "description1",
                    "notes": ["note1", "note2", ...]
                }},
                ...
            }},
            "progress": [
              "progress1",
              "progress2",
              ...
            ],
            "points": integer_score,
            "notes": ["note1", "note2", ...]
          }}

        Updated Game State:
        """

        # Use OpenAI API to update the game state
        response = client.chat.completions.create(
            model="anthropic/claude-3-sonnet:beta",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Retry if response is NoneType (sometimes the API returns None)
        while response is None:
            response = client.chat.completions.create(
                model="anthropic/claude-3-sonnet:beta",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

        # Extract the updated game state from the response
        updated_state_json = response.choices[0].message.content.strip()
        self.game_state = updated_state_json

    def get_state(self):
        return self.game_state


class PlanningUnit:
    def __init__(self):
        self.action_list = []

    def update_plan(self, game_state, latest_observation_command_reflections):
        string_observation_command_reflections = "\n\n".join([str(ocr) for ocr in latest_observation_command_reflections])

        # Generate the prompt for Claude-3
        prompt = f"""
        You are the planning unit of an AI agent playing a text adventure game called "Dreamhold". Your goal is to generate an updated action list based on the current game state and output.

        Game mechanics: 
        
        ```
        These are the commands you will use most often.
        
        "look" or "l": Look around the room -- repeat the description of everything you see.
        "examine thing" or "x thing": Look more closely at something -- learn more about it.
        "inventory" or "i": List everything you're carrying.
        "north", "south", "east", "west", etc., or "n", "s", "e", "w", etc.: Walk in some direction.
        
        For more about these commands -- or any command used in this game -- type "help" followed by the command word. For example, "help look". You might want to start by looking at the help information for all of these basic commands.
        ```
            
        Latest observations, commands, and reflections:
        {string_observation_command_reflections}

        Current Game State:
        {self.format_game_state(game_state)}

        Current Action List:
        {self.format_action_list()}

        Instructions:
        - Analyze the current game state and generate an ordered list of commands that are likely to lead to progress and score points.
        - Consider the available actions, game mechanics, and any clues or objectives mentioned in the game.
        - Prioritize goals that explore new areas, interact with objects, and solve puzzles.
        - Take into account the current action list, see if any goals have been completed or are no longer relevant, and update the list accordingly.
        - Make sure the goals are specific, achievable, and contribute to the overall progress in the game.
        - Remove or edit any goals that are no longer relevant or have been completed.
        - Don't keep more than 3-5 goals in the list at a time to maintain focus and clarity.
        - Adjust the priority of goals based on the current game state and the progress made so far.
        - Don't repeat goals or actions that have already been attempted or completed, unless there is a specific reason to revisit them.
        - Use the reflection to see if any new goals or objectives can be added based on the insights gained from the last command executed.
        - Provide the list of goals in the following format:
          1. Goal 1
          2. Goal 2
          3. Goal 3
          ...

        Updated Action List:
        """

        # Use OpenAI API to generate the updated action list
        response = client.chat.completions.create(
            model="anthropic/claude-3-sonnet:beta",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Retry if response is NoneType (sometimes the API returns None)
        while response is None:
            response = client.chat.completions.create(
                model="anthropic/claude-3-sonnet:beta",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

        # Extract the updated action list from the response
        updated_action_list_text = response.choices[0].message.content.strip()
        self.action_list = updated_action_list_text.split("\n")

    def format_game_state(self, game_state):
        try:
            formatted_state = ""
            json_game_state = json.loads(game_state)
            for key, value in json_game_state.items():
                formatted_state += f"{key}: {value}\n"
            return formatted_state
        except json.JSONDecodeError:
            return game_state

    def format_action_list(self):
        if len(self.action_list) > 0:
            formatted_list = "\n".join(self.action_list)
            return f"\n{formatted_list}\n"
        else:
            return "No current action list."

    def get_next_action(self):
        if len(self.action_list) > 0:
            return self.action_list.pop(0)
        else:
            return None


class ObservationCommandReflection:
    def __init__(self, observation, command, reflection):
        self.observation = observation
        self.command = command
        self.reflection = reflection

    def __str__(self):
        return f"Observation: {self.observation}\nCommand: {self.command}\nReflection: {self.reflection}"


# Game playing unit
class GamePlayingUnit:
    def __init__(self, game_interaction_service, state_unit, planning_unit, reflection_unit):
        self.game_interaction_service = game_interaction_service
        self.state_unit = state_unit
        self.planning_unit = planning_unit
        self.reflection_unit = reflection_unit
        self.observation_command_reflections = []

    def play(self):
        while True:
            command = "Not yet chosen."
            reflection = "Not yet generated."

            game_output = self.game_interaction_service.get_game_output()
            print(f"Game Output: {game_output}")

            observation_command_reflection = ObservationCommandReflection(game_output, command, reflection)
            self.observation_command_reflections.append(observation_command_reflection)

            last_5_observation_command_reflections = self.observation_command_reflections[-5:]
            last_5_observation_command_reflections_str = "\n\n".join([str(ocr) for ocr in last_5_observation_command_reflections])

            self.state_unit.update_state(last_5_observation_command_reflections)
            game_state = self.state_unit.get_state()
            print(f"Updated game state: {self.planning_unit.format_game_state(game_state)}")

            self.planning_unit.update_plan(game_state, last_5_observation_command_reflections)
            action_list = self.planning_unit.format_action_list()
            print(f"Updated action list: {action_list}")

            # Use OpenAI API to generate the next command for the todo item
            prompt = f"""
            You are an AI agent playing a text adventure game called "Dreamhold". Your task is to generate the next command to accomplish the given todo item based on the current game state and output.
            
            Last 5 Observations, Commands, and Reflections:
            {last_5_observation_command_reflections_str}

            Here is the action list, you need to convert the first item in the list to a valid command:
            {action_list}

            Possible Commands:
            - "look" or "l": Look around the room -- repeat the description of everything you see.
            - "examine [thing]" or "x [thing]": Look more closely at something -- learn more about it.
            - "inventory" or "i": List everything you're carrying.
            - "north", "south", "east", "west", or their abbreviations "n", "s", "e", "w": Walk in the specified direction.
            - "help [command]": Get help information for a specific command.
            - "quit": Quit the game.

            Instructions:
            - Analyze the action list to determine the next action.
            - Generate a single valid command to progress towards accomplishing the first goal in the action list.
            - The command should be a single line of text, representing an action to take in the game.
            - Choose from the possible commands listed above or any other valid command you deem necessary.

            Next Command:
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
            observation_command_reflection.command = command

            # Execute the command
            self.game_interaction_service.send_command(command)

            # Reflect on the command and its outcome
            game_output = self.game_interaction_service.get_game_output()
            reflection = self.reflection_unit.get_reflection(game_state, last_5_observation_command_reflections, game_output)
            print(f"Reflection: {reflection}")
            observation_command_reflection.reflection = reflection


# Main program
if __name__ == "__main__":
    game_interaction_service = GameInteractionService()
    state_unit = StateUnit()
    planning_unit = PlanningUnit()
    reflection_unit = ReflectionUnit()
    game_playing_unit = GamePlayingUnit(game_interaction_service, state_unit, planning_unit, reflection_unit)
    game_playing_unit.play()
