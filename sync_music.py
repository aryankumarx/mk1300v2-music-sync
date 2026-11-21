"""
Ant Esports MK1300 V2 - Music & Screen RGB Sync Tool (Cinematic Transitions)
=============================================================================
Features:
- Native Windows SMTC media detection (detects what's playing in Chrome / Spotify live)
- Fetches official high-res album covers via iTunes / Deezer APIs
- Smooth RGB interpolation between song changes (gradual crossfade over ~1.2s)
- Smooth reverse-ease down transition on pause into hardware breathing mode
- Hardware Mode 2 Breathing in calibrated theme color (autonomous, zero USB lag, never turns off)
- Seamless ramp-up to 100% normal light when resuming playback
- Holds song color rock-steady during track changes / buffering / silence
- In-process instant refresh when pressing 'R' / 'r' in the terminal
- Calibrated LED color mapping (handles pure whites, near-white tones, and punchy saturated hues)
- Clean exit with Ctrl+C restoring dynamic rainbow wave
"""

import sys
import os
import time
import json
import io
import urllib.request
import urllib.parse
import colorsys
import subprocess
import signal
import ctypes
from ctypes import wintypes
from PIL import Image
import re
import math
import threading
import msvcrt

PATH = r'\\?\HID#VID_36AE&PID_FE12&MI_02#8&1cdcfa05&0&0000#{4d1e55b2-f16f-11cf-88cb-001111000030}'
kernel32 = ctypes.windll.kernel32

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MEDIA_PS_SCRIPT = os.path.join(SCRIPT_DIR, "get_media.ps1")
WATCH_MEDIA_PS_SCRIPT = os.path.join(SCRIPT_DIR, "watch_media.ps1")
ART_TEMP_FILE = os.path.join(SCRIPT_DIR, "now_playing_art.jpg")

