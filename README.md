# MK1300 V2 Sync

Custom RGB music and screen sync for the Ant Esports MK1300 V2 mechanical keyboard.

A lightweight, standalone Python controller that talks to the keyboard directly over USB HID. No vendor software, no third-party RGB suites, no flicker.

[![Platform](https://img.shields.io/badge/platform-Windows-0078D6?style=flat-square)](https://github.com/aryankumarx/mk1300v2-music-sync)
[![Python](https://img.shields.io/badge/python-3.x-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Device](https://img.shields.io/badge/device-Ant%20Esports%20MK1300%20V2-orange?style=flat-square)](https://antesports.com/)

---

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Supported Hardware](#supported-hardware)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [How It Works](#how-it-works)
- [Safety and Reset](#safety-and-reset)
- [Troubleshooting](#troubleshooting)
- [Project Structure](#project-structure)
- [Disclaimer](#disclaimer)

---

## Overview
The stock lighting on the MK1300 V2 is limited to preset effects. This project replaces that with colours that follow what you are actually doing: the album art of the song you are playing, or the colours on your screen.

It writes only to the keyboard's vendor lighting interface, so normal typing is never affected.

---

## Features
| Mode | What it does |
| :--- | :--- |
| **Music sync (default)** | Detects the currently playing track from Spotify, YouTube, Apple Music, VLC or a browser player, fetches the cover art, and extracts the most vivid dominant colour. |
| **Screen sync** | Samples your primary monitor in real time and mirrors the on-screen colour onto the keyboard. |
| **Idle behaviour** | When playback stops, the keyboard returns to the default rainbow wave. Use `--keep` to hold the last colour instead. |
| **Smooth output** | Colour transitions are blended between updates to avoid flicker. |
| **One-click recovery** | Dedicated reset scripts restore the factory lighting at any time. |

---

## Supported Hardware
| Property | Value |
| :--- | :--- |
| **Keyboard** | Ant Esports MK1300 V2 |
| **Vendor ID** | `36AE` |
| **Product ID** | `FE12` |
| **Control interface** | Vendor interface `MI_02` |
| **Typing interface** | `MI_00` (never touched) |
| **Operating system** | Windows |

*Other keyboards are not supported unless they report the same VID and PID.*

---

## Quick Start
```bash
# 1. Clone the repository
git clone https://github.com/aryankumarx/mk1300v2-music-sync.git
cd mk1300v2-music-sync

# 2. Install dependencies
pip install -r requirements.txt
```

Then either double-click one of the launcher files, or run the scripts from a terminal as shown below.

---

## Usage

### One-click launchers
| File | Action |
| :--- | :--- |
| `Run_Music_Sync.bat` | Start syncing with your music |
| `Run_Screen_Sync.bat` | Start syncing with your screen |
| `Reset_Keyboard_To_Rainbow.bat` | Restore default rainbow lighting |
| `Fix_Keyboard_Keys.bat` | Restore key bindings if unmapped |

### Command line
```bash
# Music sync (default)
python sync_music.py

# Hold the current colour when music pauses, instead of returning to rainbow
python sync_music.py --keep

# Screen ambient sync
python sync_music.py --screen
```

### Options
| Flag | Description |
| :--- | :--- |
| *(none)* | Music album-art sync with rainbow fallback |
| `--keep` | Keep the last colour when playback pauses |
| `--screen` | Sync to the primary monitor instead of music |

---

## How It Works

```text
    Music mode                                Screen mode
    ----------                                -----------
Now-playing detection                    Capture primary monitor
         |                                          |
Fetch album cover art                      Average screen colour
         |                                          |
Extract vibrant dominant colour                     |
         |                                          |
         +--------------------+---------------------+
                              |
                     Smooth colour blending
                              |
             USB HID write to vendor interface MI_02
                              |
                    MK1300 V2 keyboard
```

The colour extraction favours saturated, high-contrast tones over muddy averages, so dark or washed-out album covers still produce a clear, punchy result.

---

## Safety and Reset
- Communication is limited strictly to vendor interface `MI_02`.
- The standard typing interface `MI_00` is never opened, so keystrokes are unaffected.
- Nothing is flashed to the keyboard firmware during RGB sync.

If the lighting or keyboard ever ends up in an unexpected state, use either method below:

| Method | Steps |
| :--- | :--- |
| **Script** | Double-click `Reset_Keyboard_To_Rainbow.bat`, or run `python undo_reset.py` |
| **Hardware** | Hold `Fn + Space` for 3 to 5 seconds on the keyboard |
| **Key Repair** | Double-click `Fix_Keyboard_Keys.bat` if keys ever become unmapped after a hardware reset |

---

## Troubleshooting
| Problem | Suggested fix |
| :--- | :--- |
| **Keyboard does not respond** | Confirm the device reports VID `36AE` and PID `FE12` in Device Manager. |
| **Colours do not change** | Close the official Ant Esports software, since two programs cannot control the device at once. |
| **Song not detected** | Make sure your player is publishing media info to Windows, and that something is actively playing. |
| **Lighting stuck on one colour** | Run `Reset_Keyboard_To_Rainbow.bat`, or use `Fn + Space`. |

---

## Project Structure
```text
mk1300v2-music-sync/
├── sync_music.py                 # Main controller (music and screen modes)
├── undo_reset.py                 # Restores default lighting
├── restore_full_keymap.py        # Complete ANSI keymap restorer
├── Run_Music_Sync.bat            # Launcher for music sync
├── Run_Screen_Sync.bat           # Launcher for screen sync
├── Reset_Keyboard_To_Rainbow.bat # Launcher for reset
├── Fix_Keyboard_Keys.bat         # 1-click key restoration batch
├── requirements.txt              # Python dependencies
└── README.md                     # Documentation
```

---

## Disclaimer
This is an independent, community project. It is not affiliated with or endorsed by Ant Esports. It works by sending lighting commands over USB HID and does not modify keyboard firmware. Use at your own risk.

Built by [aryankumarx](https://github.com/aryankumarx).
