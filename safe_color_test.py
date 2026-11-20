"""
Safe Color Test for Ant Esports MK1300 V2
=========================================
Uses ONLY Opcode 0x14 (Write one key color) and Opcode 0x16 (Select effect).
NEVER uses chunked writes (0x12 / 0x18), so the keymap is 100% untouched.

Testing:
1. Switch to UserLight mode (0x07)
2. Set keys to Cyan RGB(0, 255, 255) via individual 0x14 commands
3. Wait 4 seconds
4. Restore default hardware Rainbow Stream (0x04)
"""

import ctypes
from ctypes import wintypes
import time
import sys

PATH = r'\\?\HID#VID_36AE&PID_FE12&MI_02#8&1cdcfa05&0&0000#{4d1e55b2-f16f-11cf-88cb-001111000030}'
kernel32 = ctypes.windll.kernel32

def open_device():
    h = kernel32.CreateFileW(PATH, 0xC0000000, 3, None, 3, 0, None)
    if h == -1 or h == 0:
        return None
    return h

def send_cmd(handle, payload):
    buf = (ctypes.c_ubyte * 65)()
    buf[0] = 0x00
    for i, b in enumerate(payload):
        if i + 1 < 65:
            buf[i + 1] = b
    written = wintypes.DWORD()
    return kernel32.WriteFile(handle, buf, 65, ctypes.byref(written), None)

def read_reply(handle):
    buf = (ctypes.c_ubyte * 65)()
    read_bytes = wintypes.DWORD()
    if kernel32.ReadFile(handle, buf, 65, ctypes.byref(read_bytes), None) and read_bytes.value > 0:
        return [buf[i] for i in range(read_bytes.value)]
    return None

def test_safe_color(r=0, g=255, b=255, duration=4):
    h = open_device()
    if not h:
        print("[!] Could not open keyboard handle.")
        return False

    try:
        # 1. Query profile
        send_cmd(h, [0x06, 0x0A])
        reply = read_reply(h)
        profile = reply[6] if reply and len(reply) > 6 else 0x01
        print(f"Active profile: 0x{profile:02X}")

        # 2. Switch to UserLight effect (0x07)
        print("Switching effect engine to UserLight (0x07)...")
        send_cmd(h, [0x06, 0x16, 0x00, 0x00, 0x00, profile, 0x00, 0x07])
        read_reply(h)
        time.sleep(0.3)  # Standard settle time for MCU

        # 3. Write individual key colors (positions 0 through 65)
        # Command: 06 14 03 [3*pos] 00 00 00 00 [R G B]
        print(f"Writing solid color RGB({r}, {g}, {b}) using safe Opcode 0x14...")
        for pos in range(65):
            color_cmd = [0x06, 0x14, 0x03, 3 * pos, 0x00, 0x00, 0x00, 0x00, r, g, b]
            send_cmd(h, color_cmd)
            read_reply(h)
            time.sleep(0.002)

        print(f"Color set! Keyboard should now be solid color. Waiting {duration}s...")
        time.sleep(duration)

        # 4. Restore Rainbow Stream (0x04)
        print("Restoring hardware dynamic Rainbow Wave...")
        send_cmd(h, [0x06, 0x16, 0x00, 0x00, 0x00, profile, 0x00, 0x04])
        read_reply(h)
        print("Done! Restored to Rainbow.")
        return True

    finally:
        kernel32.CloseHandle(h)

if __name__ == '__main__':
    test_safe_color(0, 255, 255, duration=4)

