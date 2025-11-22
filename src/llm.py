import logging
import time
import requests

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self, config):
        self.endpoint = "https://openrouter.ai/api/v1/responses"
        self.api_key = config["api"]["key"]
        self.model = config["api"]["model"]
        self.effort = config["api"].get("reasoning_effort", "low")
        # Configurable retry settings
        self.max_retries = 3
        self.retry_delay = 5  # seconds

    def chat(self, system_prompt: str, user_context: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "reasoning": {
                "effort": self.effort
            },
            "input": [
                {
                    "type": "message",
                    "role": "system",
                    "content": [{"type": "input_text", "text": system_prompt}]
                },
                {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": user_context}]
                }
            ]
        }

        # Retry Logic
        for attempt in range(1, self.max_retries + 1):
            response = None  # Initialize here to prevent UnboundLocalError
            try:
                response = requests.post(self.endpoint, headers=headers, json=payload, timeout=30)
                response.raise_for_status()
                result = response.json()

                final_text = ""

                if "output" in result:
                    for item in result["output"]:
                        # 1. Handle Reasoning logging
                        if item.get("type") == "reasoning":
                            reasoning_content = ""
                            if "summary" in item and item["summary"]:
                                reasoning_content = "\n".join(item["summary"])
                            elif "content" in item:
                                reasoning_content = str(item["content"])

                            if reasoning_content:
                                logger.info(f"\n[AI REASONING]:\n{reasoning_content}\n{'-' * 20}")

                        # 2. Handle Final Message extraction
                        elif item.get("type") == "message":
                            for content_part in item.get("content", []):
                                if content_part.get("type") == "output_text":
                                    final_text += content_part.get("text", "")

                return final_text.strip()

            except Exception as e:
                logger.error(f"LLM API Attempt {attempt}/{self.max_retries} Failed: {e}")

                # Only try to log response text if we actually got a response object
                if response is not None:
                    try:
                        logger.error(f"Response Text: {response.text}")
                    except:
                        pass

                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
                else:
                    logger.error("Max retries reached. Returning fallback.")
                    return ""  # Return empty string to signal failure

        return ""