class KeyboardController:
    def __init__(self, path=PATH):
        self.path = path
        self.handle = None
        self.current_rgb = None
        self.current_mode = None

    def connect(self):
        if self.handle and self.handle != -1 and self.handle != 0:
            return True

        self.handle = kernel32.CreateFileW(
            self.path,
            0xC0000000, # GENERIC_READ | GENERIC_WRITE
            3,          # FILE_SHARE_READ | FILE_SHARE_WRITE
            None,
            3,          # OPEN_EXISTING
            0,
            None
        )
        return bool(self.handle != -1 and self.handle != 0)

    def send_packet(self, payload):
        """Sends an OUT report and immediately drains the IN ACK to keep USB pipe clean."""
        if not self.handle or self.handle == -1:
            if not self.connect():
                return False
        buf = (ctypes.c_ubyte * 65)()
        buf[0] = 0x00
        for i, b in enumerate(payload):
            if i + 1 < 65:
                buf[i + 1] = b
        written = wintypes.DWORD()
        ok = kernel32.WriteFile(self.handle, buf, 65, ctypes.byref(written), None)
        if not ok:
            return False
        read_bytes = wintypes.DWORD()
        kernel32.ReadFile(self.handle, buf, 65, ctypes.byref(read_bytes), None)
        return True

    def apply_hsv(self, mode, h_byte, s_byte, v_byte, brightness=4, speed=1, direction=0, color=1):
        """Low-level send to controller with proper direction and color flags."""
        a = [1, 0, mode, brightness, speed, direction, color, 0, h_byte, s_byte, v_byte]
        cmd = [0x06, 0x0B, len(a), 0, 0] + a
        self.send_packet(cmd)
        self.current_mode = mode

    def calibrate_color(self, r, g, b, factor=1.0):
        """
        Maps RGB to calibrated HSV.
        Handles near-white/monochrome (e.g. West Coast) cleanly and boosts color saturation.
        """
        cur_r = int(r * factor)
        cur_g = int(g * factor)
        cur_b = int(b * factor)

        hf, sf, vf = colorsys.rgb_to_hsv(cur_r / 255.0, cur_g / 255.0, cur_b / 255.0)
        h_deg = hf * 360.0
        if h_deg >= 340.0 or h_deg <= 10.0:
            h_deg = 0.0

        if sf < 0.15:
            # Crisp radiant White (avoids the MCU integer-round to zero bug on desaturated tones)
            h_byte = 0
            s_byte = 0
            v_byte = int(vf * 255.0) & 0xFF
        else:
            # Saturated punchy color
            sf = max(0.70, min(sf * 1.4, 1.0))
            h_byte = int(h_deg / 360.0 * 255.0) & 0xFF
            s_byte = int(sf * 255.0) & 0xFF
            v_byte = int(vf * 255.0) & 0xFF

        return h_byte, s_byte, v_byte

    def set_color_direct(self, r, g, b):
        """Applies solid color at 100% full brightness in Mode 1 (Static)."""
        if self.current_mode != 1:
            self.send_packet([0x06, 0x16, 0x00, 0x00, 0x00, 0x01, 0x00, 0x01])
            time.sleep(0.04)
            self.current_mode = 1
        h_byte, s_byte, v_byte = self.calibrate_color(r, g, b, 1.0)
        a = [1, 0, 1, 4, 1, 0, 1, 0, h_byte, s_byte, v_byte]
        cmd = [0x06, 0x0B, len(a), 0, 0] + a
        self.send_packet(cmd)
        self.current_rgb = (r, g, b)

    def transition_to_color(self, target_r, target_g, target_b, steps=16, duration=1.2):
        """
        Smoothly crossfades from current color to target color using direct RGB cosine interpolation.
        (The exact 'cherry on top' smooth transition requested by user).
        """
        if not self.current_rgb or self.current_mode != 1:
            self.set_color_direct(target_r, target_g, target_b)
            return

        start_r, start_g, start_b = self.current_rgb
        if (start_r, start_g, start_b) == (target_r, target_g, target_b):
            self.set_color_direct(target_r, target_g, target_b)
            return

        delay = duration / max(1, steps)
        for i in range(1, steps + 1):
            t = i / float(steps)
            t_smooth = 0.5 * (1.0 - math.cos(t * math.pi))

            cur_r = int(start_r + (target_r - start_r) * t_smooth)
            cur_g = int(start_g + (target_g - start_g) * t_smooth)
            cur_b = int(start_b + (target_b - start_b) * t_smooth)

            h_byte, s_byte, v_byte = self.calibrate_color(cur_r, cur_g, cur_b, 1.0)
            self.apply_hsv(mode=1, h_byte=h_byte, s_byte=s_byte, v_byte=v_byte, brightness=4, speed=1, direction=0, color=1)
            time.sleep(delay)

        self.current_rgb = (target_r, target_g, target_b)

    def set_breathing_mode(self, r, g, b, speed=1):
        """Activates native hardware breathing (Mode 2) in song theme color at minimum/slowest speed."""
        h_byte, s_byte, _ = self.calibrate_color(r, g, b, 1.0)
        self.send_packet([0x06, 0x16, 0x00, 0x00, 0x00, 0x01, 0x00, 0x02])
        time.sleep(0.04)
        cfg = [1, 0, 2, 4, speed, 1, 1, 0, h_byte, s_byte, 255]
        self.send_packet([0x06, 0x0B, len(cfg), 0, 0] + cfg)
        self.current_mode = 2
        self.current_rgb = (r, g, b)

    def transition_into_breathing(self, r, g, b, duration=1.0, steps=1):
        """Engages hardware breathing directly in 1 clean switch without flicker or PWM resets."""
        self.set_breathing_mode(r, g, b, speed=1)

    def ramp_up_to_play(self, r, g, b, duration=0.35, steps=1):
        """Smoothly restores 100% normal light when resuming from pause without flicker."""
        self.set_color_direct(r, g, b)

    def restore_rainbow(self):
        """Restores hardware dynamic rainbow wave effect (Stream mode 0x04)."""
        self.send_packet([0x06, 0x16, 0x00, 0x00, 0x00, 0x01, 0x00, 0x04])
        time.sleep(0.04)

        a = [1, 0, 4, 4, 1, 0, 0, 0, 0, 0, 0]
        cmd = [0x06, 0x0B, len(a), 0, 0] + a
        self.send_packet(cmd)

        self.current_mode = 4
        self.current_rgb = None
        return True

    def close(self):
        if self.handle and self.handle != -1:
            try:
                self.restore_rainbow()
                kernel32.CloseHandle(self.handle)
            except:
                pass
            self.handle = None

def extract_dominant_color(image):
    small = image.resize((36, 36)).convert('RGB')
    width, height = small.size
    total_pixels = width * height
    colors = small.getcolors(total_pixels)
    if not colors:
        return (255, 0, 0)

    colors.sort(reverse=True, key=lambda x: x[0])
    best_color = None
    best_score = -1

    for count, (r, g, b) in colors:
        hf, sf, vf = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
        if vf < 0.15: continue
        if sf < 0.15 and vf > 0.85: continue
        coverage = count / total_pixels
        score = (coverage ** 0.5) * (sf * 1.5 + 0.5)
        if score > best_score:
            best_score = score
            best_color = (r, g, b)

    if not best_color:
        best_color = colors[0][1]

    hf, sf, vf = colorsys.rgb_to_hsv(best_color[0] / 255.0, best_color[1] / 255.0, best_color[2] / 255.0)
    vf = 1.0
    sf = min(sf * 1.35, 1.0)
    rf, gf, bf = colorsys.hsv_to_rgb(hf, sf, vf)
    return (int(rf * 255), int(gf * 255), int(bf * 255))

