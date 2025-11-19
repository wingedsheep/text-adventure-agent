import json
import logging
import os
from src.engine import GameEngine
from src.browser import GameBrowser
from src.llm import LLMClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def load_config():
    # Get the folder containing main.py
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Build the absolute path to the config file
    config_path = os.path.join(base_dir, "config", "settings.json")

    if not os.path.exists(config_path):
        # Print the exact path python is trying to look at to help debug
        raise FileNotFoundError(f"Config not found at: {config_path}")

    with open(config_path) as f:
        return json.load(f)


def main():
    try:
        config = load_config()

        llm = LLMClient(config)
        browser = GameBrowser(config)

        # Pass full config to Engine now
        engine = GameEngine(browser, llm, config)
        engine.run()

    except Exception as e:
        logger.critical(f"System Failure: {e}")


if __name__ == "__main__":
    main()
