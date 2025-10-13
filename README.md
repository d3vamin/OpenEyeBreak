# Open Eye Break

A modern, feature-rich eye health and break reminder application built with PySide6. Open Eye Break helps prevent eye strain and encourages healthy work habits by implementing the 20-20-20 rule and customizable break schedules.

![Version](https://img.shields.io/badge/version-1.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)

## 🌟 Features

### Core Functionality

#### 🕒 Smart Timer System
- **Pomodoro-style Work Cycles**: Customizable work periods (1-60 minutes)
- **Short Breaks**: Quick 20-second eye rest breaks (configurable 10-59 seconds)
- **Long Breaks**: Extended rest periods (1-30 minutes) after multiple work cycles
- **Cycle Tracking**: Visual progress indicator showing current break cycle (e.g., "Break: 2/3")
- **Automatic Progression**: Seamlessly transitions between work and break phases
- **Pause/Resume**: Full control over timer with pause and resume functionality
- **Reset Function**: Instantly reset timer and cycle count to start fresh

#### 🎯 Break Notifications

##### Visual Notifications
- **Non-Modal Design**: Notifications appear on screen without stealing focus
- **Customizable Positioning**: Choose between Top, Center, or Bottom screen placement
- **Adjustable Opacity**: Set notification transparency (0-100%) for minimal distraction
- **Dynamic Sizing**: Automatically adjusts window size based on content
- **Frameless Design**: Clean, modern appearance with rounded corners

##### Break Advice System
- **Contextual Tips**: Different advice for short vs. long breaks
- **Short Break Advice**: 
  - Stretch your arms and shoulders
  - Look at distant objects (20-20-20 rule)
  - Blink exercises for eye moisture
  - Quick hydration reminders
- **Long Break Advice**:
  - Get up and move around
  - Step outside for fresh air
  - Full body stretching routines
  - Extended hydration and snack breaks
- **Toggle Option**: Enable/disable advice display per break type

##### Restrict Mode
- **Long Break Restriction**: Option to disable dismiss button during long breaks
- **Short Break Restriction**: Option to disable dismiss button during short breaks
- **Forced Breaks**: Ensures users take full breaks without early dismissal
- **Customizable**: Apply restriction to either or both break types independently

#### 🎮 Gaming Mode
- **Fullscreen Detection**: Automatically detects when applications are running fullscreen
- **Smart Notification**: Switches to system tray notifications during fullscreen
- **Non-Intrusive**: Prevents break popups from interrupting games, videos, or presentations
- **Works With**: Games, YouTube, streaming platforms, video editing software
- **Tolerance Settings**: Built-in ±20 pixel tolerance for various fullscreen implementations

### 🎨 Appearance & Themes

#### Theme Options
- **Dark Theme**: Easy on the eyes with dark blue-gray tones
  - Background: `#2c3e50`
  - Accent Colors: Blue `#3498db`, Orange `#d8601b`, Green `#25ae60`
- **Light Theme**: Clean, bright interface
  - Background: `#f0f0f0`
  - Accent Colors: Light blue `#9cbde7`, Orange `#d8601b`, Green `#25ae60`
- **System Theme**: Automatically adapts to your OS theme settings
- **Live Preview**: See theme changes instantly before applying
- **Persistent Settings**: Theme choice saved across sessions

#### Color Coding
- **Green**: Work time/active timer
- **Blue**: Short break periods
- **Orange/Red**: Long break periods
- **Yellow**: Settings and configuration

### 🔊 Sound System

#### Notification Sounds
- **Windows System Sounds**: Choose from all available Windows system sounds
- **Automatic Detection**: Scans Windows registry for available sounds
- **Common Sounds Include**:
  - Exclamation
  - Critical Stop
  - Asterisk
  - Question
  - Notification
  - Default Beep
  - Windows Logon/Logoff
  - Mail notification
  - And more...

#### Sound Behavior
- **Break Start Sound**: Plays when break begins
- **Break End Sound**: Plays when break completes
- **Test Function**: Preview sounds before applying
- **Enable/Disable Toggle**: Quick on/off for all sounds
- **Minimalist Approach**: Subtle sounds that don't startle

### 🖥️ System Tray Integration

#### Tray Icon Features
- **Minimize to Tray**: Clicking minimize button hides window to system tray
- **Background Operation**: Timer continues running while minimized
- **Visual Indicator**: System tray icon always visible when app is running
- **Tooltip**: Hover over icon to see "Open Eye Break"

#### Tray Menu
- **Settings**: Quick access to open settings page
- **Quit**: Cleanly exit application
- **Single-Click Restore**: Click icon to restore window
- **Context Menu**: Right-click for full menu options

#### Tray Notifications
- **Minimize Alert**: Brief notification when minimizing to tray
- **Gaming Mode Alerts**: Break notifications appear in tray during fullscreen
- **Duration**: 5-second display for non-intrusive awareness

### ⚙️ Settings & Customization

#### Work Settings
- **Work Duration**: 1-60 minutes per work session
- **Default**: 20 minutes (optimal for eye health)
- **Real-time Preview**: See changes before applying

#### Short Break Settings
- **Duration**: 10-59 seconds
- **Frequency**: Every work cycle
- **Default**: 20 seconds (20-20-20 rule)
- **Show Advice**: Toggle advice display
- **Restrict Mode**: Force full break duration

#### Long Break Settings
- **Duration**: 1-30 minutes
- **Frequency**: After 2-10 short breaks (configurable)
- **Default**: 5 minutes after every 3 short breaks
- **Show Advice**: Toggle advice display
- **Restrict Mode**: Force full break duration

#### Test Break Function
- **Try Short Break**: Preview short break notification with current settings
- **Try Long Break**: Preview long break notification with current settings
- **Live Settings**: Tests use unapplied settings for accurate preview
- **Full Simulation**: Includes countdown timer and end sound

### 🎯 User Interface

#### Main Timer Window
- **Compact Design**: 380x180px minimalist window
- **Frameless**: Modern borderless design
- **Draggable**: Click and drag title bar to reposition
- **Phase Indicator**: Always shows current phase (Work/Short Break/Long Break)
- **Large Timer Display**: Easy-to-read 36pt countdown
- **Color-Coded Status**: Visual feedback for current phase
- **Control Buttons**: 
  - Pause/Resume Timer
  - Reset Timer and Cycles

#### Settings Window
- **Expandable Layout**: Adjusts height based on content
- **Organized Sections**: Clear separation of settings categories
- **Visual Separators**: Clean dividers between setting groups
- **Live Theme Preview**: See theme changes before applying
- **Discard Option**: Close button discards changes
- **Apply and Close**: Save all changes simultaneously

#### Title Bar
- **Custom Design**: Consistent across both windows
- **Settings Button**: Gear icon for quick access
- **Minimize Button**: Hide to system tray
- **Close Button**: Exit application (with confirmation)
- **Drag Handle**: Entire title bar acts as drag handle

## 🚀 Installation

### Requirements
- Python 3.8 or higher
- Windows OS (for system tray and fullscreen detection)
- PySide6

### Install Dependencies
```bash
pip install PySide6
```

### Running from Source
```bash
python main.py
```

### Building Executable
You can compile the application using PyInstaller:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --icon=resources/icon.ico --add-data "resources/icon.ico;resources" main.py
```

## 📖 Usage Guide

### First Launch
1. Application starts automatically with timer running
2. Default settings: 20-minute work, 20-second breaks
3. Timer displays in main window with current phase

### Taking Breaks
1. **Short Breaks**: Popup appears every work cycle
   - Shows advice for eye exercises
   - Displays countdown timer
   - Dismiss button available (unless restricted)
   - Auto-closes when complete

2. **Long Breaks**: Popup appears after configured cycles
   - Shows extended break advice
   - Longer duration for movement
   - Optional restrict mode
   - Visual progress tracking

### Using Gaming Mode
1. Enable in Settings → Notification Appearance
2. Application detects fullscreen windows automatically
3. Break notifications appear in system tray instead
4. Popup resumes when exiting fullscreen

### Customizing Experience
1. Click gear icon or minimize and select "Settings"
2. Adjust work and break durations
3. Change theme and notification appearance
4. Test breaks before applying
5. Click "Apply and Close" to save

### Minimizing to Tray
1. Click minimize button in title bar
2. Application continues in background
3. Timer keeps running
4. Click tray icon to restore

## 🔧 Technical Details

### Architecture
- **Timer Logic**: Separate class handling all timing and state
- **GUI Components**: Modular widget system with TimerWidget and SettingsWidget
- **Theme System**: Dynamic color management with caching
- **Sound System**: Registry-based Windows sound enumeration

### Performance Optimizations
- **Cached System Sounds**: Registry queried once at startup
- **Color Caching**: Theme colors cached to reduce dictionary recreation
- **Efficient Updates**: Only necessary widgets updated on theme change
- **Memory Management**: Proper cleanup of notification windows

### Key Features Implementation

#### Fullscreen Detection
- Windows API integration via ctypes
- 20-pixel tolerance for various window managers
- Own-window exclusion to prevent self-detection
- Active window monitoring

#### Break Window Management
- Non-modal design for non-intrusive operation
- Dynamic sizing based on content
- Transparent background with configurable opacity
- Test mode with separate countdown logic

#### Settings Management
- Temporary settings for preview functionality
- Discard changes without affecting running timer
- Live theme preview before applying
- Validation for all input ranges

## 🎨 Color Scheme Reference

### Dark Theme
- Primary Background: `#2c3e50`
- Text: `#ecf0f1`
- Input Background: `#34495e`
- Short Break (Blue): `#3498db`
- Long Break (Orange): `#d8601b`
- Work Time (Green): `#25ae60`
- Settings (Yellow): `#f39c12`

### Light Theme
- Primary Background: `#f0f0f0`
- Text: `#333333`
- Input Background: `#e1e1e1`
- Short Break (Blue): `#9cbde7`
- Long Break (Orange): `#d8601b`
- Work Time (Green): `#25ae60`
- Settings (Yellow): `#f39c12`

## 🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License
This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments
- Built with PySide6 (Qt for Python)
- Inspired by the 20-20-20 rule for eye health
- Pomodoro Technique principles

## 📞 Support
For issues, questions, or suggestions, please open an issue on GitHub.

## 🔄 Version History
- **v1.0** - Initial release
  - Core timer functionality
  - Theme system
  - Gaming mode
  - System tray integration
  - Restrict mode
  - Customizable notifications

---

**Made with ❤️ for healthier computer usage**
