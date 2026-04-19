import cv2
import numpy as np
import mss
import pyautogui
import subprocess
from PIL import Image

class Vision:
    def __init__(self):
        # Determine the scale factor (Retina/5K systems)
        # pyautogui.size() returns points
        # mss screenshot returns actual pixels
        with mss.mss() as sct:
            monitor = sct.monitors[1] # Primary monitor
            screenshot = np.array(sct.grab(monitor))
            
            screen_w, screen_h = pyautogui.size()
            pixel_w = screenshot.shape[1]
            pixel_h = screenshot.shape[0]
            
            self.scale_x = pixel_w / screen_w
            self.scale_y = pixel_h / screen_h
            
            # Usually scale is 2.0 on Mac Retina/5K
            print(f"Detected screen scale factor: {self.scale_x}x, {self.scale_y}y")

    def get_window_bounds(self, window_name):
        """
        Uses AppleScript to find the bounds of a window by title.
        Returns (x, y, w, h) in POINTS, or None.
        """
        script = f'''
        tell application "System Events"
            try
                set winList to windows of (first process whose name contains "{window_name}" or title of every window contains "{window_name}")
                set win to item 1 of winList
                set pos to position of win
                set siz to size of win
                return (item 1 of pos) & "," & (item 2 of pos) & "," & (item 1 of siz) & "," & (item 2 of siz)
            on error
                return "NOT_FOUND"
            end try
        end tell
        '''
        try:
            output = subprocess.check_output(["osascript", "-e", script], text=True).strip()
            if output == "NOT_FOUND" or not output:
                return None
            parts = [int(float(p)) for p in output.split(",")]
            return tuple(parts) # (x, y, w, h)
        except Exception as e:
            print(f"Error finding window '{window_name}': {e}")
            return None

    def capture_screen(self, region=None):
        """
        Captures a region of the screen.
        region: (x, y, w, h) in PIXELS. If None, captures primary monitor.
        """
        with mss.mss() as sct:
            if region:
                monitor = {
                    "top": int(region[1]),
                    "left": int(region[0]),
                    "width": int(region[2]),
                    "height": int(region[3])
                }
            else:
                monitor = sct.monitors[1]
                
            sct_img = sct.grab(monitor)
            # Convert to OpenCV format (BGRA -> BGR)
            img = np.array(sct_img)
            return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    def find_all_matches(self, template_path, threshold=0.8, region_points=None):
        """
        Finds all occurrences of a template.
        Returns a list of ((x, y), confidence).
        """
        region_px = None
        if region_points:
            region_px = (
                region_points[0] * self.scale_x,
                region_points[1] * self.scale_y,
                region_points[2] * self.scale_x,
                region_points[3] * self.scale_y
            )

        screen_bgr = self.capture_screen(region=region_px)
        template = cv2.imread(template_path)
        if template is None:
            return []

        h, w = template.shape[:2]
        # For simplicity in 'find_all', we use scale 1.0 for now, 
        # but we can iterate if needed.
        res = cv2.matchTemplate(screen_bgr, template, cv2.TM_CCOEFF_NORMED)
        loc = np.where(res >= threshold)
        
        matches = []
        for pt in zip(*loc[::-1]):
            # Calculate center in points
            rel_center_pt_x = (pt[0] + w // 2) / self.scale_x
            rel_center_pt_y = (pt[1] + h // 2) / self.scale_y
            
            abs_center_x = rel_center_pt_x + (region_points[0] if region_points else 0)
            abs_center_y = rel_center_pt_y + (region_points[1] if region_points else 0)
            
            matches.append(((int(abs_center_x), int(abs_center_y)), res[pt[1], pt[0]]))
            
        return matches

    def check_is_elite(self, point_pt, radius=10):
        """
        Check if the color at a specific point (in points) indicates an 'Elite' weapon.
        Elite colors are usually Purple/Gold.
        """
        px_x = int(point_pt[0] * self.scale_x)
        px_y = int(point_pt[1] * self.scale_y)
        
        # Capture a small area around the point
        region = (px_x - radius, px_y - radius, radius * 2, radius * 2)
        img = self.capture_screen(region=region)
        
        if img is None: return False
        
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # Define 'Elite' color range (Purple: 125-155, Gold: 20-30 in OpenCV HSV)
        # We look for a significant amount of these colors
        lower_purple = np.array([125, 50, 50])
        upper_purple = np.array([155, 255, 255])
        
        mask = cv2.inRange(hsv, lower_purple, upper_purple)
        purple_ratio = np.sum(mask > 0) / (mask.shape[0] * mask.shape[1])
        
        return purple_ratio > 0.2 # If 20% of the area is purple, it's elite

if __name__ == "__main__":
    v = Vision()
    print("Vision initialized.")
