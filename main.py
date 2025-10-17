# main.py (Final Version with Restrict Mode and Dual Notification Sound)

import sys
import winsound
import random
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QComboBox, QSpinBox, QCheckBox, QSlider,
    QMessageBox, QFrame, QStackedWidget, QSystemTrayIcon, QMenu
)
from PySide6.QtCore import Qt, QTimer, Slot, QSize, QRect, QTime, QThread, Signal
from PySide6.QtGui import QFont, QColor, QPalette, QGuiApplication, QFontMetrics, QIcon, QRegion, QPainterPath

try:
    import win32gui
    import win32con
    import win32api
except ImportError:
    print("ERROR: pywin32 not installed. Install with: pip install pywin32")
    sys.exit(1)


# --- APPLICATION CONSTANTS ---
FULLSCREEN_CHECK_INTERVAL_MS = 500
WINDOW_PUSH_DELAY_MS = 100
TRAY_NOTIFICATION_DURATION_MS = 5000
TOLERANCE_PIXELS = 10
NOTIFICATION_WINDOW_OPACITY_MIN = 0
NOTIFICATION_WINDOW_OPACITY_MAX = 100
NOTIFICATION_WINDOW_MIN_WIDTH = 280
NOTIFICATION_WINDOW_MAX_WIDTH = 800
HORIZONTAL_PADDING = 10 * 2 + 20
TITLE_BAR_HEIGHT = 30
SETTINGS_WINDOW_WIDTH = 450
TIMER_WINDOW_WIDTH = 380
TIMER_WINDOW_HEIGHT = 180
WINDOW_BORDER_RADIUS = 10

# ----------------------------------------------------------------------
# --- THEME AND COLOR DEFINITIONS ---
# ----------------------------------------------------------------------

# Define Theme color sets for easy switching
THEMES = {
    "Dark": {
        'BG': "#2c3e50",          # Dark Blue/Gray
        'FG': "#ecf0f1",          # Light Text
        'INPUT_BG': "#34495e",    # Title Bar/Input Background
        'ACCENT': "#3498db",      # Blue Accent (Short Break/Minimize)
        'RED': "#d8601b",         # Red Accent (Stop/Long Break)
        'GREEN': "#25ae60",       # Green Accent (Start/Work Time)
        'YELLOW': "#f39c12",      # Yellow Accent (Settings)
        'TEXT_ACCENT': "#bdc3c7", # Muted Text
    },
    "Light": {
        'BG': "#f0f0f0",          # Light Gray
        'FG': "#333333",          # Dark Text
        'INPUT_BG': "#e1e1e1",    # Title Bar/Input Background
        'ACCENT': "#9cbde7",      # Blue Accent
        'RED': "#d8601b",         # Red Accent
        'GREEN': "#25ae60",       # Green Accent
        'YELLOW': "#f39c12",      # Yellow Accent
        'TEXT_ACCENT': "#7f8c8d", # Muted Text
    },
    "System": None # Will use OS/Qt defaults
}

def get_windows_system_sounds():
    """Query available Windows system sounds from the registry."""
    import winreg
    
    sounds = {}
    
    try:
        # Open the Windows registry key for system sounds
        key_path = r"AppEvents\Schemes\Apps\.Default"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path)
        except WindowsError as e:
            print(f"Warning: Could not access registry for system sounds: {e}")
            return {
                "Exclamation": "SystemExclamation",
                "Critical Stop": "SystemHand",
                "Default Beep": "SystemDefault",
            }
        
        # Common system sounds that are likely to exist
        sound_names = [
            ("SystemExclamation", "Exclamation"),
            ("SystemHand", "Critical Stop"),
            ("SystemAsterisk", "Asterisk"),
            ("SystemQuestion", "Question"),
            ("SystemNotification", "Notification"),
            ("SystemDefault", "Default Beep"),
            (".Default", "Default"),
            ("SystemWelcome", "Windows Logon"),
            ("SystemExit", "Windows Logoff"),
            ("MailBeep", "New Mail Notification"),
            ("AppGPFault", "Program Error"),
            ("Close", "Close Program"),
            ("Maximize", "Maximize"),
            ("MenuCommand", "Menu Command"),
            ("MenuPopup", "Menu Popup"),
            ("Minimize", "Minimize"),
            ("Open", "Open Program"),
            ("RestoreDown", "Restore Down"),
            ("RestoreUp", "Restore Up"),
        ]
        
        # Try each sound and add it if it exists
        for alias, display_name in sound_names:
            try:
                # Try to open the sound's subkey
                sound_key = winreg.OpenKey(key, f"{alias}\\.Current")
                # If successful, add to our dictionary
                sounds[display_name] = alias
                winreg.CloseKey(sound_key)
            except WindowsError:
                # Sound doesn't exist, skip it
                pass
        
        winreg.CloseKey(key)
        
    except Exception as e:
        print(f"Error querying system sounds: {e}")
        # Return default sounds as fallback
        return {
            "Exclamation": "SystemExclamation",
            "Critical Stop": "SystemHand",
            "Default Beep": "SystemDefault",
        }
    
    # If no sounds found, return defaults
    if not sounds:
        sounds = {
            "Exclamation": "SystemExclamation",
            "Critical Stop": "SystemHand",
            "Default Beep": "SystemDefault",
        }
    
    return sounds


# ----------------------------------------------------------------------
# --- BREAK ADVICE LISTS ---
# ----------------------------------------------------------------------

BREAK_ADVICE = [
    "Stretch your arms and shoulders. Release that tension!",
    "Stand up and walk a few steps. Get the blood flowing.",
    "Blink rapidly for 10 seconds to moisten your eyes.",
    "Look out the window at a distant object.",
    "Gently massage your temples and neck to relieve strain.",
    "Close your eyes and focus on your breath.",
    "Grab a quick drink of water. Stay hydrated!"
]

LONG_BREAK_ADVICE = [
    "Get up and make a fresh cup of coffee or tea.",
    "Do a quick chore like loading the dishwasher. Get moving!",
    "Step outside for a few minutes of fresh air and sunlight.",
    "Do some light stretching. Focus on your back and legs.",
    "Listen to a favorite song or short podcast episode.",
    "Close your eyes and practice mindful breathing.",
    "Hydrate! Drink a full glass of water, and maybe grab a snack."
]


# ----------------------------------------------------------------------
# --- TIMER LOGIC CLASS (Integrated) ---
# ----------------------------------------------------------------------

class TimerLogic:
    SOUND_OPTIONS = get_windows_system_sounds()
    
    
    def __init__(self, settings):
        self.settings = settings
        self.reset()
        
    def reset(self):
        self.is_running = False
        self.is_short_break = False
        self.is_long_break = False
        self.work_cycle_count = 0
        self.current_seconds = self.settings['short_work_min'] * 60
        
    def start(self):
        self.is_running = True
        
    def stop(self):
        self.is_running = False
        
    def move_to_next_work_timer(self):
        """Moves to the next work timer while maintaining the current cycle count."""
        self.is_short_break = False
        self.is_long_break = False
        # Start the next work timer
        self.current_seconds = self.settings['short_work_min'] * 60
        # Note: work_cycle_count is already incremented when break started
        self.is_running = True
        
    def tick(self):
        if not self.is_running:
            return False
            
        self.current_seconds = max(0, self.current_seconds - 1)
        
        if self.current_seconds > 0:
            return False
            
        if self.is_break():
            self.end_break()
            return True # Phase switched: Break ended
        else:
            self.start_break()
            return True # Phase switched: Work ended, Break started
            
    def start_break(self):
        self.work_cycle_count += 1
        
        if self.work_cycle_count % self.settings['breaks_until_long'] == 0:
            self.is_long_break = True
            self.is_short_break = False
            self.current_seconds = self.settings['long_break_min'] * 60
        else:
            self.is_long_break = False
            self.is_short_break = True
            self.current_seconds = self.settings['short_break_sec']
            
    def end_break(self):
        self.is_short_break = False
        self.is_long_break = False
        self.current_seconds = self.settings['short_work_min'] * 60
        
    def is_break(self):
        return self.is_short_break or self.is_long_break
        
    def check_long_break_notify(self):
        # Long break notification is handled directly when the break starts
        return False

    def get_time_display(self):
        minutes = self.current_seconds // 60
        seconds = self.current_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    def get_phase_name(self):
        breaks_until_long = self.settings['breaks_until_long']
        current_cycle = (self.work_cycle_count % breaks_until_long) or breaks_until_long
        if self.is_long_break:
            return f"LONG BREAK (After {breaks_until_long} short breaks)"
        elif self.is_short_break:
            return f"SHORT BREAK ({current_cycle}/{breaks_until_long})"
        else:
            next_cycle = ((self.work_cycle_count + 1) % breaks_until_long) or breaks_until_long
            return f"WORK TIME (Break: {next_cycle}/{breaks_until_long})"
            
    def get_break_message(self):
        if self.is_long_break:
            return "LONG BREAK: Time to step away from your computer!"
        elif self.is_short_break:
            return "SHORT BREAK: Look 20 feet away for 20 seconds!"
        return "ERROR: Not in a break phase."


