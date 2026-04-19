import pyautogui
import time
import random

# Fail-safe: Moving mouse to any corner kills the script
pyautogui.FAILSAFE = True

def human_click(x, y, offset=5):
    """
    Clicks at (x, y) with a small random offset.
    """
    target_x = x + random.randint(-offset, offset)
    target_y = y + random.randint(-offset, offset)
    
    # Slight move duration to look less robotic
    duration = random.uniform(0.1, 0.3)
    pyautogui.moveTo(target_x, target_y, duration=duration, tween=pyautogui.easeOutQuad)
    
    # Small pause before clicking
    time.sleep(random.uniform(0.05, 0.15))
    pyautogui.click()
    print(f"Clicked at ({target_x}, {target_y})")

def random_pause(min_sec=0.5, max_sec=1.5):
    """
    Sleeps for a random duration.
    """
    time.sleep(random.uniform(min_sec, max_sec))

if __name__ == "__main__":
    print("Mouse module loaded. Failsafe is ON (move mouse to corner to stop).")
