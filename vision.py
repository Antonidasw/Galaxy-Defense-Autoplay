import cv2
import numpy as np
import os
import mss
import mss
import subprocess
from PIL import Image

class Vision:
    def __init__(self):
        # Determine the scale factor (Retina/5K systems)
        self.template_cache = {}
        self.global_retina_scale = None # We will auto-detect "1.0" or "0.5" natively
        with mss.mss() as sct:
            monitor = sct.monitors[1] # Primary monitor
            screenshot = np.array(sct.grab(monitor))
            
            pixel_w = screenshot.shape[1]
            pixel_h = screenshot.shape[0]
            
            # Use AppleScript to get screen size in points instead of pyautogui
            script = 'tell application "Finder" to get bounds of window of desktop'
            try:
                out = subprocess.check_output(["osascript", "-e", script], text=True).strip()
                clean_out = out.replace("{", "").replace("}", "").strip()
                parts = [p.strip() for p in clean_out.split(",")]
                screen_w = int(float(parts[2]))
                screen_h = int(float(parts[3]))
                
                if screen_w <= 0 or screen_h <= 0:
                    raise ValueError("Invalid screen dimensions")
                    
            except Exception as e:
                screen_w, screen_h = pixel_w, pixel_h
            
            # Since MSS on MacOS returns points (1x), we lock scale to 1.0 
            # to avoid scaling regions and misclicking.
            self.scale_x = 1.0
            self.scale_y = 1.0
            
            print(f"Detected screen scale factor: {self.scale_x:.2f}x, {self.scale_y:.2f}y")

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

    def get_region_px(self, region_points):
        """Converts points based region to pixel based region"""
        if not region_points:
            return None
        return [
            region_points[0] * self.scale_x,
            region_points[1] * self.scale_y,
            region_points[2] * self.scale_x,
            region_points[3] * self.scale_y
        ]

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

    def find_all_matches(self, template_path, threshold=0.8, region_points=None, v_range=None, screen_bgr=None):
        """
        Finds all occurrences of a template.
        v_range: Optional tuple (start_pct, end_pct) e.g. (0.1, 0.3) for vertical slice.
        Returns a list of ((x, y), confidence).
        """
        crop_offset_y_px = 0
        
        if screen_bgr is None:
            region_px = None
            if region_points:
                region_px = [
                    region_points[0] * self.scale_x,
                    region_points[1] * self.scale_y,
                    region_points[2] * self.scale_x,
                    region_points[3] * self.scale_y
                ]
            screen_bgr = self.capture_screen(region=region_px)

        # We apply v_range directly on the screen_bgr array!
        if v_range:
            h = screen_bgr.shape[0]
            start_y = int(h * v_range[0])
            end_y = int(h * v_range[1])
            screen_bgr = screen_bgr[start_y:end_y, :]
            crop_offset_y_px = start_y

        # Ensure we don't resize dynamically. Pre-cache both scales.
        if template_path not in self.template_cache:
            t = cv2.imread(template_path)
            if t is not None:
                t_50 = cv2.resize(t, (t.shape[1] // 2, t.shape[0] // 2))
                self.template_cache[template_path] = {'1.0': t, '0.5': t_50}
            else:
                self.template_cache[template_path] = None
        
        cache_entry = self.template_cache[template_path]
        if cache_entry is None: return []

        if self.global_retina_scale is None:
            # We don't know the exact screen scale yet, try both to figure it out
            t_10 = cache_entry['1.0']
            t_50 = cache_entry['0.5']
            
            max_10 = -1
            res_10 = None
            if t_10.shape[0] <= screen_bgr.shape[0] and t_10.shape[1] <= screen_bgr.shape[1]:
                res_10 = cv2.matchTemplate(screen_bgr, t_10, cv2.TM_CCOEFF_NORMED)
                max_10 = res_10.max()
                
            max_05 = -1
            res_05 = None
            if t_50.shape[0] <= screen_bgr.shape[0] and t_50.shape[1] <= screen_bgr.shape[1]:
                res_05 = cv2.matchTemplate(screen_bgr, t_50, cv2.TM_CCOEFF_NORMED)
                max_05 = res_05.max()
                
            # Lock the scale if confidence is high indicating a true positive match
            if max_10 > max_05 and max_10 >= threshold:
                self.global_retina_scale = '1.0'
            elif max_05 > max_10 and max_05 >= threshold:
                self.global_retina_scale = '0.5'
                
            if max_05 > max_10 and res_05 is not None:
                res = res_05
                template_used = t_50
                max_val = max_05
            else:
                res = res_10 if res_10 is not None else res_05
                template_used = t_10
                max_val = max_10 if max_10 != -1 else max_05
        else:
            # Fast Path! We already know the Mac's screen scale mismatch. Only execute 1 check!
            template_used = cache_entry[self.global_retina_scale]
            if template_used.shape[0] <= screen_bgr.shape[0] and template_used.shape[1] <= screen_bgr.shape[1]:
                res = cv2.matchTemplate(screen_bgr, template_used, cv2.TM_CCOEFF_NORMED)
                max_val = res.max()
            else:
                return []

        if max_val < threshold:
            return []

        h, w = template_used.shape[:2]
        
        # Debug trace to see what the max confidence is in reality
        if max_val > 0.5:  
            print(f"[DEBUG] {os.path.basename(template_path)} max confidence: {max_val:.3f}")
            
        loc = np.where(res >= threshold)
        
        # Deduplicate points that are very close to each other (NMS)
        matches = []
        added_pts = []
        min_dist = 10 # 10 pixels minimum distance between identical templates
        
        for pt in zip(*loc[::-1]):
            # Check distance against already added points
            is_new = True
            for exist_pt in added_pts:
                dist = ((exist_pt[0] - pt[0])**2 + (exist_pt[1] - pt[1])**2)**0.5
                if dist < min_dist:
                    is_new = False
                    break
                    
            if is_new:
                added_pts.append(pt)
                # pt represents coordinate in the cropped screen_bgr
                px_x = pt[0]
                px_y = pt[1] + crop_offset_y_px
                
                # Convert pixel back to display points
                rel_pt_x = px_x / self.scale_x
                rel_pt_y = px_y / self.scale_y
                
                abs_x = rel_pt_x + (region_points[0] if region_points else 0)
                abs_y = rel_pt_y + (region_points[1] if region_points else 0)
                
                # add half template size in points to click the center!
                abs_center_x = abs_x + ((w / 2) / self.scale_x)
                abs_center_y = abs_y + ((h / 2) / self.scale_y)
                
                matches.append(((int(abs_center_x), int(abs_center_y)), res[pt[1], pt[0]]))
            
        return matches

    def find_template(self, template_path, threshold=0.8, region_points=None, screen_bgr=None):
        """
        Finds the single best occurrence of a template.
        Returns ((x, y), confidence) or (None, 0.0)
        """
        matches = self.find_all_matches(template_path, threshold, region_points, screen_bgr=screen_bgr)
        if not matches:
            return None, 0.0
        
        # Sort by confidence
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[0]

    def check_is_elite(self, point_pt, radius=10):
        px_x = int(point_pt[0] * self.scale_x)
        px_y = int(point_pt[1] * self.scale_y)
        region = (px_x - radius, px_y - radius, radius * 2, radius * 2)
        img = self.capture_screen(region=region)
        if img is None: return False
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        lower_purple = np.array([125, 50, 50])
        upper_purple = np.array([155, 255, 255])
        mask = cv2.inRange(hsv, lower_purple, upper_purple)
        purple_ratio = np.sum(mask > 0) / (mask.shape[0] * mask.shape[1])
        return purple_ratio > 0.2

    def get_preview_qimage(self, region_points=None, width=400):
        """
        Captures the screen and returns a QImage for the GUI.
        """
        from PySide6.QtGui import QImage
        from PySide6.QtCore import Qt
        
        region_px = None
        if region_points:
            region_px = [
                region_points[0] * self.scale_x,
                region_points[1] * self.scale_y,
                region_points[2] * self.scale_x,
                region_points[3] * self.scale_y
            ]

        screen_bgr = self.capture_screen(region=region_px)
        if screen_bgr is None:
            return None
            
        height, width_orig, channels = screen_bgr.shape
        bytes_per_line = channels * width_orig
        screen_rgb = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2RGB)
        
        q_img = QImage(screen_rgb.data, width_orig, height, bytes_per_line, QImage.Format_RGB888)
        q_img_copy = q_img.copy() 
        return q_img_copy.scaledToWidth(width, Qt.SmoothTransformation)

if __name__ == "__main__":
    v = Vision()
    print("Vision initialized.")
