import time
import os
from vision import Vision
from mouse import human_click, random_pause
from data_logger import DataLogger

class AutomationEngine:
    def __init__(self, vision: Vision, logger: DataLogger, log_callback=None):
        self.v = vision
        self.logger = logger
        self.log_callback = log_callback
        self.running = False
        self.stop_on_fail = False
        self.loop_count = 0
        self.infinite_loop = False
        self.mode = "Normal" # "Normal" or "Elite"
        
        self.current_weapons = [] # List of weapon names owned in the 5 slots
        self.current_loop = 0
        
        self.state = "IDLE" # IDLE, LOBBY, PRE_GAME, IN_GAME, RESULT
        self.templates_weapon_dir = "templates/weapons"

    def log(self, text):
        print(text)
        if self.log_callback:
            self.log_callback(text)

    def set_settings(self, mode, loop_count, stop_on_fail, weapon_priorities):
        self.mode = mode
        self.loop_count = loop_count
        self.infinite_loop = (loop_count == -1)
        self.stop_on_fail = stop_on_fail
        self.weapon_priorities = weapon_priorities

    def start(self):
        self.running = True
        self.current_loop = 0
        self.state = "LOBBY"
        print(f"Engine started: Mode={self.mode}, Loops={self.loop_count}")

    def stop(self):
        self.running = False
        self.state = "IDLE"

    def run_one_cycle(self):
        """Main loop called by the GUI timer"""
        if not self.running:
            return

        if self.state == "LOBBY":
            self._handle_lobby()
        elif self.state == "PRE_GAME":
            self._handle_pre_game()
        elif self.state == "IN_GAME":
            self._handle_in_game()
        elif self.state == "RESULT":
            self._handle_result()

    def _handle_lobby(self):
        # 1. Scan for Ads/Popups/Paywalls
        self._skip_popups()
        
        # 2. Find Start/Battle button
        self.log("Lobby: Scanning for Battle button...")
        # if found: click it, self.state = "PRE_GAME"
        pass

    def _skip_popups(self):
        """Looks for 'X' buttons or 'Close' text to skip paywalls"""
        # Common 'X' or 'Close' templates would go here
        # For now, let's assume we look for any templates in 'templates/ui/close.png'
        pass

    def _handle_pre_game(self):
        # Select difficulty if needed
        # Select weapons if there is a menu
        self.state = "IN_GAME"
        pass

    def _handle_in_game(self):
        # The main logic during battle
        # 1. Look for weapon selection/upgrade offers
        self._manage_weapons()
        # 2. Check if battle ended (Victory/Defeat)
        pass

    def _manage_weapons(self):
        """Identifies weapon cards on screen and chooses based on 5-slot logic"""
        # Get all .png files in templates/weapons
        if not os.path.exists(self.templates_weapon_dir):
            return

        offered_weapons = [] # List of (name, pos, is_elite)
        
        templates = [f for f in os.listdir(self.templates_weapon_dir) if f.endswith(".png")]
        
        for t_name in templates:
            weapon_name = t_name.split(".")[0]
            path = os.path.join(self.templates_weapon_dir, t_name)
            matches = self.v.find_all_matches(path, threshold=0.8)
            
            for pos, conf in matches:
                is_elite = self.v.check_is_elite(pos)
                offered_weapons.append({
                    "name": weapon_name,
                    "pos": pos,
                    "is_elite": is_elite
                })

        if not offered_weapons:
            return

        # LOGIC:
        # 1. If < 5 weapons owned, prioritize picking a NEW weapon
        choice = None
        if len(self.current_weapons) < 5:
            for w in offered_weapons:
                if w["name"] not in self.current_weapons:
                    choice = w
                    break
        
        # 2. If no new weapon chosen (or already have 5), pick best upgrade
        if not choice:
            # Sort by Elite status first, then maybe priorities
            offered_weapons.sort(key=lambda x: x["is_elite"], reverse=True)
            for w in offered_weapons:
                if w["name"] in self.current_weapons:
                    choice = w
                    break
        
        if choice:
            print(f"Choosing weapon: {choice['name']} (Elite: {choice['is_elite']})")
            human_click(choice["pos"][0], choice["pos"][1])
            if choice["name"] not in self.current_weapons:
                self.current_weapons.append(choice["name"])
            random_pause(0.5, 1.0)

    def _handle_result(self):
        # 1. Record win/loss
        # 2. Handle 'Stop on Failure'
        # 3. Close result window
        # 4. Increment cycle, loop back to LOBBY or stop
        pass
