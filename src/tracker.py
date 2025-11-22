import re
import json
import time
import logging
from typing import Set, List, Dict, Optional

logger = logging.getLogger(__name__)


class GameTracker:
    def __init__(self):
        self.start_time = time.time()
        self.steps = 0

        self.visited_rooms: Set[str] = set()

        # We track names seen in text to help identify WHICH masks we have,
        # but the authoritative count comes from the game score (X of 7).
        self.seen_mask_names: Set[str] = set()
        self.current_score = 0

        self.timeline: List[Dict] = []

        # Regex to catch "brown mask", "gold mask", etc.
        self.mask_pattern = re.compile(r"\b(?!(?:a|the|this|that|your)\b)(\w+)\s+mask\b", re.IGNORECASE)

    def update(self,
               room_name: str,
               score: int,
               observation: str,
               reasoning: str = "",
               command: str = ""):
        self.steps += 1

        # 1. Update Room
        if room_name and room_name != "Unknown":
            self.visited_rooms.add(room_name)

        # 2. Scan for Mask Names (passive collection)
        # We collect any mask name mentioned in the text so we have a list
        # available when the score eventually goes up.
        matches = self.mask_pattern.findall(observation)
        for mask_type in matches:
            self.seen_mask_names.add(mask_type.lower())

        self.current_score = score

        # 3. Record Snapshot (Log everything)
        self.timeline.append({
            "step": self.steps,
            "room": room_name,
            "score": self.current_score,
            "observation": observation,
            "reasoning": reasoning,
            "command": command,
            "known_mask_names": list(self.seen_mask_names)
        })

    def save_benchmark(self, filename="benchmark_data.json"):
        """Saves the session data to JSON."""
        duration = time.time() - self.start_time

        data = {
            "meta": {
                "total_steps": self.steps,
                "duration_seconds": round(duration, 2),
                "total_unique_rooms": len(self.visited_rooms),
                "final_score": self.current_score,
                "masks_seen": list(self.seen_mask_names)
            },
            "timeline": self.timeline
        }

        with open(filename, "w") as f:
            json.dump(data, f, indent=2)

        return data["meta"]
