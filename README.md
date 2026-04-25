# Galaxy Defense Autoplay

An intelligent, vision-based automated bot for the game **Galaxy Defense**. Designed to automatically manage repetitive tasks, battle navigation, and weapon upgrades with a high-performance decoupled GUI.

## 🌟 Version 0.1 Prototype Features

- **High-Performance Vision Engine**: Uses OpenCV template matching to read the screen in real-time, operating efficiently at a 50ms tick rate without freezing the UI.
- **Multithreaded Architecture**: The automation loop runs independently in a background thread, while PySide6 ensures a buttery smooth dashboard experience.
- **Smart Level & Difficulty Scaling**: 
  - Automatically switches between **Normal** and **Elite** modes by checking inactive UI states.
  - Features an intelligent **Maximum Level** mode that auto-scales (tries higher levels upon winning, steps down upon losing) without relying on OCR.
- **Weapon Upgrade Logic**: Identifies offered weapon upgrades and auto-selects the best choice based on user priority and elite/normal status.
- **Auto-Correction & Failsafes**: Built-in visual verification retries clicks if animations lag, and global failsafes auto-correct the bot if it accidentally drops into the lobby during a game.

## 🛠️ Prerequisites & Setup

1. **Python 3.10+** is recommended.
2. Clone this repository and install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. **Template Preparation**:
   The bot relies on visual templates to "see" the game. Ensure the `templates/` folder contains your screenshots of UI elements (e.g., `battle_btn.png`, `mode_Normal_inactive.png`, `level_next.png`, etc.). 
   *Note: For mode switching, make sure you capture the INACTIVE text of the modes (i.e. take a screenshot of "Normal" while Elite is active).*

## 🚀 How to Run

Start the bot via the graphical interface:
```bash
python gui.py
```

### Dashboard Usage:
1. **Game Mode**: Select `Normal` or `Elite`.
2. **Level Mode**: 
   - `Current Level`: The bot will continuously play whichever level is currently selected on your screen.
   - `Maximum Level`: The bot will automatically scroll to your highest unlocked level, and dynamically step up/down based on your win/loss record.
3. Click **START BOT** and hover your mouse out of the way. 
4. *Failsafe*: Moving your mouse violently to any corner of the screen will trigger PyAutoGUI's failsafe and halt the bot.

## 🏗️ Architecture Notes
- `gui.py`: The frontend PySide6 dashboard.
- `engine.py`: The state machine handling Lobby, Pre-Game, In-Game, and Result states.
- `vision.py`: The robust retina-aware wrapper for `cv2.matchTemplate` and `mss` screen capturing.
- `mouse.py`: Handles cross-platform, non-blocking click executions (with AppleScript fallback for macOS).

---
*Created for automated stamina usage. Use responsibly!*
