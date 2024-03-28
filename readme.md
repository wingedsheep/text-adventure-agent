# AI Text Adventure Player for The Dreamhold

This project is an AI agent designed to play the text adventure game "The Dreamhold" by interacting with the game's web interface using Selenium and leveraging the OpenAI API for natural language processing and decision-making.

## Overview

The AI agent is composed of several modules that work together to observe the game state, plan actions, execute commands, and reflect on the outcomes. The main components are:

1. **GameInteractionService**: This module handles the interaction with the game's web interface using Selenium. It retrieves the game output, sends commands, and captures the updated game state.

2. **ReflectionUnit**: This module analyzes the last command executed and its outcome, providing a concise reflection on whether the command was successful, any new information gained, and suggestions for future actions or strategies.

3. **StateUnit**: This module maintains and updates the game state based on the game output and observations. It keeps track of the current location, visited locations, inventory, progress, and additional notes.

4. **PlanningUnit**: This module generates an ordered list of actions (goals) based on the current game state and output. It prioritizes goals that are likely to lead to progress and score points, such as exploring new areas, interacting with objects, and solving puzzles.

5. **GamePlayingUnit**: This is the main orchestrator that brings all the other modules together. It manages the game loop, retrieves game output, updates the state, plans actions, executes commands, and reflects on the outcomes.

## How it Works

1. The `GamePlayingUnit` initializes the other modules and starts the game loop.
2. It retrieves the game output using the `GameInteractionService`.
3. The `StateUnit` analyzes the output and updates the game state accordingly.
4. The `PlanningUnit` generates an ordered list of actions based on the current game state.
5. The `GamePlayingUnit` uses the OpenAI API to generate the next command based on the first action in the list.
6. The command is executed by the `GameInteractionService`, and the game output is retrieved.
7. The `ReflectionUnit` analyzes the command and its outcome, providing a reflection to guide future actions.
8. The process repeats from step 2 until the game is completed or terminated.

## Setup

1. Clone the repository: `git clone https://github.com/your-username/ai-text-adventure-player.git`
2. Navigate to the project directory: `cd ai-text-adventure-player`
3. Install the required dependencies: `pip install -r requirements.txt`
4. Create an OpenRouter API key:
   - OpenRouter is a service that provides different language models with a single interface, making it easier to switch between them. It offers a Standardized API that allows you to use the same code with different models or providers.
   - To create an OpenRouter API key, visit https://openrouter.ai/ and sign up for an account.
5. Create a `settings.json` file in the project directory with your OpenAI API key:

```json
{
  "openrouter": {
    "apiKey": "YOUR_API_KEY"
  }
}
```

6. Run the main script: `python main.py` or `python simple-agent.py` (This will start the AI agent to play The Dreamhold)

## Dependencies

The project relies on the following Python libraries:

- `openai`: For accessing the OpenAI API
- `selenium`: For interacting with the game's web interface
- `beautifulsoup4`: For parsing HTML content

Make sure to install these dependencies before running the project.

## Notes

Somehow simple agent seems to be working better than the main agent. The main agent seems to get stuck more often.

## Contributing

Contributions to this project are welcome! If you find any issues or have suggestions for improvements, please open an issue or submit a pull request.