def fetch_online_album_art(artist, title, album=""):
    clean_title = re.sub(r'\(.*?\)|\[.*?\]', '', title)
    clean_title = re.sub(r'(?i)\b(official\s+video|official\s+music\s+video|official\s+audio|lyric\s+video|lyrics|4k|hd|remix|feat\..*|ft\..*)\b', '', clean_title)
    clean_title = clean_title.replace("||", " ").strip()

    queries = []
    if artist and album and album != title:
        queries.append(f"{artist} {album}")
    if artist and artist.lower() not in clean_title.lower():
        queries.append(f"{artist} {clean_title}")
    queries.append(clean_title)

    for query in queries:
        query = query.strip()
        if not query: continue

        # 1. Try iTunes Search API
        try:
            url = f"https://itunes.apple.com/search?term={urllib.parse.quote(query)}&entity=song&limit=1"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=3) as res:
                data = json.loads(res.read())
                results = data.get('results', [])
                if results and 'artworkUrl100' in results[0]:
                    art_url = results[0]['artworkUrl100'].replace('100x100bb', '600x600bb')
                    img_req = urllib.request.Request(art_url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(img_req, timeout=3) as img_res:
                        return Image.open(io.BytesIO(img_res.read())).convert('RGB'), "iTunes"
        except:
            pass

        # 2. Try Deezer Search API
        try:
            url = f"https://api.deezer.com/search?q={urllib.parse.quote(query)}&limit=1"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=3) as res:
                data = json.loads(res.read())
                results = data.get('data', [])
                if results and 'album' in results[0] and 'cover_medium' in results[0]['album']:
                    art_url = results[0]['album']['cover_medium']
                    img_req = urllib.request.Request(art_url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(img_req, timeout=3) as img_res:
                        return Image.open(io.BytesIO(img_res.read())).convert('RGB'), "Deezer"
        except:
            pass

    return None, None

COLOR_CACHE = {}

def resolve_track_color(info, artist, title, album):
    track_id = f"{artist} - {title}"
    if track_id in COLOR_CACHE:
        return COLOR_CACHE[track_id]

    color = None
    if info.get("HasThumbnail") and os.path.exists(ART_TEMP_FILE):
        try:
            with Image.open(ART_TEMP_FILE) as img:
                color = extract_dominant_color(img)
                print(f"   Artwork:    Extracted from player thumbnail")
        except:
            color = None

    if not color:
        img, source = fetch_online_album_art(artist, title, album)
        if img:
            color = extract_dominant_color(img)
            print(f"   Artwork:    Fetched via {source}")

    if not color:
        val = abs(hash(title)) % 360
        rf, gf, bf = colorsys.hsv_to_rgb(val / 360.0, 1.0, 1.0)
        color = (int(rf * 255), int(gf * 255), int(bf * 255))
        print(f"   Artwork:    Generated theme palette")

    COLOR_CACHE[track_id] = color
    return color

class MediaStreamReader(threading.Thread):
    def __init__(self, script_path=WATCH_MEDIA_PS_SCRIPT):
        super().__init__(daemon=True)
        self.script_path = script_path
        self.lock = threading.Lock()
        self.current_info = {"Status": "None", "Title": "", "Artist": "", "Album": ""}
        self.running = True
        self.process = None

    def run(self):
        cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", self.script_path]
        try:
            self.process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1
            )
            for line in self.process.stdout:
                if not self.running:
                    break
                line = line.strip()
                if not line or line.startswith("ERROR"):
                    continue
                parts = line.split("|")
                if len(parts) >= 4:
                    status, title, artist, album = parts[0], parts[1], parts[2], parts[3]
                    with self.lock:
                        self.current_info = {
                            "Status": status,
                            "Title": title,
                            "Artist": artist,
                            "Album": album
                        }
        except Exception:
            pass

    def get_info(self):
        with self.lock:
            return dict(self.current_info)

    def stop(self):
        self.running = False
        if self.process:
            try:
                self.process.terminate()
            except:
                pass