# ----------------------------------------------------------------------
# --- BREAK NOTIFICATION WINDOW (NON-MODAL FOR ALL BREAKS) ---
# ----------------------------------------------------------------------

class BreakNotificationWindow(QFrame):
    """
    Non-modal, passive display window for both short and long breaks (Live or Test).
    It is updated and dismissed externally by the TimerWidget.
    """
    def __init__(self, parent_widget, is_long_break, advice_message, 
                 initial_time_value, is_test_mode,
                 bg_color, text_color, opacity, position,
                 restrict_long_break, restrict_short_break, # NEW PARAMETERS
                 alarm_sound_alias=None, force_on_top=True, show_advice=True):
        super().__init__()
        self.setAttribute(Qt.WA_DeleteOnClose, True) # Ensure the window is deleted when closed
        self.parent_widget = parent_widget # TimerWidget instance
        self.is_long_break = is_long_break
        self.is_test = is_test_mode
        self.test_timer = None
        self.alarm_sound_alias = alarm_sound_alias
        self.show_advice = show_advice
        
        # NEW: Determine if the dismiss button should be restricted
        is_restricted = False
        if self.is_long_break and restrict_long_break:
            is_restricted = True
        elif not self.is_long_break and restrict_short_break: # It's a short break
            is_restricted = True
        
        # --- DYNAMIC SIZE CALCULATION FOR ADVICE ---
        advice_font = QFont("Arial", 14, QFont.Bold) 
        timer_font = QFont("Arial", 36, QFont.Bold)
        advice_metrics = QFontMetrics(advice_font)
        timer_metrics = QFontMetrics(timer_font)

        HORIZONTAL_PADDING = 10 * 2 + 20 

        # Calculate width based on whether advice is shown
        if show_advice:
            advice_width = advice_metrics.size(Qt.TextSingleLine, advice_message).width()
            new_width = max(NOTIFICATION_WINDOW_MIN_WIDTH, min(advice_width + HORIZONTAL_PADDING, NOTIFICATION_WINDOW_MAX_WIDTH))
            ADVICE_HEIGHT = advice_metrics.height()
        else:
            # When no advice, size based on button text if button exists
            if not is_restricted:
                button_font = QFont("Arial", 10, QFont.Bold)
                button_metrics = QFontMetrics(button_font)
                button_text_width = button_metrics.size(Qt.TextSingleLine, "Dismiss Notification").width()
                new_width = max(NOTIFICATION_WINDOW_MIN_WIDTH, button_text_width + HORIZONTAL_PADDING + 20)
            else:
                # No advice and no button - minimal width for timer only
                new_width = NOTIFICATION_WINDOW_MIN_WIDTH
            ADVICE_HEIGHT = 0

        TIMER_HEIGHT = timer_metrics.height()

        # Adjust height based on whether the button is shown
        BUTTON_HEIGHT = 40 if not is_restricted else 0 

        # Adjust spacing based on whether advice is shown
        ADVICE_SPACING = 5 if show_advice else 0

        VERTICAL_CONTENT_HEIGHT = ADVICE_HEIGHT + ADVICE_SPACING + TIMER_HEIGHT + 10 + BUTTON_HEIGHT
        new_height = VERTICAL_CONTENT_HEIGHT + 20

        self.setFixedSize(new_width, new_height) 
        
        # --- WINDOW SETUP ---
        # Initialize window_flags with base flags
        window_flags = (
            Qt.Window |                    # Base window flag
            Qt.FramelessWindowHint |       # No window frame
            Qt.Tool                        # Tool window (no taskbar entry)
        )

        if force_on_top:
            window_flags |= Qt.WindowStaysOnTopHint # Add the "on top" hint only if requested

        self.setWindowFlags(window_flags)

        # Store the force_on_top flag for later use
        self.force_on_top = force_on_top

        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)  # Don't steal focus
        
        # Calculate alpha channel value
        alpha = int(255 * (opacity / 100.0)) 
        qcolor = QColor(bg_color)
        transparent_bg_color = f"rgba({qcolor.red()}, {qcolor.green()}, {qcolor.blue()}, {alpha})"

        # Apply theme-based styling
        self.setStyleSheet(f"""
            QFrame {{ 
                background-color: {transparent_bg_color}; 
                border-radius: 10px;
                border: none;
            }}
            QLabel {{ 
                color: {text_color};
            }}
            QPushButton {{
                background-color: #f1c40f; /* Yellow */
                color: black;
                font-weight: bold;
                border: none;
                padding: 10px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: #e67e22; /* Darker Orange */
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5) 

        # Advice Label
        if self.show_advice:
            self.advice_label = QLabel(advice_message) # <-- Use self.advice_label for reference
            self.advice_label.setFont(advice_font) 
            self.advice_label.setAlignment(Qt.AlignCenter)
            self.advice_label.setWordWrap(True) # Use True for better wrapping
            
            # Advice text styling
            advice_font = QFont("Arial", 14)
            advice_font.setItalic(True)
            self.advice_label.setFont(advice_font)

            # Add advice label to the local layout
            layout.addWidget(self.advice_label) 
        
        # --- Time Logic Setup ---
        if self.is_test:
            # Test Mode: Use local countdown timer
            self.test_seconds_left = initial_time_value
            initial_display = self._format_test_time(self.test_seconds_left)
            
            self.test_timer = QTimer(self)
            self.test_timer.timeout.connect(self._test_tick)
            self.test_timer.start(1000)
        else:
            # Live Mode: Use string passed from main TimerLogic
            initial_display = initial_time_value
        
        # Time Label
        self.timer_label = QLabel(initial_display)
        self.timer_label.setFont(timer_font)
        self.timer_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.timer_label)
        
        layout.addSpacing(5) # Space before button

        # Dismiss Button (Only add if not restricted)
        if not is_restricted:
            self.dismiss_button = QPushButton("Dismiss Notification")
            # Calculate button width: full width minus margins if advice shown, or match content width if no advice
            button_width = new_width - 20
            self.dismiss_button.setFixedSize(button_width, 40)
            
            # Connect button to the external close handler
            self.dismiss_button.clicked.connect(self.parent_widget.close_notification_window)
            
            layout.addWidget(self.dismiss_button, alignment=Qt.AlignCenter)
        
        self._position_on_screen(position)
        self.show()

        # If not forcing on top, push window behind active window after a delay.
        if not self.force_on_top:
            self._push_behind_active_window()

    def _position_on_screen(self, position):
        """Positions the window on the primary screen based on the setting (Top/Center/Bottom)."""
        screen_geometry = QGuiApplication.primaryScreen().geometry()
        
        x = screen_geometry.x() + (screen_geometry.width() - self.width()) // 2
        
        if position == "Top":
            y = screen_geometry.y() + 50 # 50px offset from the top
        elif position == "Center":
            y = screen_geometry.y() + (screen_geometry.height() - self.height()) // 2
        elif position == "Bottom":
            y = screen_geometry.y() + screen_geometry.height() - self.height() - 50 # 50px offset from the bottom
        else: # Default to Center
            y = screen_geometry.y() + (screen_geometry.height() - self.height()) // 2
            
        self.move(x, y)
    
    def _push_behind_active_window(self):
        """Positions this window behind the currently active fullscreen window."""
        # Add delay to ensure window is fully rendered before repositioning
        QTimer.singleShot(WINDOW_PUSH_DELAY_MS, self._do_push_behind)

    def _do_push_behind(self):
        """ Actually push the window behind after the delay. """
        try:
            # First, verify the notification window still exists and is valid
            if not self or not self.isVisible():
                return
            
            # Get our window handle
            our_hwnd = int(self.winId())
            if not our_hwnd or our_hwnd == 0:
                print("Invalid window handle for notification window")
                return
            
            # Verify our window handle is still valid (belongs to a real window)
            if not win32gui.IsWindow(our_hwnd):
                print("Notification window no longer exists")
                return
            
            # Get the active (foreground) window
            active_hwnd = win32gui.GetForegroundWindow()
            if not active_hwnd:
                print("No foreground window found")
                return
            
            # Verify the active window is valid and not our own window
            if not win32gui.IsWindow(active_hwnd):
                print("Active window no longer exists")
                return
            
            if active_hwnd == our_hwnd:
                print("Active window is already our notification - skipping z-order change")
                return
            
            # Move our window behind the active window
            result = win32gui.SetWindowPos(
                our_hwnd,
                active_hwnd,  # Insert after this window (puts us behind it)
                0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE
            )
            
            if not result:
                print("SetWindowPos failed - window may have been closed")
                
        except AttributeError as e:
            # Window was deleted before this method ran
            print(f"Notification window was deleted before push-behind could complete: {e}")
        except Exception as e:
            print(f"Could not push window behind: {e}")

    def _format_test_time(self, seconds):
        """ Formats time according to test rules: MM:SS or XX (seconds only if < 60). """
        if seconds <= 0:
            return "0"
            
        if seconds < 60:
            return f"{seconds}" # Seconds only
        else:
            minutes = seconds // 60
            remaining_seconds = seconds % 60
            return f"{minutes:02d}:{remaining_seconds:02d}"

    @Slot()
    def _test_tick(self):
        """ Handles the countdown logic for test mode. """
        self.test_seconds_left -= 1
        
        if self.test_seconds_left >= 0:
            self.timer_label.setText(self._format_test_time(self.test_seconds_left))
        
        # CRITICAL CHANGE: Check if the test timer has completed and close the window
        if self.test_seconds_left <= 0:
            self.stop_test_timer()
            
            # Play the selected sound to indicate the test break is over (END SOUND for test)
            if self.alarm_sound_alias and self.parent_widget.main_window.settings['enable_sound']:
                # Use parent's play_alarm function for consistency and winsound wrapper
                self.parent_widget.main_window.play_alarm(self.alarm_sound_alias)
            else:
                # Fallback if sound is disabled or alias is missing
                winsound.PlaySound("SystemBeep", winsound.SND_ALIAS | winsound.SND_ASYNC) 
            
            # Auto-close the test notification when the timer reaches zero
            self.parent_widget.close_notification_window()

    def stop_test_timer(self):
        """ Stops the internal test timer if active. """
        if self.is_test and self.test_timer and self.test_timer.isActive():
            self.test_timer.stop()
    
    def closeEvent(self, event):
        """ Handle window close event properly. """
        self.stop_test_timer()
        super().closeEvent(event)

    @Slot()
    def update_time_display(self, time_string):
        """ Updates the time displayed on the notification window (used for LIVE breaks only). """
        if not self.is_test:
            self.timer_label.setText(time_string)
            
# --- FULLSCREEN DETECTION THREAD ---
class FullscreenMonitorThread(QThread):
    # Background thread that continuously monitors for fullscreen apps.
    fullscreen_detected = Signal(bool)  # Emits True when fullscreen detected
    
    def __init__(self):
        super().__init__()
        self.is_running = True
        self.last_fullscreen_state = False
        
    def run(self):
        # Continuously check for fullscreen apps in background.
        while self.is_running:
            try:
                current_state = self._check_fullscreen()
                
                # Only emit if state changed
                if current_state != self.last_fullscreen_state:
                    self.fullscreen_detected.emit(current_state)
                    self.last_fullscreen_state = current_state
            except Exception as e:
                print(f"Fullscreen detection error: {e}")
            
            self.msleep(FULLSCREEN_CHECK_INTERVAL_MS)
    
    def stop(self):
        # Stop the monitoring thread.
        self.is_running = False
        self.wait()
    
    def _check_fullscreen(self):
        # Check if active window is fullscreen.
        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return False

            if not win32gui.IsWindowVisible(hwnd):
                return False
            if win32gui.IsIconic(hwnd):
                return False

            rect = win32gui.GetWindowRect(hwnd)
            hmon = win32api.MonitorFromWindow(hwnd, win32con.MONITOR_DEFAULTTOPRIMARY)
            mon_info = win32api.GetMonitorInfo(hmon)
            mon_rect = mon_info["Monitor"]

            win_left, win_top, win_right, win_bottom = rect
            mon_left, mon_top, mon_right, mon_bottom = mon_rect

            win_width = win_right - win_left
            win_height = win_bottom - win_top
            mon_width = mon_right - mon_left
            mon_height = mon_bottom - mon_top

            is_fullscreen = (
                (abs(win_width - mon_width) <= TOLERANCE_PIXELS and
                abs(win_height - mon_height) <= TOLERANCE_PIXELS)
                or
                (abs(win_left - mon_left) <= TOLERANCE_PIXELS and
                abs(win_top - mon_top) <= TOLERANCE_PIXELS and
                abs(win_right - mon_right) <= TOLERANCE_PIXELS and
                abs(win_bottom - mon_bottom) <= TOLERANCE_PIXELS)
            )
            return is_fullscreen
        except Exception as e:
            print(f"Fullscreen check failed: {e}")
            return False

# ----------------------------------------------------------------------
# --- MAIN APPLICATION FRAME (The QMainWindow) ---
# ----------------------------------------------------------------------

class OpenEyeBreakApp(QMainWindow):
    # Placeholder color properties, will be set by apply_theme()
    BG, FG, INPUT_BG, ACCENT, RED, GREEN, YELLOW = [""] * 7 
    
    def __init__(self):
        super().__init__()
        
        # 1. Default Settings
        self.settings = {
            'short_work_min': 20,     
            'short_break_sec': 20,    
            'long_break_min': 5,      
            'breaks_until_long': 3,    # NEW: Number of short breaks before long break
            'enable_sound': True,
            'alarm_sound': TimerLogic.SOUND_OPTIONS.get("Exclamation", "SystemExclamation"), 
            'theme': "Dark",
            'notif_opacity': 50,      
            'notif_position': "Center",
            'restrict_long_break': False,
            'restrict_short_break': False,
            'gaming_mode': False,       # NEW: Gaming Mode setting
            'show_advice_long': True,
            'show_advice_short': True
        }
        
        # Store the base window flags
        self._base_flags = Qt.Window | Qt.FramelessWindowHint
        
        # Initialize system tray
        self.setup_system_tray()

        # Start background fullscreen monitoring thread (only if gaming mode is enabled)
        self.fullscreen_monitor = FullscreenMonitorThread()
        self.fullscreen_monitor.fullscreen_detected.connect(self.on_fullscreen_changed)
        self.is_fullscreen_app_active = False

        # Start immediately if gaming mode is already enabled
        if self.settings.get('gaming_mode', False):
            self.fullscreen_monitor.start()
        
        # Make sure window doesn't get destroyed when closed
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        
        # 2. Initialize Timer Logic
        self.timer_logic = TimerLogic(self.settings)

        # 3. Setup Main Window Frame
        self.setWindowTitle("Open Eye Break")
        self.setFixedSize(TIMER_WINDOW_WIDTH, TIMER_WINDOW_HEIGHT)
        
        # Set window flags for frameless window that shows in taskbar
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose, False)  # Prevent destruction on close
        
        # Store original window flags
        self._original_flags = self.windowFlags()
        
        # --- Core Layout for Styling ---
        self.main_container = QFrame()
        self.main_container.setObjectName("MainContainer")
        self.setCentralWidget(self.main_container)
        
        # 4. Setup QStackedWidget inside the MainContainer
        container_layout = QVBoxLayout(self.main_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        self.stacked_widget = QStackedWidget()
        container_layout.addWidget(self.stacked_widget)
        
        # 5. Create Pages 
        self.timer_widget = TimerWidget(self)
        self.settings_widget = SettingsWidget(self.settings, self) 

        # 6. Add Pages to Stack
        self.TIMER_INDEX = 0
        self.SETTINGS_INDEX = 1
        self.stacked_widget.addWidget(self.timer_widget) 
        self.stacked_widget.addWidget(self.settings_widget) 
        self.stacked_widget.setCurrentIndex(self.TIMER_INDEX) 

        # 7. Apply initial theme to set color constants and style widgets
        self.apply_theme(self.settings['theme'])

        # Apply rounded corners mask
        self.apply_window_mask()

        # 8. Setup QTimer
        self.qtimer = QTimer(self)
        self.qtimer.timeout.connect(self.timer_widget.update_display) 
        self.qtimer.start(1000) 

    # --- Theme and Utility Methods ---
    
    def apply_theme(self, theme_name, update_settings=False):
        """
        Sets color constants and updates the main window's palette and styles.
        """
        if update_settings:
            self.settings['theme'] = theme_name
        
        current_theme = THEMES.get(theme_name)

        if theme_name == "System" or current_theme is None:
            # Get colors from system defaults for 'System' theme
            app_palette = QApplication.instance().palette()
            self.BG = QColor(app_palette.color(QPalette.Window)).name()
            self.FG = QColor(app_palette.color(QPalette.WindowText)).name()
            self.INPUT_BG = QColor(app_palette.color(QPalette.Base)).name()
            # Use fixed colors for accents as system palette doesn't define them consistently
            self.ACCENT = "#3498db" 
            self.RED = "#e74c3c"
            self.GREEN = "#2ecc71"
            self.YELLOW = "#f1c40f"
        else:
            # Apply custom colors
            self.BG = current_theme['BG']
            self.FG = current_theme['FG']
            self.INPUT_BG = current_theme['INPUT_BG']
            self.ACCENT = current_theme['ACCENT']
            self.RED = current_theme['RED']
            self.GREEN = current_theme['GREEN']
            self.YELLOW = current_theme['YELLOW']
            
        self.set_color_palette(theme_name)
        
        # Update styles for all child widgets (Timer and Settings)
        self.timer_widget.update_styles()
        self.settings_widget.update_styles()
    
    def resizeEvent(self, event):
        """Re-apply mask when window is resized."""
        super().resizeEvent(event)
        self.apply_window_mask()

    def set_color_palette(self, theme_name):
        """Applies the QPalette to the main window based on current color constants."""
        if theme_name == "System":
            # Reset to system palette
            app = QApplication.instance()
            self.setPalette(app.palette())
        else:
            # Apply custom palette
            palette = self.palette()
            palette.setColor(QPalette.Window, QColor(self.BG))
            palette.setColor(QPalette.WindowText, QColor(self.FG))
            palette.setColor(QPalette.Base, QColor(self.INPUT_BG))
            palette.setColor(QPalette.Text, QColor(self.FG))
            palette.setColor(QPalette.ButtonText, QColor(self.FG))
            palette.setColor(QPalette.Highlight, QColor(self.ACCENT))
            self.setPalette(palette)

    def apply_window_mask(self):
        """Creates a rounded rectangle mask for the frameless window."""
        path = QPainterPath()
        path.addRoundedRect(
            self.rect(), 
            WINDOW_BORDER_RADIUS,  # corner radius
            WINDOW_BORDER_RADIUS   # corner radius
        )
        mask = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(mask)

    def on_gaming_mode_changed(self, enabled):
        """Called when gaming mode setting changes in settings."""
        if enabled:
            if not self.fullscreen_monitor.isRunning():
                self.fullscreen_monitor.start()
                print("Gaming mode enabled - started fullscreen monitoring")
        else:
            if self.fullscreen_monitor.isRunning():
                self.fullscreen_monitor.stop()
                print("Gaming mode disabled - stopped fullscreen monitoring")

    def play_alarm(self, sound_alias):
        try:
            winsound.PlaySound(sound_alias, winsound.SND_ALIAS | winsound.SND_ASYNC)
        except Exception as e:
            print(f"Failed to play {sound_alias}: {e}")
            try:
                winsound.PlaySound("SystemBeep", winsound.SND_ALIAS | winsound.SND_ASYNC)
            except Exception as fallback_error:
                print(f"Fallback sound also failed: {fallback_error}")

    # --- System Tray Implementation ---
    def setup_system_tray(self):
        """Initialize the system tray icon and menu"""
        import os
        import sys
        
        # Get the correct path for the icon whether running as script or exe
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            base_path = sys._MEIPASS
        else:
            # Running as script
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        icon_path = os.path.join(base_path, "resources", "icon.ico")
        app_icon = QIcon(icon_path)
        
        # Set application icon
        self.setWindowIcon(app_icon)
        
        # Set system tray icon
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(app_icon)
        self.tray_icon.setToolTip("Open Eye Break")
        
        # Create tray menu
        tray_menu = QMenu()
        restore_action = tray_menu.addAction("Settings")
        restore_action.triggered.connect(self.open_settings_from_tray)
        tray_menu.addSeparator()
        quit_action = tray_menu.addAction("Quit")
        quit_action.triggered.connect(QApplication.quit)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()
    
    def changeEvent(self, event):
        """Handle window state changes"""
        if event.type() == event.Type.WindowStateChange:
            if self.windowState() & Qt.WindowMinimized:
                self.minimize_to_tray()
        super().changeEvent(event)
    
    def minimize_to_tray(self):
        """Hide the window and show tray icon"""
        # Close any active notification first
        if hasattr(self, 'timer_widget'):
            self.timer_widget.close_notification_window()
        
        # Just hide the window
        self.hide()
        
        if self.settings['enable_sound']:
            self.play_alarm("SystemDefault")  # Play a subtle sound when minimizing
        if self.tray_icon:
            self.tray_icon.showMessage(
                "Open Eye Break",
                "Application minimized to tray. Timer continues running.",
                QSystemTrayIcon.Information,
                2000
            )
    
    @Slot(bool)
    def on_fullscreen_changed(self, is_fullscreen):
        """Called when fullscreen state changes."""
        self.is_fullscreen_app_active = is_fullscreen

    def restore_from_tray(self):
        """Restore the window from system tray"""
        # Close any active notification first
        if hasattr(self, 'timer_widget'):
            self.timer_widget.close_notification_window()
        
        # Reset window flags to base state
        self.setWindowFlags(self._base_flags)
        self.show()
        self.activateWindow()
        
        if self.settings['enable_sound']:
            self.play_alarm("SystemDefault")  # Play a subtle sound when restoring
    
    @Slot()
    def open_settings_from_tray(self):
        """Open the settings page from the tray icon"""
        self.restore_from_tray()
        self.show_settings_page()

    def tray_icon_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.Trigger:  # Single click
            if self.isVisible():
                if self.isMinimized():
                    self.showNormal()
                self.activateWindow()
            else:
                self.restore_from_tray()

    # --- Stack Navigation ---
    @Slot()
    def show_settings_page(self):
        # Switches to the Settings page. Copies main settings to temp settings.
        self.timer_widget.close_notification_window() # Ensure notification is closed
        self.settings_widget.load_settings(self.settings) 
        required_height = self.settings_widget.sizeHint().height()
        self.setFixedSize(SETTINGS_WINDOW_WIDTH, required_height)
        self.stacked_widget.setCurrentIndex(self.SETTINGS_INDEX)

    def show_timer_page(self, new_settings=None):
        # Switches back to the Timer page, applies new settings, and closes any open test break window.
        self.timer_widget.close_notification_window()

        if new_settings:
            # Check if gaming mode setting changed BEFORE updating settings
            gaming_mode_changed = new_settings.get('gaming_mode') != self.settings.get('gaming_mode')
            
            # Update the theme permanently if the theme changed in settings
            if new_settings['theme'] != self.settings['theme']:
                self.apply_theme(new_settings['theme'], update_settings=True)
                
            self.settings = new_settings  # NOW update settings
            self.timer_logic = TimerLogic(self.settings) 
            self.timer_widget.link_logic(self.timer_logic)
            self.timer_logic.start()
            self.timer_widget.update_gui_after_reset()

            # Apply gaming mode change AFTER settings are updated
            if gaming_mode_changed:
                self.on_gaming_mode_changed(new_settings['gaming_mode'])

        self.setFixedSize(TIMER_WINDOW_WIDTH, TIMER_WINDOW_HEIGHT)
        self.stacked_widget.setCurrentIndex(self.TIMER_INDEX)

    # --- Window Dragging Logic ---
    def mousePressEvent(self, event):
        # Determine the correct title bar widget
        if self.stacked_widget.currentIndex() == self.TIMER_INDEX:
            title_bar_widget = self.timer_widget.title_bar
        else: # SETTINGS_INDEX
            title_bar_widget = self.settings_widget.title_header_frame
            
        title_bar_geometry = title_bar_widget.geometry()

        # The PySide6.QtWidgets.QWidget.mapTo() signature requires a QPoint or QPointF for the second argument.
        mapped_point = title_bar_widget.mapTo(self, title_bar_geometry.topLeft())
        draggable_area = QRect(mapped_point, title_bar_geometry.size())
            
        if draggable_area.contains(event.position().toPoint()):
            if event.button() == Qt.LeftButton:
                self.old_pos = event.globalPosition().toPoint()
        else:
            self.old_pos = None

    def mouseMoveEvent(self, event):
        if hasattr(self, 'old_pos') and self.old_pos is not None:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.pos() + delta)
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.old_pos = None

    def closeEvent(self, event):
        """Handle application close - clean up threads."""
        try:
            if hasattr(self, 'fullscreen_monitor') and self.fullscreen_monitor:
                if self.fullscreen_monitor.isRunning():
                    self.fullscreen_monitor.stop()
                    self.fullscreen_monitor.wait(2000)  # Wait max 2 seconds for thread to finish
                    print("Fullscreen monitor thread stopped cleanly")
        except Exception as e:
            print(f"Error stopping fullscreen monitor: {e}")
        
        super().closeEvent(event)


# ----------------------------------------------------------------------
# --- TIMER CONTENT WIDGET (The Timer Page) ---
# ----------------------------------------------------------------------

class TimerWidget(QWidget):
    
    def __init__(self, parent):
        super().__init__(parent)
        self.main_window = parent 
        self.timer_logic = parent.timer_logic 
        self.notification_window = None # Holds a reference to the active notification
        self._create_ui()

    def link_logic(self, logic):
        """ Used to update the logic object after settings change. """
        self.timer_logic = logic
        
    def get_colors(self):
        """ Helper to get current colors and settings from parent. """
        return {
            'BG': self.main_window.BG,
            'FG': self.main_window.FG,
            'INPUT_BG': self.main_window.INPUT_BG,
            'ACCENT': self.main_window.ACCENT,
            'RED': self.main_window.RED,
            'GREEN': self.main_window.GREEN,
            'YELLOW': self.main_window.YELLOW,
            'THEME': self.main_window.settings['theme'],
            # These are used for the standard timer loop (applied settings)
            'NOTIF_OPACITY': self.main_window.settings['notif_opacity'], 
            'NOTIF_POSITION': self.main_window.settings['notif_position']
        }
        
    def _style_button(self, button):
        """Applies minimal, context-specific styling to buttons, including hover."""
        colors = self.get_colors()
        
        # Default button style (used for Test Sound, Try Break buttons)
        default_style = f"""
            QPushButton {{
                background-color: {colors['INPUT_BG']}; 
                color: {colors['FG']};
                border: none;
                padding: 5px;
                border-radius: 4px; 
            }}
            QPushButton:hover {{
                background-color: {colors['ACCENT']}; 
                color: white; 
            }}
        """
        button.setStyleSheet(default_style)
        
        # Override specific buttons with custom/colored styles
        if button.objectName() in ["SettingsButton", "MinimizeButton"]:
            custom_style = f"""
                QPushButton#{button.objectName()} {{ 
                    background-color: {colors['INPUT_BG']}; 
                    color: {colors['FG']}; 
                    border: none; 
                }}
                QPushButton#SettingsButton:hover {{ 
                    background-color: {colors['YELLOW']}; 
                    color: {colors['BG']}; 
                }}
                QPushButton#MinimizeButton:hover {{ 
                    background-color: {colors['ACCENT']}; 
                    color: {colors['FG']}; 
                }}
            """
            button.setStyleSheet(custom_style)
            
        elif button.objectName() == "CloseButton":
            button.setStyleSheet(f"""
                QPushButton#CloseButton {{
                    background-color: {colors['INPUT_BG']}; 
                    color: {colors['FG']};
                    border: none;
                    padding: 5px;
                }}
                QPushButton#CloseButton:hover {{
                    background-color: {colors['RED']};
                    color: white; 
                }}
            """)
            
        elif button.objectName() == "ApplyButton":
             button.setStyleSheet(f"""
                QPushButton#ApplyButton {{
                    color: white;
                    font-weight: bold;
                    background-color: {colors['GREEN']};
                    border: none;
                    padding: 5px;
                    border-radius: 4px;
                }}
                QPushButton#ApplyButton:hover {{
                    background-color: #27ae60;
                }}
            """)
        
        # Re-apply the StartStopButton state style if it exists
        if button.objectName() == "StartStopButton":
            self.update_gui_after_reset()


    def update_styles(self):
        """Re-applies all dynamic styles when the theme changes."""
        colors = self.get_colors()
        
        # 1. Update Container Background
        self.main_window.main_container.setStyleSheet(f"""
            #MainContainer {{ 
                background-color: {colors['BG']}; 
            }}
        """)
        
        # 2. Update Title Bar Background
        self.title_bar.setStyleSheet(f"""
            #TitleBar {{ 
                background-color: {colors['INPUT_BG']}; 
            }}
        """)
        
        # 3. Update Content Background
        content_widget = self.findChild(QWidget, 'content_widget')
        if content_widget:
            content_widget.setStyleSheet(f"background-color: {colors['BG']};")
        
        # 4. Update Button Styles
        for child in self.title_bar.findChildren(QPushButton):
            self._style_button(child)
        self._style_button(self.start_button)
        
        # 5. Update Labels
        title_label = self.title_bar.findChild(QLabel)
        if title_label:
            title_label.setStyleSheet(f"color: {colors['FG']};")
            
        # 6. Force update the display for current phase/color
        self.update_gui_after_reset()


    def _create_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- Custom Title Bar ---
        self.title_bar = QFrame(self)
        self.title_bar.setObjectName("TitleBar")
        self.title_bar.setFixedHeight(TITLE_BAR_HEIGHT)
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(5, 0, 0, 0)
        title_layout.setSpacing(5)
        
        # Title Label
        title_label = QLabel("Open Eye Break v1.0")
        title_label.setFont(QFont("Arial", 10, QFont.Bold))
        title_layout.addWidget(title_label)
        
        title_layout.addStretch(1)
        
        # Buttons are created first, then styled in update_styles()
        self.settings_btn = QPushButton("\u2699") 
        self.settings_btn.setObjectName("SettingsButton")
        self.settings_btn.setFixedSize(30, 30)
        self.settings_btn.setFont(QFont("Arial", 12))
        self.settings_btn.clicked.connect(self.main_window.show_settings_page)
        title_layout.addWidget(self.settings_btn)

        self.min_btn = QPushButton("—")
        self.min_btn.setObjectName("MinimizeButton")
        self.min_btn.setFixedSize(30, 30)
        self.min_btn.clicked.connect(self.main_window.minimize_to_tray)
        title_layout.addWidget(self.min_btn)
        
        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("CloseButton")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.clicked.connect(self.main_window.close)
        # Apply initial style to the close button which is used in the main window's dragging logic
        self._style_button(self.close_btn)
        title_layout.addWidget(self.close_btn)
        
        main_layout.addWidget(self.title_bar)

        # --- Content Area ---
        content_widget = QWidget()
        content_widget.setObjectName("content_widget")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 5, 10, 10)
        content_layout.setSpacing(0)

        # Phase Indicator Label
        self.phase_label = QLabel(self.timer_logic.get_phase_name())
        font = QFont("Arial", 10)
        font.setItalic(True)
        self.phase_label.setFont(font) 
        self.phase_label.setStyleSheet(f"color: #bdc3c7;")
        self.phase_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(self.phase_label)

        # Time Display Label
        self.time_label = QLabel(self.timer_logic.get_time_display())
        self.time_label.setFont(QFont("Arial", 36, weight=QFont.Bold))
        self.time_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(self.time_label)
        
        # Button Container
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(10)

        # Start/Stop Button
        self.start_button = QPushButton("PAUSE TIMER")
        self.start_button.setObjectName("StartStopButton")
        self.start_button.setFont(QFont("Arial", 12, QFont.Bold))
        self.start_button.clicked.connect(self.toggle_timer)
        self.start_button.setFixedHeight(30)
        
        # Reset Button
        self.reset_button = QPushButton("RESET")
        self.reset_button.setObjectName("ResetButton")
        self.reset_button.setFont(QFont("Arial", 12, QFont.Bold))
        self.reset_button.clicked.connect(self.reset_timer)
        self.reset_button.setFixedHeight(30)
        
        # Add buttons to container
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.reset_button)
        content_layout.addWidget(button_container)
        
        # Start the timer automatically
        self.timer_logic.start()
        
        # Apply initial style to the buttons
        self._style_button(self.start_button)
        self._style_button(self.reset_button)


        main_layout.addWidget(content_widget)

    # --- Timer & GUI Update Methods ---
    @Slot()
    def toggle_timer(self):
        """Starts or stops the timer and updates the button text."""
        if self.timer_logic.is_running:
            self.timer_logic.stop()
        else:
            self.timer_logic.start()
        self.update_gui_after_reset()
            
    @Slot()
    def update_display(self):
        """Ticked every second by QTimer. Updates display and checks for phase change."""
        
        if not self.timer_logic.is_running:
            return
        
        # 1. Check for long break notification (pre-alarm)
        if self.timer_logic.check_long_break_notify():
            if self.main_window.settings['enable_sound']:
                self.main_window.play_alarm("SystemAsterisk")
        
        # 2. Advance the timer logic
        phase_switched = self.timer_logic.tick()

        # 3. Handle phase switch
        if phase_switched:
            # If the phase is now a break
            if self.timer_logic.is_break():

                self.show_break_window()
            # If the phase is now work (break just ended)
            else:
                # Play the end-of-break sound (END SOUND for live)
                if self.main_window.settings['enable_sound']:
                    self.main_window.play_alarm(self.main_window.settings['alarm_sound'])
                    
                self.close_notification_window()
                
            self.update_gui_after_reset()
            
        # 4. Update Main Timer Display
        time_display_str = self.timer_logic.get_time_display()
        self.time_label.setText(time_display_str)
        
        # 5. Update Notification Window Display (if open) - Only for LIVE break
        if self.notification_window is not None:
            self.notification_window.update_time_display(time_display_str)


    def reset_timer(self):
        """Resets the timer completely to its initial state (including cycle count)."""
        self.timer_logic.reset()  # This will reset everything including the cycle count
        self.timer_logic.start()  # Auto-start after reset
        self.update_gui_after_reset()
        # Close any open notification window
        self.close_notification_window()
    
    def update_gui_after_reset(self):
        """Updates all labels and buttons based on current logic state."""
        colors = self.get_colors()
        self.phase_label.setText(self.timer_logic.get_phase_name())

        # Determine if we're in a break
        is_in_break = self.timer_logic.is_long_break or self.timer_logic.is_short_break
        
        if self.timer_logic.is_long_break: 
            color = colors['RED'] 
        elif self.timer_logic.is_short_break:
            color = colors['ACCENT']
        else:
            color = colors['GREEN']
            
        self.time_label.setStyleSheet(f"color: {color};")
        
        # Show 00:00 during breaks, otherwise show actual time
        if is_in_break:
            self.time_label.setText("00:00")
            # Disable pause button during breaks
            self.start_button.setEnabled(False)
        else:
            self.time_label.setText(self.timer_logic.get_time_display())
            self.start_button.setEnabled(True)
        
        # Style for Start/Stop button
        if self.timer_logic.is_running:
            self.start_button.setText("PAUSE TIMER")
            self.start_button.setStyleSheet(f"""
                QPushButton#StartStopButton {{
                    color: white;
                    font-weight: bold;
                    border: none;
                    padding: 5px;
                    border-radius: 4px;
                    background-color: {colors['YELLOW']};
                }}
                QPushButton#StartStopButton:hover {{
                    background-color: #c0392b;
                }}
                QPushButton#StartStopButton:disabled {{
                    background-color: #7f8c8d;
                    color: #bdc3c7;
                }}
            """)
        else:
            self.start_button.setText("RESUME TIMER")
            self.start_button.setStyleSheet(f"""
                QPushButton#StartStopButton {{
                    color: white;
                    font-weight: bold;
                    border: none;
                    padding: 5px;
                    border-radius: 4px;
                    background-color: {colors['GREEN']};
                }}
                QPushButton#StartStopButton:hover {{
                    background-color: #27ae60;
                }}
                QPushButton#StartStopButton:disabled {{
                    background-color: #7f8c8d;
                    color: #bdc3c7;
                }}
            """)
            
        # Style for Reset button
        self.reset_button.setStyleSheet(f"""
            QPushButton#ResetButton {{
                color: white;
                font-weight: bold;
                border: none;
                padding: 5px;
                border-radius: 4px;
                background-color: {colors['RED']};
            }}
            QPushButton#ResetButton:hover {{
                background-color: #c0392b;
            }}
            QPushButton#ResetButton:disabled {{
                background-color: #7f8c8d;
                color: #bdc3c7;
            }}
            """)


    def show_break_window(self):
        """
        Creates the non-modal BreakNotificationWindow for both short and long breaks (LIVE).
        """
        
        self.close_notification_window()
        
        # Play sound at the START of the LIVE break
        if self.main_window.settings['enable_sound']:
            self.main_window.play_alarm(self.main_window.settings['alarm_sound'])

        # Check for Gaming Mode and fullscreen apps - use the monitored state
        gaming_mode_enabled = self.main_window.settings.get('gaming_mode', False)
        fullscreen_app_detected = self.main_window.is_fullscreen_app_active
        
        if gaming_mode_enabled and fullscreen_app_detected:
            # Gaming mode ON + fullscreen app detected: Force on top is false
            force_on_top_flag = False
        else:
            # Normal case: Force on top is true
            force_on_top_flag = True
        
        colors = self.get_colors()

        # Determine if advice should be shown
        show_advice_flag = (self.main_window.settings['show_advice_long'] if self.timer_logic.is_long_break 
                    else self.main_window.settings['show_advice_short'])
        
        # Determine if it is a long or short break and set parameters accordingly
        if self.timer_logic.is_long_break:
            # LONG BREAK
            advice = random.choice(LONG_BREAK_ADVICE)
            bg_color = colors['RED'] 
            restrict_long = self.main_window.settings['restrict_long_break']
            restrict_short = False
        else:
            # SHORT BREAK
            advice = random.choice(BREAK_ADVICE)
            bg_color = colors['ACCENT'] 
            restrict_long = False
            restrict_short = self.main_window.settings['restrict_short_break']
            
        text_color = "white"
            
        # Instantiate the unified notification window (LIVE mode: pass formatted string, is_test_mode=False)
        self.notification_window = BreakNotificationWindow(
            self, 
            self.timer_logic.is_long_break,
            advice,
            self.timer_logic.get_time_display(), # MM:SS string
            False,                               # is_test_mode
            bg_color,
            text_color,
            colors['NOTIF_OPACITY'],    
            colors['NOTIF_POSITION'],
            restrict_long,                       # NEW
            restrict_short,                       # NEW
            force_on_top=force_on_top_flag,
            show_advice=show_advice_flag
        )
        
    @Slot()
    def close_notification_window(self):
        """
        Closes any active BreakNotificationWindow and starts the next work timer.
        """
        try:
            if self.notification_window is not None:
                try:
                    self.notification_window.stop_test_timer()
                    self.notification_window.close()
                except Exception as e:
                    print(f"Error closing notification: {e}")
                finally:
                    self.notification_window.deleteLater()
                    self.notification_window = None
                
                # Start the next work timer if we were in a break
                if self.timer_logic.is_short_break or self.timer_logic.is_long_break:
                    self.timer_logic.move_to_next_work_timer()  # Move to next work timer while maintaining cycle count
                    self.update_gui_after_reset()  # Update the display

        except Exception as e:
            print(f"Unexpected error closing notification: {e}")
            self.notification_window = None

        
    def test_break(self, is_long_break, opacity=None, position=None, short_break_sec=None, long_break_min=None,
                   restrict_long=None, restrict_short=None, show_advice=None): # NEW PARAMETERS
        
        #Immediately triggers a test break window with a counting down timer.
        
        self.close_notification_window()
            
        colors = self.get_colors()
        
        # Make sure we have a valid parent widget
        if not hasattr(self, 'main_window') or not self.main_window:
            return
        
        if is_long_break:
            # LONG BREAK TEST
            advice = random.choice(LONG_BREAK_ADVICE)
            bg_color = colors['RED'] 
            # Calculate time from preview parameter or fall back to applied settings
            preview_long_break_min = long_break_min if long_break_min is not None else self.main_window.settings['long_break_min']
            total_seconds = preview_long_break_min * 60
        else:
            # SHORT BREAK TEST
            advice = random.choice(BREAK_ADVICE)
            bg_color = colors['ACCENT'] 
            # Calculate time from preview parameter or fall back to applied settings
            preview_short_break_sec = short_break_sec if short_break_sec is not None else self.main_window.settings['short_break_sec']
            total_seconds = preview_short_break_sec

        text_color = "white"
        test_opacity = opacity if opacity is not None else colors['NOTIF_OPACITY']
        test_position = position if position is not None else colors['NOTIF_POSITION']
        
        # Get restrict settings from arguments or fall back to applied settings
        test_restrict_long = restrict_long if restrict_long is not None else self.main_window.settings['restrict_long_break']
        test_restrict_short = restrict_short if restrict_short is not None else self.main_window.settings['restrict_short_break']

        # NEW: Play sound at the START of the test break
        alarm_sound = self.main_window.settings['alarm_sound']
        if self.main_window.settings['enable_sound']:
            self.main_window.play_alarm(alarm_sound)

        # Instantiate the unified notification window (TEST mode: pass integer seconds, is_test_mode=True)
        self.notification_window = BreakNotificationWindow(
            self, 
            is_long_break,
            advice,
            total_seconds, # Pass the integer seconds
            True,          # is_test_mode
            bg_color,
            text_color,
            test_opacity,    
            test_position,
            test_restrict_long,  # NEW
            test_restrict_short, # NEW
            alarm_sound, # Pass sound alias for end sound
            True,
            show_advice=show_advice if show_advice is not None else True  # Use the provided value or default to True
        )

# ----------------------------------------------------------------------
# --- SETTINGS CONTENT WIDGET (The Settings Page) ---
# ----------------------------------------------------------------------

class SettingsWidget(QWidget):
    
    def __init__(self, current_settings, parent):
        super().__init__(parent)
        self.main_window = parent 
        self.temp_settings = current_settings.copy()
        
        self._create_ui()

    def get_colors(self):
        """Helper to get current colors from parent."""
        return {
            'BG': self.main_window.BG,
            'FG': self.main_window.FG,
            'INPUT_BG': self.main_window.INPUT_BG,
            'GREEN': self.main_window.GREEN,
        }
        
    def update_styles(self):
        """Re-applies all dynamic styles when the theme changes."""
        colors = self.get_colors()
        
        # 1. Update Title Bar Background
        self.title_header_frame.setStyleSheet(f"""
            background-color: {colors['INPUT_BG']};
        """)
        
        # 2. Update Content Background and default text color
        self.settings_content.setStyleSheet(f"background-color: {colors['BG']}; color: {colors['FG']};")
        
        # 3. Update Title Label
        header_title = self.title_header_frame.findChild(QLabel)
        if header_title:
            header_title.setStyleSheet(f"color: {colors['FG']};")
            
        # 4. Update Buttons (Close and Apply)
        self.main_window.timer_widget._style_button(self.close_btn) 
        self.main_window.timer_widget._style_button(self.findChild(QPushButton, "ApplyButton"))
        self.main_window.timer_widget._style_button(self.findChild(QPushButton, "TestSoundButton"))
        self.main_window.timer_widget._style_button(self.findChild(QPushButton, "TryShortBreakButton"))
        self.main_window.timer_widget._style_button(self.findChild(QPushButton, "TryLongBreakButton"))
        
        # 5. Update Labels and Checkboxes (Ensure they use the correct foreground color)
        for label in self.settings_content.findChildren(QLabel):
            # Apply color to all labels, including those with <b> tags
            label.setStyleSheet(f"color: {colors['FG']};")
            
        # Update all checkboxes
        for checkbox in self.settings_content.findChildren(QCheckBox):
            checkbox.setStyleSheet(f"color: {colors['FG']};")


    def _create_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- Custom Settings Header ---
        self.title_header_frame = QFrame()
        self.title_header_frame.setFixedHeight(30)
        header_layout = QHBoxLayout(self.title_header_frame)
        header_layout.setContentsMargins(10, 0, 0, 0)
        header_layout.setSpacing(5)
        
        # Settings Title
        header_title = QLabel("Settings")
        header_title.setFont(QFont("Arial", 12, QFont.Bold))
        header_layout.addWidget(header_title)
        
        header_layout.addStretch(1)
        
        # Close Button (X) - DISCARD changes
        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("CloseButton")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.setFont(QFont("Arial", 12))
        self.close_btn.clicked.connect(self.close_settings) 
        header_layout.addWidget(self.close_btn)

        main_layout.addWidget(self.title_header_frame)
        
        # Settings Content
        self.settings_content = QWidget() 
        content_layout = QVBoxLayout(self.settings_content)
        content_layout.setContentsMargins(10, 10, 10, 10)
        
        # --- Theme Selection ---
        theme_frame = QWidget()
        theme_layout = QHBoxLayout(theme_frame)
        theme_layout.setContentsMargins(0, 0, 0, 0)
        theme_layout.addWidget(QLabel("<b>Application Theme:</b>"))
        
        self.theme_picker = QComboBox()
        self.theme_picker.addItems(THEMES.keys())
        self.theme_picker.currentIndexChanged.connect(self._instant_theme_change)
        
        theme_layout.addWidget(self.theme_picker)
        theme_layout.addStretch(1)
        content_layout.addWidget(theme_frame)

        content_layout.addWidget(self._create_separator())
        
        # Long Break Settings
        content_layout.addWidget(QLabel("<b>Long Break Settings</b>"))
        self._create_setting(content_layout, "Long Break Duration:", 'long_break_min', "minutes", 1, 30)
        self._create_setting(content_layout, "Take a Long Break After:", 'breaks_until_long', "short breaks", 2, 10)

        # Show Advice checkbox
        self.checkbox_show_advice_long = self._create_checkbox_setting(
            content_layout, 
            "Show Advice", 
            'show_advice_long', 
            self.temp_settings.get('show_advice_long', True)
        )
        
        # Restrict Mode Checkbox for Long Break
        self.checkbox_restrict_long_break = self._create_checkbox_setting(
            content_layout, 
            "Restrict Mode (Disable Dismiss Button)", 
            'restrict_long_break', 
            self.temp_settings.get('restrict_long_break', False)
        )
        
        content_layout.addWidget(self._create_separator())
        
        # Short Break Settings
        content_layout.addWidget(QLabel("<b>Short Break Settings</b>"))
        self._create_setting(content_layout, "Take a short break every:", 'short_work_min', "minutes", 1, 60)
        self._create_setting(content_layout, "For:", 'short_break_sec', "seconds", 10, 59)

        # Show Advice checkbox
        self.checkbox_show_advice_short = self._create_checkbox_setting(
            content_layout, 
            "Show Advice", 
            'show_advice_short', 
            self.temp_settings.get('show_advice_short', True)
        )

        # NEW: Restrict Mode Checkbox for Short Break
        self.checkbox_restrict_short_break = self._create_checkbox_setting(
            content_layout, 
            "Restrict Mode (Disable Dismiss Button)", 
            'restrict_short_break', 
            self.temp_settings.get('restrict_short_break', False)
        )
        
        content_layout.addWidget(self._create_separator())

        # --- Notification Options ---
        content_layout.addWidget(QLabel("<b>Notification Appearance</b>"))
        
        # Gaming Mode Checkbox
        gaming_frame = QWidget()
        gaming_layout = QHBoxLayout(gaming_frame)
        gaming_layout.setContentsMargins(0, 0, 0, 0)
        
        self.gaming_mode_cb = QCheckBox("Gaming Mode")
        self.gaming_mode_cb.setToolTip("Disable on screen notification while in fullscreen mode")
        gaming_layout.addWidget(self.gaming_mode_cb)
        gaming_layout.addStretch(1)
        content_layout.addWidget(gaming_frame)
        
        # Transparency Slider
        transparency_frame = QWidget()
        transparency_layout = QHBoxLayout(transparency_frame)
        transparency_layout.setContentsMargins(0, 0, 0, 0)
        transparency_layout.addWidget(QLabel("Opacity (0-100%):"))
        
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setSingleStep(5)
        self.opacity_slider.setPageStep(10)
        self.opacity_slider.setValue(50) 
        
        self.opacity_label = QLabel(f"{self.opacity_slider.value()}%")
        self.opacity_slider.valueChanged.connect(lambda v: self.opacity_label.setText(f"{v}%"))
        
        transparency_layout.addWidget(self.opacity_slider)
        transparency_layout.addWidget(self.opacity_label)
        content_layout.addWidget(transparency_frame)
        
        # Position Dropdown
        position_frame = QWidget()
        position_layout = QHBoxLayout(position_frame)
        position_layout.setContentsMargins(0, 0, 0, 0)
        position_layout.addWidget(QLabel("Position on Screen:"))
        
        self.position_picker = QComboBox()
        self.position_picker.addItems(["Top", "Center", "Bottom"])
        self.position_picker.setCurrentText("Center")
        
        position_layout.addWidget(self.position_picker)
        position_layout.addStretch(1)
        content_layout.addWidget(position_frame)
        
        content_layout.addWidget(self._create_separator())
        
        # Sound Options
        self.sound_enable_cb = QCheckBox("Enable sounds")
        content_layout.addWidget(self.sound_enable_cb)

        # Alarm Sound Picker
        sound_frame = QWidget()
        sound_layout = QHBoxLayout(sound_frame)
        sound_layout.setContentsMargins(0, 0, 0, 0)
        sound_layout.addWidget(QLabel("Alarm Sound:"))
        
        self.sound_picker = QComboBox()
        self.sound_picker.addItems(TimerLogic.SOUND_OPTIONS.keys())
        sound_layout.addWidget(self.sound_picker)
        
        test_btn = QPushButton("Test Sound")
        test_btn.setObjectName("TestSoundButton")
        test_btn.clicked.connect(lambda: self.main_window.play_alarm(TimerLogic.SOUND_OPTIONS[self.sound_picker.currentText()]))
        sound_layout.addWidget(test_btn)
        
        content_layout.addWidget(sound_frame)

        # Try Break Buttons
        break_frame = QWidget()
        break_layout = QHBoxLayout(break_frame)
        break_layout.setContentsMargins(0, 0, 0, 0)
        try_short_btn = QPushButton("Try Short Break")
        try_short_btn.setObjectName("TryShortBreakButton")
        try_long_btn = QPushButton("Try Long Break")
        try_long_btn.setObjectName("TryLongBreakButton")
        
        # Pass the current, UNAPPLIED opacity and position values for testing
        try_short_btn.clicked.connect(
            lambda: self.main_window.timer_widget.test_break(
                is_long_break=False,
                opacity=self.opacity_slider.value(), 
                position=self.position_picker.currentText(),
                restrict_long=self.checkbox_restrict_long_break.isChecked(), # NEW
                restrict_short=self.checkbox_restrict_short_break.isChecked(), # NEW
                show_advice=self.checkbox_show_advice_short.isChecked(),
                short_break_sec=self.spin_short_break_sec.value()  # Pass unapplied short break duration
            )
        )
        try_long_btn.clicked.connect(
            lambda: self.main_window.timer_widget.test_break(
                is_long_break=True,
                opacity=self.opacity_slider.value(), 
                position=self.position_picker.currentText(),
                restrict_long=self.checkbox_restrict_long_break.isChecked(), # NEW
                restrict_short=self.checkbox_restrict_short_break.isChecked(), # NEW
                show_advice=self.checkbox_show_advice_long.isChecked(),
                long_break_min=self.spin_long_break_min.value()  # Pass unapplied long break duration
            )
        )
        
        break_layout.addWidget(try_short_btn)
        break_layout.addWidget(try_long_btn)
        content_layout.addWidget(break_frame)
        
        content_layout.addStretch(1) 
        
        # Apply Button
        apply_btn = QPushButton("Apply and Close")
        apply_btn.setObjectName("ApplyButton")
        apply_btn.setFont(QFont("Arial", 12, QFont.Bold))
        apply_btn.setFixedHeight(30)
        apply_btn.clicked.connect(self.apply_settings)
        content_layout.addWidget(apply_btn)
        
        main_layout.addWidget(self.settings_content) 

    @Slot()
    def _instant_theme_change(self, index):
        """Called immediately when the theme ComboBox selection changes."""
        selected_theme = self.theme_picker.itemText(index)
        
        # Only preview the theme without updating the main settings
        self.main_window.apply_theme(selected_theme, update_settings=False)


    def load_settings(self, current_settings):
        """Loads the current main settings into the temporary fields."""
        self.temp_settings = current_settings.copy()
        
        # Load theme setting
        self.theme_picker.blockSignals(True)
        self.theme_picker.setCurrentText(self.temp_settings['theme'])
        self.theme_picker.blockSignals(False)

        # Load numerical settings
        self.spin_long_break_min.setValue(self.temp_settings['long_break_min'])
        self.spin_breaks_until_long.setValue(self.temp_settings['breaks_until_long'])
        self.spin_short_work_min.setValue(self.temp_settings['short_work_min'])
        self.spin_short_break_sec.setValue(self.temp_settings['short_break_sec'])
        
        # Load sound settings
        self.sound_enable_cb.setChecked(self.temp_settings['enable_sound'])
        current_display_name = next(
            (k for k, v in TimerLogic.SOUND_OPTIONS.items() if v == self.temp_settings['alarm_sound']), 
            list(TimerLogic.SOUND_OPTIONS.keys())[0] if TimerLogic.SOUND_OPTIONS else "Exclamation"
        )
        self.sound_picker.setCurrentText(current_display_name)
        
        # Load Gaming Mode setting
        self.gaming_mode_cb.setChecked(self.temp_settings.get('gaming_mode', False))
        
        # Load transparency and position (block signals to avoid triggering updates)
        self.opacity_slider.blockSignals(True)
        self.opacity_slider.setValue(self.temp_settings['notif_opacity'])
        self.opacity_label.setText(f"{self.temp_settings['notif_opacity']}%")
        self.opacity_slider.blockSignals(False)
        
        self.position_picker.setCurrentText(self.temp_settings['notif_position'])
        
        # Load restrict mode settings
        self.checkbox_restrict_long_break.setChecked(self.temp_settings.get('restrict_long_break', False))
        self.checkbox_restrict_short_break.setChecked(self.temp_settings.get('restrict_short_break', False))

        # Load show advice settings
        self.checkbox_show_advice_long.setChecked(self.temp_settings.get('show_advice_long', True))
        self.checkbox_show_advice_short.setChecked(self.temp_settings.get('show_advice_short', True))


    def _create_setting(self, layout, label_text, key, unit, minval, maxval):
        frame = QWidget()
        h_layout = QHBoxLayout(frame)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.addWidget(QLabel(label_text))
        
        spinbox = QSpinBox()
        spinbox.setRange(minval, maxval)
        spinbox.setValue(self.temp_settings.get(key, minval))
        setattr(self, f'spin_{key}', spinbox) 
        
        h_layout.addWidget(spinbox)
        h_layout.addWidget(QLabel(unit))
        h_layout.addStretch(1)
        
        layout.addWidget(frame)

    def _create_checkbox_setting(self, layout, label_text, key, initial_value=False):
        """NEW: Helper to create a QCheckBox setting with the correct key and layout."""
        frame = QWidget()
        h_layout = QHBoxLayout(frame)
        h_layout.setContentsMargins(0, 0, 0, 0)
        
        checkbox = QCheckBox(label_text)
        checkbox.setChecked(initial_value)
        setattr(self, f'checkbox_{key}', checkbox)
        
        h_layout.addWidget(checkbox)
        h_layout.addStretch(1)
        
        layout.addWidget(frame)
        return checkbox 

    def _create_separator(self):
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        return separator

    def get_settings(self):
        """Collects and returns the currently selected settings from the UI."""
        settings = {}
        
        settings['theme'] = self.theme_picker.currentText()
        
        settings['long_break_min'] = self.spin_long_break_min.value()
        settings['breaks_until_long'] = self.spin_breaks_until_long.value()
        settings['short_work_min'] = self.spin_short_work_min.value()
        settings['short_break_sec'] = self.spin_short_break_sec.value()
        settings['enable_sound'] = self.sound_enable_cb.isChecked()
        
        selected_display_name = self.sound_picker.currentText()
        settings['alarm_sound'] = TimerLogic.SOUND_OPTIONS[selected_display_name]
        
        # Collect transparency and position settings
        settings['notif_opacity'] = self.opacity_slider.value()
        settings['notif_position'] = self.position_picker.currentText()
        
        # Collect Gaming Mode setting
        settings['gaming_mode'] = self.gaming_mode_cb.isChecked()
        
        # NEW: Collect restrict mode settings
        settings['restrict_long_break'] = self.checkbox_restrict_long_break.isChecked()
        settings['restrict_short_break'] = self.checkbox_restrict_short_break.isChecked()

        # Collect show advice settings
        settings['show_advice_long'] = self.checkbox_show_advice_long.isChecked()
        settings['show_advice_short'] = self.checkbox_show_advice_short.isChecked()
        
        return settings

    @Slot()
    def apply_settings(self):
        """Called when Apply & Close is pressed. Updates main window and switches page."""
        new_settings = self.get_settings()
        self.temp_settings = new_settings.copy() 
        
        # Update the main window's settings including the theme
        self.main_window.settings['theme'] = new_settings['theme']
        self.main_window.apply_theme(new_settings['theme'], update_settings=True)
        self.main_window.show_timer_page(new_settings)
        
    @Slot()
    def close_settings(self):
        """
        Called when the Close (X) button is pressed. 
        Discards changes and switches back to the original theme.
        """
        # Restore the original theme
        original_theme = self.temp_settings['theme']  # Get the original theme from temp settings
        self.main_window.apply_theme(original_theme, update_settings=False)
        self.main_window.show_timer_page() 


# ----------------------------------------------------------------------
# --- MAIN EXECUTION ---
# ----------------------------------------------------------------------

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    app.setStyle("Fusion")
    
    # Set application-wide icon
    import os
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        base_path = sys._MEIPASS
    else:
        # Running as script
        base_path = os.path.dirname(os.path.abspath(__file__))

    icon_path = os.path.join(base_path, "resources", "icon.ico")
    app_icon = QIcon(icon_path)
    app.setWindowIcon(app_icon)
    
    window = OpenEyeBreakApp()
    window.show()
    
    sys.exit(app.exec())