import logging
import requests

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self, config):
        # Note: We target the responses endpoint directly
        self.endpoint = "https://openrouter.ai/api/v1/responses"
        self.api_key = config["api"]["key"]
        self.model = config["api"]["model"]
        self.effort = config["api"].get("reasoning_effort", "low")

    def chat(self, system_prompt: str, user_context: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Construct payload for Responses API Beta
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

        try:
            response = requests.post(self.endpoint, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()

            final_text = ""

            # The Responses API returns a list of outputs (Reasoning blocks + Message blocks)
            if "output" in result:
                for item in result["output"]:

                    # 1. Handle Reasoning
                    if item.get("type") == "reasoning":
                        # Some models return a summary, some text, some encrypted content
                        # We try to grab whatever text is available
                        reasoning_content = ""

                        if "summary" in item and item["summary"]:
                            reasoning_content = "\n".join(item["summary"])
                        elif "content" in item:
                            # Sometimes raw content is here depending on model
                            reasoning_content = str(item["content"])

                        if reasoning_content:
                            logger.info(f"\n[AI REASONING]:\n{reasoning_content}\n{'-' * 20}")
                        else:
                            logger.info("\n[AI REASONING]: (Content encrypted or hidden by provider)")

                    # 2. Handle Final Message
                    elif item.get("type") == "message":
                        for content_part in item.get("content", []):
                            if content_part.get("type") == "output_text":
                                final_text += content_part.get("text", "")

            return final_text.strip()

        except Exception as e:
            logger.error(f"LLM API Error: {e}")
            if response:
                logger.error(f"Response Body: {response.text}")
            return ""
