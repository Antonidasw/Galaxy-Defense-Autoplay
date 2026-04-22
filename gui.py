import sys
import time
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QCheckBox, 
                             QComboBox, QSpinBox, QTextEdit, QFrame, QListWidget,
                             QListWidgetItem, QProgressBar)
from PySide6.QtCore import Qt, QTimer, QSize, QThread, Signal
from PySide6.QtGui import QFont, QColor, QPalette, QPixmap

from vision import Vision
from engine import AutomationEngine
from data_logger import DataLogger

class EngineWorker(QThread):
    log_sig = Signal(str)
    stop_sig = Signal()

    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        # safely route cross-thread callbacks to GUI signals
        self.engine.log_callback = self.log_sig.emit
        self.engine.on_stop_callback = self.stop_sig.emit
        self._active = True

    def run(self):
        while self._active:
            self.engine.run_one_cycle()
            time.sleep(0.05) # 50ms engine tick speed

    def terminate_worker(self):
        self._active = False
        self.wait()

class GalaxyDefenseGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Galaxy Defense Autoplay - Pro")
        self.setMinimumSize(900, 600)
        
        # Initialize Backend
        self.vision = Vision()
        self.logger = DataLogger()
        self.engine = AutomationEngine(self.vision, self.logger)
        
        # Threading wrapper
        self.worker = EngineWorker(self.engine)
        self.worker.log_sig.connect(self.log)
        self.worker.stop_sig.connect(self._on_engine_stopped)
        self.worker.start() # Start background loop
        
        self._init_ui()
        self._apply_styles()
        
        # Timer for UI Stats alone (does not block)
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_stats)
        self.timer.start(500) 
        
        self.preview_timer = QTimer()
        self.preview_timer.timeout.connect(self._update_preview)
        self.preview_timer.start(200) # 5 FPS preview

    def closeEvent(self, event):
        self.worker.terminate_worker()
        super().closeEvent(event)

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # --- LEFT SIDEBAR (Status & Stats) ---
        sidebar = QVBoxLayout()
        stats_frame = QFrame()
        stats_frame.setFrameShape(QFrame.StyledPanel)
        stats_layout = QVBoxLayout(stats_frame)
        
        self.status_label = QLabel("Status: IDLE")
        self.status_label.setStyleSheet("font-weight: bold; color: #ffcc00;")
        
        self.win_rate_label = QLabel("Win Rate: 0%")
        self.total_games_label = QLabel("Total Games: 0")
        
        # --- PREVIEW AREA ---
        self.preview_label = QLabel("Live Preview Not Available")
        self.preview_label.setFixedSize(200, 260)
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("background-color: #000; border: 2px solid #333; color: #555;")
        
        stats_layout.addWidget(QLabel("DASHBOARD"))
        stats_layout.addWidget(self.status_label)
        stats_layout.addWidget(self.total_games_label)
        stats_layout.addWidget(self.win_rate_label)
        stats_layout.addWidget(QLabel("LIVE VIEW:"))
        stats_layout.addWidget(self.preview_label)
        stats_layout.addStretch()
        
        sidebar.addWidget(stats_frame)
        
        # --- CENTER AREA (Settings) ---
        settings_panel = QVBoxLayout()
        
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Game Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Normal", "Elite"])
        mode_layout.addWidget(self.mode_combo)
        
        loop_layout = QHBoxLayout()
        loop_layout.addWidget(QLabel("Loop Cycles:"))
        self.loop_spin = QSpinBox()
        self.loop_spin.setRange(-1, 999) # -1 for infinite
        self.loop_spin.setValue(10)
        loop_layout.addWidget(self.loop_spin)
        loop_layout.addWidget(QLabel("(-1 = Non-stop)"))
        
        self.fail_check = QCheckBox("Stop on Game Failure")
        self.fail_check.setChecked(True)
        
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("START BOT")
        self.start_btn.setFixedHeight(50)
        self.start_btn.clicked.connect(self.start_bot)
        
        self.stop_btn = QPushButton("STOP")
        self.stop_btn.setFixedHeight(50)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_bot)
        
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        
        # Logs
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setPlaceholderText("Logs will appear here...")
        
        settings_panel.addLayout(mode_layout)
        settings_panel.addLayout(loop_layout)
        settings_panel.addWidget(self.fail_check)
        settings_panel.addLayout(btn_layout)
        settings_panel.addWidget(QLabel("LOGS:"))
        settings_panel.addWidget(self.console)
        
        # --- RIGHT SIDE (Weapon Priorities) ---
        priority_panel = QVBoxLayout()
        priority_panel.addWidget(QLabel("WEAPON PRIORITY"))
        self.weapon_list = QListWidget()
        # Mock weapons (user will add templates)
        for w in ["Railgun", "Thunder_Bolt", "Flame_Thrower", "Laser_Turret"]:
            item = QListWidgetItem(w)
            self.weapon_list.addItem(item)
        
        priority_panel.addWidget(self.weapon_list)
        priority_panel.addWidget(QLabel("Drag items to prioritize"))
        
        # Add all segments to main layout
        main_layout.addLayout(sidebar, 1)
        main_layout.addLayout(settings_panel, 3)
        main_layout.addLayout(priority_panel, 1)

    def _apply_styles(self):
        # Premium Dark Theme
        self.setStyleSheet("""
            QMainWindow { background-color: #121212; color: #e0e0e0; }
            QLabel { color: #bdbdbd; font-size: 14px; }
            QPushButton { 
                background-color: #333333; 
                border: 1px solid #555555; 
                padding: 10px; 
                border-radius: 5px; 
                color: white; 
                font-weight: bold;
            }
            QPushButton:hover { background-color: #444444; border-color: #0078d4; }
            QPushButton#start_btn { background-color: #1b5e20; }
            QPushButton#start_btn:hover { background-color: #2e7d32; }
            QTextEdit { background-color: #1e1e1e; border: 1px solid #333333; color: #76ff03; font-family: 'Courier New'; }
            QFrame { border: 1px solid #333333; border-radius: 10px; background-color: #1e1e1e; }
            QComboBox, QSpinBox { background-color: #333333; border: 1px solid #555555; color: white; padding: 5px; }
        """)

    def start_bot(self):
        self.log("Initializing automation...")
        settings = {
            "mode": self.mode_combo.currentText(),
            "loop_count": self.loop_spin.value(),
            "stop_on_fail": self.fail_check.isChecked(),
            "priorities": [self.weapon_list.item(i).text() for i in range(self.weapon_list.count())]
        }
        self.engine.set_settings(**settings)
        self.engine.start()
        
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_label.setText("Status: RUNNING")
        self.status_label.setStyleSheet("color: #00e676; font-weight: bold;")

    def stop_bot(self):
        self.engine.stop()
        self.log("Bot stopped manually by user.")

    def _on_engine_stopped(self):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Status: STOPPED / FINISHED")
        self.status_label.setStyleSheet("color: #f44336; font-weight: bold;")

    def _update_stats(self):
        """Update general UI stats efficiently"""
        stats = self.logger.get_stats()
        self.win_rate_label.setText(f"Win Rate: {stats['win_rate']:.1f}%")
        self.total_games_label.setText(f"Total Games: {stats['total_games']}")

    def _update_preview(self):
        """Refresh the screenshot preview in the sidebar"""
        # Find window bounds ONCE to prevent AppleScript from completely freezing GUI event thread
        if not hasattr(self, '_cached_preview_region'):
            self._cached_preview_region = self.vision.get_window_bounds("Galaxy Defense")
            
        # Prefer the freshly locked engine bounds, fallback to the GUI one-time bounds
        region = getattr(self.engine, "cached_region", None)
        if region is None:
            region = self._cached_preview_region
            
        q_img = self.vision.get_preview_qimage(region_points=region, width=200)
        if q_img:
            self.preview_label.setPixmap(QPixmap.fromImage(q_img))
        else:
            self.preview_label.setText("Window Not Found")

    def log(self, message):
        timestamp = time.strftime("[%H:%M:%S]")
        self.console.append(f"{timestamp} {message}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GalaxyDefenseGUI()
    window.show()
    sys.exit(app.exec())
