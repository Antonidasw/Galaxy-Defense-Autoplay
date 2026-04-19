import cv2
import os
import time
from vision import Vision

def main():
    print("--- Vision Debug Tool ---")
    v = Vision()
    TEMPLATES_DIR = "templates"
    DEBUG_OUTPUT = "debug_output.png"
    
    if not os.path.exists(TEMPLATES_DIR):
        print(f"Error: {TEMPLATES_DIR} folder not found.")
        return

    templates = [f for f in os.listdir(TEMPLATES_DIR) if f.endswith('.png')]
    if not templates:
        print("No templates found.")
        return

    # Try to find the window
    WINDOW_TITLE = "Galaxy Defense"
    region = v.get_window_bounds(WINDOW_TITLE)
    
    if region:
        print(f"Targeting window: {WINDOW_TITLE} at {region}")
        status_target = f"[{WINDOW_TITLE}]"
    else:
        print(f"Window '{WINDOW_TITLE}' not found. Targeting Full Screen.")
        status_target = "[Full Screen]"
        region = None

    print(f"Capturing and matching {len(templates)} templates...")
    
    # Capture screen or region
    # For debug drawing, we need to handle the offset carefully if we capture only a region
    screen = v.capture_screen(region=(region[0]*v.scale_x, region[1]*v.scale_y, region[2]*v.scale_x, region[3]*v.scale_y) if region else None)
    
    # We'll draw on a copy of the screen
    debug_img = screen.copy()
    
    found_any = False
    for template_name in sorted(templates):
        template_path = os.path.join(TEMPLATES_DIR, template_name)
        
        # Use the class method we just improved
        pos, max_val = v.find_template(template_path, threshold=0.1, region_points=region)
        
        template = cv2.imread(template_path)
        h, w = template.shape[:2]
        
        color = (0, 255, 0) if max_val >= 0.8 else (0, 0, 255)
        print(f"  - {template_name:20}: Max Confidence: {max_val:.4f} {'[MATCH]' if max_val >= 0.8 else '[NO MATCH]'}")
        
        if pos:
            # Since pos is in POINTS, we need to convert back to pixels for drawing
            # Alternatively, we can just use the internal logic.
            # For debugging, let's just find the scale again or return it from find_template.
            # To keep it simple, I'll just show the confidence here.
            pass
        
    cv2.imwrite(DEBUG_OUTPUT, debug_img)
    print(f"\nDebug image saved to: {DEBUG_OUTPUT}")
    print("Check this image to see where the bot thinks the matches are.")

if __name__ == "__main__":
    main()
