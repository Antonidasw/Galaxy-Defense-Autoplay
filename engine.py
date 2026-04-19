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

    def _handle_in_game(self, region=None):
        """The main logic during battle"""
        # 1. State Check: ONLY manage weapons if 'Level Up' exists on screen
        anchor_path = os.path.join("templates", "anchor_level_up.png")
        if not os.path.exists(anchor_path):
            return
            
        pos, val = self.v.find_template(anchor_path, threshold=0.7, region_points=region)
        if pos:
            self.log("Level Up screen detected! Starting weapon selection...")
            self._manage_weapons(region=region)
        else:
            # We are in battle, stay idle
            pass

    def _manage_weapons(self, region=None):
        """Identifies weapon cards on screen and chooses based on 5-slot logic and ROI"""
        if not os.path.exists(self.templates_weapon_dir):
            return

        templates = [f for f in os.listdir(self.templates_weapon_dir) if f.endswith(".png")]
        
        # 1. Sync CURRENT weapons (Status Zone ROI)
        # We scan the top region to see what we actually have
        self.current_weapons = []
        for t_name in templates:
            weapon_name = t_name.split(".")[0]
            path = os.path.join(self.templates_weapon_dir, t_name)
            # Scan top 15%-35% of the window
            status_matches = self.v.find_all_matches(path, threshold=0.8, region_points=region, v_range=(0.15, 0.35))
            if status_matches:
                self.current_weapons.append(weapon_name)
        
        self.log(f"Synced owned weapons: {self.current_weapons}")

        # 2. Identify OFFERED weapons (Choice Zone ROI)
        offered_weapons = []
        for t_name in templates:
            weapon_name = t_name.split(".")[0]
            path = os.path.join(self.templates_weapon_dir, t_name)
            # Scan middle-bottom 40%-80% of the window
            choice_matches = self.v.find_all_matches(path, threshold=0.8, region_points=region, v_range=(0.40, 0.80))
            
            for pos, conf in choice_matches:
                is_elite = self.v.check_is_elite(pos)
                offered_weapons.append({
                    "name": weapon_name,
                    "pos": pos,
                    "is_elite": is_elite
                })

        if not offered_weapons:
            return

        # 3. Apply Decision Logic
        choice = None
        # Priority 1: Fill 5 slots
        if len(self.current_weapons) < 5:
            for w in offered_weapons:
                if w["name"] not in self.current_weapons:
                    choice = w
                    break
        
        # Priority 2: Best Upgrade
        if not choice:
            offered_weapons.sort(key=lambda x: x["is_elite"], reverse=True)
            for w in offered_weapons:
                if w["name"] in self.current_weapons:
                    choice = w
                    break
        
        if choice:
            self.log(f"Decision: Click {choice['name']} (Elite: {choice['is_elite']})")
            human_click(choice["pos"][0], choice["pos"][1])
            # Sleep for 3 seconds as requested to wait for UI transitions
            time.sleep(3)
            random_pause(0.5, 1.0)

    def _handle_result(self):
        # 1. Record win/loss
        # 2. Handle 'Stop on Failure'
        # 3. Close result window
        # 4. Increment cycle, loop back to LOBBY or stop
        pass