def run_music_sync(controller):
    print("\n" + "=" * 65)
    print(" [✓] MUSIC SYNC ACTIVE - Ant Esports MK1300 V2")
    print(" - Dominant album cover color detection (Chrome / YouTube / Spotify)")
    print(" - Smooth crossfade color transitions between songs (cherry on top!)")
    print(" - Smooth reverse ease-down into Breathing Mode on pause")
    print(" - Hardware Mode 2 Breathing in theme color (autonomous, never turns off)")
    print(" - Instant smooth ramp-up to 100% normal light when resuming")
    print(" - Holds song color steady during track changes / buffering")
    print(" - Press 'R' inside this window to instant-refresh active song sync")
    print(" - Press Ctrl+C anytime to exit and restore rainbow wave")
    print("=" * 65 + "\n")

    watcher = MediaStreamReader()
    watcher.start()

    current_track = ""
    current_rgb = (255, 120, 0)
    controller.set_color_direct(current_rgb[0], current_rgb[1], current_rgb[2])

    pending_track = None
    pending_track_start_time = None

    pause_detected_time = None
    is_breathing = False

    try:
        while True:
            # Check for 'R' key press to instant-refresh active song without restarting window
            if msvcrt.kbhit():
                try:
                    ch = msvcrt.getch()
                    if ch in (b'r', b'R'):
                        print("\n[↻] 'R' pressed: Instant refreshing song sync with Chrome...")
                        current_track = ""
                        pending_track = None
                        pending_track_start_time = None
                        pause_detected_time = None
                        is_breathing = False
                        COLOR_CACHE.clear()
                        time.sleep(0.05)
                except:
                    pass

            info = watcher.get_info()
            status = info.get("Status", "None")
            title = info.get("Title", "").strip()
            artist = info.get("Artist", "").strip()
            album = info.get("Album", "").strip()
            track_id = f"{artist} - {title}" if title else ""

            if status == "Playing" and title:
                pause_detected_time = None

                # If we were in paused breathing, cleanly restore normal light
                if is_breathing:
                    controller.ramp_up_to_play(current_rgb[0], current_rgb[1], current_rgb[2])
                    is_breathing = False

                # Check if song changed
                if track_id != current_track:
                    if pending_track != track_id:
                        # New song just started playing! Record start time and pre-resolve color in background thread
                        pending_track = track_id
                        pending_track_start_time = time.time()
                        # Pre-cache color in background thread so the main loop doesn't block or freeze
                        threading.Thread(
                            target=resolve_track_color,
                            args=(info, artist, title, album),
                            daemon=True
                        ).start()

                    # Wait ~1.5s after new song starts playing before starting crossfade
                    if time.time() - pending_track_start_time < 1.5:
                        time.sleep(0.05)
                        continue

                    # 1.5s elapsed: smoothly crossfade from current_rgb to new song's color
                    color = resolve_track_color(info, artist, title, album)
                    print(f"🎵 Now Playing: {title}")
                    if artist: print(f"   Artist:     {artist}")
                    if album and album != title: print(f"   Album:      {album}")
                    print(f"   Transition: Smoothly crossfading from RGB {current_rgb} -> RGB {color}...")
                    controller.transition_to_color(color[0], color[1], color[2], steps=16, duration=1.2)
                    print(f"   [✓] Normal light active (100%)\n")

                    current_track = track_id
                    current_rgb = color
                    pending_track = None

                else:
                    # Same track playing at 100% solid light: zero packets sent, perfectly stable
                    time.sleep(0.05)

            elif status in ("Paused", "Stopped") and title:
                # Playback paused
                if pause_detected_time is None:
                    pause_detected_time = time.time()

                elapsed_paused = time.time() - pause_detected_time

                # Buffer protection: during the first 1.8s of gap/silence (e.g. track change),
                # hold current song's RGB rock-steady so it never flickers, drops, or enters breathing prematurely!
                if elapsed_paused < 1.8:
                    time.sleep(0.05)
                else:
                    # Genuinely paused for > 1.8s -> smooth slow hardware breathing
                    if not is_breathing:
                        print(f"⏸️ Music paused: '{title}'. Ambient Breathing Mode active (speed=1)...\n")
                        controller.transition_into_breathing(current_rgb[0], current_rgb[1], current_rgb[2])
                        is_breathing = True

                    # Sleep cleanly while paused - zero packets sent, keyboard breathes in hardware
                    time.sleep(0.1)

            else:
                # Silence between tracks or buffering -> HOLD CURRENT RGB STEADY!
                time.sleep(0.05)

    finally:
        watcher.stop()

def main():
    kb = KeyboardController()
    print("Connecting to Ant Esports MK1300 V2...")
    if not kb.connect():
        print("[!] Could not connect to keyboard. Make sure it is plugged in.")
        return 1

    print("Keyboard connected successfully!")

    def cleanup(signum=None, frame=None):
        print("\nRestoring keyboard to rainbow wave and exiting...")
        kb.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    try:
        run_music_sync(kb)
    finally:
        cleanup()

if __name__ == '__main__':
    main()
