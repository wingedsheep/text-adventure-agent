import json
import logging
import os
from src.engine import GameEngine
from src.browser import GameBrowser
from src.llm import LLMClient
from src.tracker import GameTracker

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
        raise FileNotFoundError(f"Config not found at: {config_path}")

    with open(config_path) as f:
        return json.load(f)


def main():
    try:
        config = load_config()

        # 1. Create Dependencies
        llm = LLMClient(config)
        browser = GameBrowser(config)
        tracker = GameTracker()

        # 2. Inject Dependencies into Engine
        engine = GameEngine(browser, llm, tracker, config)

        # 3. Run
        engine.run()

    except Exception as e:
        logger.critical(f"System Failure: {e}")


if __name__ == "__main__":
    main()
