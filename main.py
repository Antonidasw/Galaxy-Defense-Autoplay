import os
import time
import sys
from vision import Vision
from mouse import human_click, random_pause

# Configuration
TEMPLATES_DIR = "templates"
CONFIDENCE_THRESHOLD = 0.7
LOOP_DELAY = 1.0 # Seconds between screen scans
WINDOW_TITLE = "Galaxy Defense" # Exact or partial title of your game window

def main():
    print("--- Galaxy Defense Bot Starting ---")
    print(f"Watch out: Failsafe is active. Move mouse to screen corner to emergency stop.")
    
    v = Vision()
    
    # Check if templates directory exists
    if not os.path.exists(TEMPLATES_DIR):
        os.makedirs(TEMPLATES_DIR)
        print(f"Created '{TEMPLATES_DIR}' folder. Please put your .png screenshots there.")
        return

    print("Bot is running. Scanning for templates...")
    
    spinner = ["|", "/", "-", "\\"]
    spinner_idx = 0
    
    try:
        while True:
            # Refresh list of templates
            templates = [f for f in os.listdir(TEMPLATES_DIR) if f.endswith('.png')]
            
            # Find window every loop in case it moves or is closed/reopened
            region = v.get_window_bounds(WINDOW_TITLE)
            
            if region:
                status_window = f"Target: [{WINDOW_TITLE}]"
            else:
                status_window = "Target: [Full Screen] (Window not found)"
                region = None

            found_anything = False
            best_match = ("", 0.0) # To show what it saw if nothing matches
            
            for template_name in sorted(templates):
                template_path = os.path.join(TEMPLATES_DIR, template_name)
                
                pos, val = v.find_template(template_path, threshold=CONFIDENCE_THRESHOLD, region_points=region)
                
                if val > best_match[1]:
                    best_match = (template_name, val)
                
                if pos:
                    print(f"\nMATCH: Found {template_name} (Confidence: {val:.2f}) at {pos}")
                    human_click(pos[0], pos[1])
                    found_anything = True
                    
                    # Wait for the template to disappear before continuing 
                    # (Prevents double-clicking due to lag or animations)
                    print(f"Waiting for {template_name} to disappear...", end="\r")
                    timeout = 5.0
                    start_wait = time.time()
                    while time.time() - start_wait < timeout:
                        # Scan again to see current confidence
                        _, check_val = v.find_template(template_path, threshold=CONFIDENCE_THRESHOLD, region_points=region)
                        if check_val < CONFIDENCE_THRESHOLD:
                            print(f"\n{template_name} disappeared. Resuming...           ")
                            break
                        time.sleep(0.5)
                    
                    # Short additional pause for state transition
                    random_pause(0.5, 1.0)
                    break 
                
            if not found_anything:
                char = spinner[spinner_idx % len(spinner)]
                spinner_idx += 1
                # Show what it's looking at and the best it found
                print(f" {char} Scanning... {status_window} Best: {best_match[0]} ({best_match[1]:.2f})    ", end="\r")
                sys.stdout.flush()
            
            time.sleep(LOOP_DELAY)
            
    except KeyboardInterrupt:
        print("\nBot stopped by user.")

if __name__ == "__main__":
    main()
