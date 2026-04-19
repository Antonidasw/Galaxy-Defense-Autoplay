import pyautogui
import mss
import numpy as np

def verify_scale():
    print("--- Mac Display Scale Verification ---")
    
    # PyAutoGUI size (Points)
    screen_w, screen_h = pyautogui.size()
    print(f"PyAutoGUI Screen Size (Points): {screen_w} x {screen_h}")
    
    # MSS size (Pixels)
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        sct_img = sct.grab(monitor)
        pixel_w = sct_img.width
        pixel_h = sct_img.height
        print(f"MSS Screen Size (Pixels): {pixel_w} x {pixel_h}")
        
    scale_x = pixel_w / screen_w
    scale_y = pixel_h / screen_h
    
    print(f"Detected Scale Factor: {scale_x:.2f}x (Width), {scale_y:.2f}x (Height)")
    
    # Current mouse position
    mx, my = pyautogui.position()
    print(f"Current Mouse Position (Points): ({mx}, {my})")
    print(f"Expected Pixel Position: ({mx * scale_x}, {my * scale_y})")
    
    if scale_x > 1.1:
        print("\nSUCCESS: Retina/High-DPI scaling detected and accounted for.")
    else:
        print("\nINFO: Standard DPI scaling (1.0x).")

if __name__ == "__main__":
    verify_scale()
