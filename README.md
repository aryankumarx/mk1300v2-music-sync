# Ant Esports MK1300 V2 - Custom RGB Music & Screen Sync

A lightweight, standalone Python RGB controller for the **Ant Esports MK1300 V2** mechanical keyboard (`VID_36AE`, `PID_FE12`).

Zero third-party bloatware, zero flickering, direct native USB HID control.

---

## ✨ Features

1. **🎵 Music Album Art Sync (Default Mode)**
   - Automatically detects whatever song or video you are playing (Spotify, YouTube, Apple Music, VLC, browser players).
   - Extracts or fetches the official album cover art.
   - Intelligently extracts the most punchy, vibrant dominant color.
   - Updates your keyboard smoothly without flickering.
   - When music pauses, softly returns to the default dynamic rainbow wave.

2. **🖥️ Screen Ambient Sync (`--screen`)**
   - Samples your primary monitor in real-time and reflects on-screen colors directly onto your keyboard.

3. **🛡️ 100% Safe Hardware Control**
   - Communicates directly with Vendor Interface 2 (`MI_02`).
   - Does not touch or interrupt standard typing inputs (`MI_00`).
   - Includes instant 1-click restore/undo scripts.

---

## 🚀 How to Run

### Option 1: 1-Click Launchers (Easiest)
- Double-click **`Run_Music_Sync.bat`** to start syncing with your music.
- Double-click **`Run_Screen_Sync.bat`** to start syncing with your screen.
- Double-click **`Reset_Keyboard_To_Rainbow.bat`** anytime to restore default rainbow lighting.

### Option 2: Command Line
```powershell
# Music sync mode
python sync_music.py

# Keep current color when music pauses (instead of rainbow)
python sync_music.py --keep

# Screen ambient sync mode
python sync_music.py --screen
```

---

## 🔄 Emergency / Factory Reset
If you ever want to reset the keyboard back to standard hardware defaults:
- Double-click **`Reset_Keyboard_To_Rainbow.bat`** or run `python undo_reset.py`
- **Hardware shortcut:** You can also press and hold **`Fn + Space`** for 3–5 seconds directly on the keyboard at any time.
