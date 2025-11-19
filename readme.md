# Dreamhold AI Agent

A modular AI agent that plays "The Dreamhold" text adventure using Selenium and an LLM. It features long-term memory through summarization and configurable reflection strategies.

## Quick Start

1. **Install Dependencies**
 
   ```bash
      pip install -r requirements.txt
   ```

2.  **Configure**
    Create `config/settings.json` (see example below).

3.  **Run**

    ```bash
    python main.py
    ```

## Configuration (`config/settings.json`)

The agent behavior is fully controlled here.

```json
{
  "api": {
    "base_url": "[https://openrouter.ai/api/v1](https://openrouter.ai/api/v1)",
    "key": "sk-YOUR-KEY",
    "model": "google/gemini-2.0-flash-001"
  },
  "game": {
    "url": "[https://eblong.com/zarf/zweb/dreamhold/](https://eblong.com/zarf/zweb/dreamhold/)",
    "headless": false
  },
  "agent": {
    "use_reflection": false,
    "memory_limit": 100
  }
}
```

  * **`use_reflection`**: `true` enables a strategic thinking step before every command. `false` (default) is faster but less analytical.
  * **`memory_limit`**: Number of turns to keep in raw text before triggering a **Summarization** event (compresses history into a narrative).

## Modules (`src/`)

  * **`engine.py`**: The brain. Manages the game loop, enforces memory limits, triggers summarization, and decides actions.
  * **`browser.py`**: The hands/eyes. Handles Selenium automation and HTML text extraction.
  * **`llm.py`**: The voice. Wraps the API connection to your chosen model.
  * **`prompts.py`**: The personality. Contains the system instructions for Commanding, Reflecting, and Summarizing.

## Logic Flow

1.  **Observe:** Scrape new text from the game window.
2.  **Memory Check:** If history \> `memory_limit`, compress recent turns into the `Global Summary`.
3.  **Reflect (Optional):** If enabled, ask the AI to analyze the situation explicitly.
4.  **Act:** Send the Context (Summary + Recent History + Reflection) to the AI to generate the next command.
