import os
import time
from vision import Vision
from mouse import human_click, random_pause
from data_logger import DataLogger

class AutomationEngine:
    def __init__(self, vision: Vision, logger: DataLogger, log_callback=None, on_stop_callback=None):
        self.v = vision
        self.logger = logger
        self.log_callback = log_callback
        self.on_stop_callback = on_stop_callback
        self.running = False
        self.stop_on_fail = False
        self.loop_count = 0
        self.infinite_loop = False
        self.mode = "Normal" # "Normal" or "Elite"
        
        self.current_weapons = [] # List of weapon names owned in the 5 slots
        self.current_loop = 0
        self.pause_until = 0 # Non-blocking sleep mechanism
        
        self.state = "IDLE" # IDLE, LOBBY, PRE_GAME, IN_GAME, RESULT
        self.templates_weapon_dir = "templates/weapons"

    def log(self, text):
        print(text)
        if self.log_callback:
            self.log_callback(text)

    def set_settings(self, mode, loop_count, stop_on_fail, priorities):
        self.mode = mode
        self.loop_count = loop_count
        self.infinite_loop = (loop_count == -1)
        self.stop_on_fail = stop_on_fail
        self.weapon_priorities = priorities

    def start(self):
        self.running = True
        self.current_loop = 0
        self.state = "LOBBY"
        
        # Cache region here so we don't spam AppleScript 2 times a second!
        self.cached_region = self.v.get_window_bounds("Galaxy Defense")
        self.log(f"Window bounds cached: {self.cached_region}")
        print(f"Engine started: Mode={self.mode}, Loops={self.loop_count}")

    def stop(self):
        self.running = False
        self.state = "IDLE"
        if self.on_stop_callback:
            self.on_stop_callback()

    def run_one_cycle(self):
        """Main loop called by the GUI timer"""
        if not self.running:
            return
            
        # Non-blocking pause
        if time.time() < self.pause_until:
            return

        region = getattr(self, "cached_region", None)

        if self.state == "LOBBY":
            self._handle_lobby(region)
        elif self.state == "PRE_GAME":
            self._handle_pre_game(region)
        elif self.state == "IN_GAME":
            self._handle_in_game(region)
        elif self.state == "RESULT":
            self._handle_result()

    def _handle_lobby(self, region=None):
        # 1. Scan for Ads/Popups/Paywalls
        self._skip_popups(region)
        
        # 2. Find Start/Battle button
        battle_path = os.path.join("templates", "battle_btn.png")
        if os.path.exists(battle_path):
            pos, val = self.v.find_template(battle_path, threshold=0.9, region_points=region)
            if pos:
                self.log("Battle button found! Clicking...")
                human_click(pos[0], pos[1])
                self.pause_until = time.time() + 2 # wait 2 sec
                self.state = "PRE_GAME"
            else:
                self.log("Lobby: Scanning for Battle button...")
        else:
            self.log("Warning: 'battle_btn.png' not found in templates folder!")
            self.stop()

    def _skip_popups(self, region):
        """Looks for 'X' buttons or 'Close' text to skip paywalls"""
        # Common 'X' or 'Close' templates would go here
        # For now, let's assume we look for any templates in 'templates/ui/close.png'
        pass

    def _handle_pre_game(self, region=None):
        """
        State between clicking battle in lobby and actually fighting.
        We just wait a bit and transition to IN_GAME to start scanning for Level Up/Extra Chance.
        """
        self.log("Transitioning to Battle field...")
        self.pause_until = time.time() + 2
        self.state = "IN_GAME"

    def _handle_in_game(self, region=None):
        """The main logic during battle"""
        # Master screen capture to do all checks instantly!
        region_px = self.v.get_region_px(region)
        master_screen = self.v.capture_screen(region_px)
        
        # 1. Check for Result (Defeat/Victory)
        if self._check_result(region, master_screen):
            return

        # 2. Check for Extra Chance
        extra_path = os.path.join("templates", "anchor_extra_chance.png")
        if os.path.exists(extra_path) and self.v.find_template(extra_path, threshold=0.9, region_points=region, screen_bgr=master_screen)[0]:
            self._handle_extra_chance(region, master_screen)
            return

        # 3. Check for Level Up
        anchor_path = os.path.join("templates", "anchor_level_up.png")
        if os.path.exists(anchor_path) and self.v.find_template(anchor_path, threshold=0.9, region_points=region, screen_bgr=master_screen)[0]:
            self.log("Level Up screen detected! Starting weapon selection...")
            self._manage_weapons(region=region, pre_captured_screen=master_screen)
            return

    def _check_result(self, region, screen_bgr=None):
        defeat_path = os.path.join("templates", "defeat.png")
        perfect_path = os.path.join("templates", "perfect_clear.png")
        victory_path = os.path.join("templates", "victory.png")
        
        # Check Defeat
        if os.path.exists(defeat_path) and self.v.find_template(defeat_path, threshold=0.9, region_points=region, screen_bgr=screen_bgr)[0]:
            self.log("Game Over: Defeat detected.")
            self.logger.record_game(self.mode, "Loss", 0)
            
            if self.stop_on_fail:
                self.log("Stopping bot as 'Stop on Failure' is enabled.")
                self.stop()
                return True
                
            self._handle_cycle_end(region)
            return True
            
        # Check Victory
        v_found = os.path.exists(victory_path) and self.v.find_template(victory_path, threshold=0.9, region_points=region, screen_bgr=screen_bgr)[0]
        p_found = os.path.exists(perfect_path) and self.v.find_template(perfect_path, threshold=0.9, region_points=region, screen_bgr=screen_bgr)[0]
        
        if v_found or p_found:
            self.log("Victory/Perfect Clear detected!")
            self.logger.record_game(self.mode, "Win", 0)
            self._handle_cycle_end(region)
            return True
            
        return False

    def _handle_cycle_end(self, region):
        """Helper to increment loop and check if we should stop"""
        if not self.infinite_loop:
            self.current_loop += 1
            if self.current_loop >= self.loop_count:
                self.log(f"Completed {self.loop_count} loops. Stopping.")
                self.stop()
                return
                
        self._click_back_button(region)
        self.state = "LOBBY"

    def _click_back_button(self, region):
        back_path = os.path.join("templates", "back_btn.png")
        if os.path.exists(back_path):
            pos, val = self.v.find_template(back_path, threshold=0.9, region_points=region)
            if pos:
                self.log("Clicking Back button...")
                human_click(pos[0], pos[1])
                self.pause_until = time.time() + 2

    def _handle_extra_chance(self, region, screen_bgr=None):
        self.log("Handling Extra Chance...")
        claim_path = os.path.join("templates", "claim_btn.png")
        if os.path.exists(claim_path):
            c_pos, c_val = self.v.find_template(claim_path, threshold=0.9, region_points=region, screen_bgr=screen_bgr)
            if c_pos:
                self.log("Claim button found. Clicking!")
                human_click(c_pos[0], c_pos[1])
                self.pause_until = time.time() + 2
                return

        card_back = os.path.join("templates", "extra_card_back.png")
        if os.path.exists(card_back):
            card_pos, card_val = self.v.find_template(card_back, threshold=0.9, region_points=region, screen_bgr=screen_bgr)
            if card_pos:
                self.log("Flipping card.")
                human_click(card_pos[0], card_pos[1])
                self.pause_until = time.time() + 2

    def _manage_weapons(self, region=None, pre_captured_screen=None):
        """Identifies weapon cards on screen and chooses based on 5-slot logic and ROI"""
        if not os.path.exists(self.templates_weapon_dir):
            return

        templates = [f for f in os.listdir(self.templates_weapon_dir) if f.endswith(".png")]
        
        # PRE-CAPTURE the screen ONCE so we don't take 40 screenshots!
        master_screen_bgr = pre_captured_screen
        if master_screen_bgr is None:
            region_px = self.v.get_region_px(region)
            master_screen_bgr = self.v.capture_screen(region=region_px)
        
        # 1. Sync CURRENT weapons (Status Zone ROI)
        # We scan the top region to see what we actually have
        self.current_weapons = []
        for t_name in templates:
            weapon_name = t_name.split(".")[0]
            path = os.path.join(self.templates_weapon_dir, t_name)
            # Scan top 15%-35% of the window
            status_matches = self.v.find_all_matches(
                path, threshold=0.9, region_points=region, v_range=(0.15, 0.35), screen_bgr=master_screen_bgr
            )
            if status_matches:
                if weapon_name not in self.current_weapons:
                    self.current_weapons.append(weapon_name)
        
        self.log(f"Synced owned weapons: {self.current_weapons}")

        # 2. Identify OFFERED weapons (Choice Zone ROI)
        offered_weapons = []
        for t_name in templates:
            weapon_name = t_name.split(".")[0]
            path = os.path.join(self.templates_weapon_dir, t_name)
            # Scan middle-bottom 40%-80% of the window
            choice_matches = self.v.find_all_matches(
                path, threshold=0.9, region_points=region, v_range=(0.40, 0.80), screen_bgr=master_screen_bgr
            )
            
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
        
        # Priority 2: Best Upgrade (Using user priorities + Elite status)
        if not choice:
            def get_priority(name):
                try:
                    return self.weapon_priorities.index(name)
                except ValueError:
                    return 999 # Lowest priority if not in list
                    
            # Sort by Elite status first, then by User Priority List ranking
            offered_weapons.sort(key=lambda x: (not x["is_elite"], get_priority(x["name"])))
            
            for w in offered_weapons:
                if w["name"] in self.current_weapons:
                    choice = w
                    break
        
        if choice:
            self.log(f"Decision: Click {choice['name']} (Elite: {choice['is_elite']})")
            human_click(choice["pos"][0], choice["pos"][1])
            # Sleep mechanism via state engine instead of thread blocking
            self.pause_until = time.time() + 3 + 0.5 # 3.5 sec equivalent

    def _handle_result(self):
        # Migrated to _check_result inside _handle_in_game
        pass
