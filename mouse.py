import time
import random
import subprocess

# Try to import pyautogui, but provide a robust fallback for macOS
try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
    pyautogui.FAILSAFE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False

def human_click(x, y, offset=5):
    """
    Clicks at (x, y) with a small random offset.
    Uses AppleScript on Mac if pyautogui is missing.
    """
    target_x = x + random.randint(-offset, offset)
    target_y = y + random.randint(-offset, offset)
    
    if PYAUTOGUI_AVAILABLE:
        duration = random.uniform(0.1, 0.3)
        pyautogui.moveTo(target_x, target_y, duration=duration, tween=pyautogui.easeOutQuad)
        time.sleep(random.uniform(0.05, 0.15))
        pyautogui.click()
    else:
        # macOS Native Fallback using clics (or osascript for simple clicks)
        # Note: osascript 'click at' usually needs specific app threading, 
        # but the simplest way without extra tools is often a small shell command or AppleScript
        script = f'tell application "System Events" to click at {{{target_x}, {target_y}}}'
        try:
            # Popen throws the command to the OS in the background and returns INSTANTLY!
            subprocess.Popen(["osascript", "-e", script])
        except Exception as e:
            print(f"Error executing click via AppleScript: {e}")
            
    print(f"Clicked at ({target_x}, {target_y})")

def random_pause(min_sec=0.5, max_sec=1.5):
    time.sleep(random.uniform(min_sec, max_sec))

if __name__ == "__main__":
    print(f"Mouse module loaded. PyAutoGUI available: {PYAUTOGUI_AVAILABLE}")
