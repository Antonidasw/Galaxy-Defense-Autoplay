import os
import json
import csv
from datetime import datetime

class DataLogger:
    def __init__(self, log_dir="data"):
        self.log_dir = log_dir
        self.history_file = os.path.join(log_dir, "history.csv")
        self.stats_file = os.path.join(log_dir, "stats.json")
        
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
            
        # Initialize CSV header if file doesn't exist
        if not os.path.exists(self.history_file):
            with open(self.history_file, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "mode", "outcome", "max_level", "duration"])

    def record_game(self, mode, outcome, max_level, duration=0):
        """
        Record a single game result.
        outcome: 'Win' or 'Loss'
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Append to CSV
        with open(self.history_file, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, mode, outcome, max_level, duration])
            
        self._update_stats(outcome, max_level)

    def _update_stats(self, outcome, max_level):
        """Update aggregate statistics in stats.json"""
        stats = self.get_stats()
        
        stats["total_games"] = stats.get("total_games", 0) + 1
        if outcome.lower() == "win":
            stats["wins"] = stats.get("wins", 0) + 1
        else:
            stats["losses"] = stats.get("losses", 0) + 1
            
        stats["win_rate"] = (stats["wins"] / stats["total_games"]) * 100
        stats["max_level_ever"] = max(stats.get("max_level_ever", 0), max_level)
        
        with open(self.stats_file, "w") as f:
            json.dump(stats, f, indent=4)

    def get_stats(self):
        if os.path.exists(self.stats_file):
            with open(self.stats_file, "r") as f:
                return json.load(f)
        return {"total_games": 0, "wins": 0, "losses": 0, "max_level_ever": 0, "win_rate": 0}

    def get_recent_history(self, limit=10):
        if not os.path.exists(self.history_file):
            return []
        
        history = []
        with open(self.history_file, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                history.append(row)
        
        return history[-limit:]
