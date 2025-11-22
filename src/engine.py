import logging
import time
from typing import List, Dict
from .browser import GameBrowser
from .llm import LLMClient
from .tracker import GameTracker
from .prompts import REFLECTION_PROMPT, COMMAND_PROMPT, SUMMARY_PROMPT

logger = logging.getLogger(__name__)


class GameEngine:
    def __init__(self, browser: GameBrowser, llm: LLMClient, tracker: GameTracker, config: dict):
        self.browser = browser
        self.llm = llm
        self.tracker = tracker

        # Agent Settings
        agent_conf = config.get("agent", {})
        self.memory_limit = agent_conf.get("memory_limit", 100)
        self.use_reflection = agent_conf.get("use_reflection", False)

        self.history: List[Dict[str, str]] = []
        self.global_summary = "The game has just started."

    def _get_context(self) -> str:
        """Combines global summary and recent history for the LLM."""
        history_text = ""
        for i, t in enumerate(self.history, 1):
            ref_str = f"\nRef: {t['ref']}" if t['ref'] else ""
            history_text += f"Turn {i}:\nObs: {t['obs']}{ref_str}\nCmd: {t['cmd']}\n"

        return f"PREVIOUS GAME SUMMARY:\n{self.global_summary}\n\nRECENT HISTORY:\n{history_text}"

    def _summarize(self):
        """Compresses history into the global summary."""
        try:
            logger.info(">> Triggering Memory Summarization...")
            context = self._get_context()
            new_summary = self.llm.chat(SUMMARY_PROMPT, context)

            if new_summary:
                self.global_summary = new_summary
                self.history = []  # Clear buffer
                logger.info(f">> Memory Updated. New Summary Length: {len(new_summary)} chars")
        except Exception as e:
            logger.error(f"Summarization failed (skipping): {e}")

    def run(self):
        self.browser.start()
        try:
            turn_count = 0
            while True:
                turn_count += 1

                # 1. Check Memory Limit
                if len(self.history) >= self.memory_limit:
                    self._summarize()

                # 2. Observe
                obs = self.browser.get_observation()
                game_state = self.browser.get_game_state()

                # Log status to console (for the user to see progress)
                logger.info(f"\n--- Turn {turn_count} [Rm: {game_state['room']} | Score: {game_state['score']}/7] ---")
                logger.info(f"Observation: {obs[:150]}...")

                full_context = self._get_context() + f"\n\nCurrent Observation: {obs}"

                # 3. Reflect (Optional)
                reflection = ""
                cmd_context = full_context

                if self.use_reflection:
                    reflection = self.llm.chat(REFLECTION_PROMPT, full_context)
                    if reflection:
                        logger.info(f"Reflection: {reflection}")
                        cmd_context += f"\nReflection: {reflection}"
                    else:
                        logger.warning("Reflection failed, proceeding without it.")

                # 4. Act
                command = self.llm.chat(COMMAND_PROMPT, cmd_context)

                # Failsafe for empty command
                if not command:
                    logger.warning("LLM failed to generate command. Defaulting to 'wait'.")
                    command = "wait"

                # Clean command
                command = command.replace('"', '').replace("'", "").strip()
                logger.info(f"Command: {command}")

                # --- 4.5 UPDATE TRACKER (Save Obs, Reason, Command) ---
                self.tracker.update(
                    room_name=game_state["room"],
                    score=game_state["score"],
                    observation=obs,
                    reasoning=reflection,
                    command=command
                )
                # -----------------------------------------------------

                if command.lower() in ["quit", "exit"]:
                    break

                # 5. Execute & Store
                self.browser.send_command(command)
                self.history.append({
                    "obs": obs,
                    "ref": reflection,
                    "cmd": command
                })

        except KeyboardInterrupt:
            logger.info("Game stopped by user.")
        except Exception as e:
            logger.critical(f"Unexpected Engine Error: {e}")
        finally:
            meta = self.tracker.save_benchmark()
            logger.info(f"Benchmark Saved: {meta}")
            self.browser.close()
