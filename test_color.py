"""
Ant Esports MK1300 V2 - Quick Color Test
Changes keyboard to solid Cyan for 3 seconds, then automatically restores rainbow wave.
"""

import ctypes
from ctypes import wintypes
import time
import sys 

PATH = r'\\?\HID#VID_36AE&PID_FE12&MI_02#8&1cdcfa05&0&0000#{4d1e55b2-f16f-11cf-88cb-001111000030}'
kernel32 = ctypes.windll.kernel32

def send_cmd(h, payload):
    buf = (ctypes.c_ubyte * 65)()
    buf[0] = 0x00
    for i, b in enumerate(payload):
        buf[i + 1] = b
    written = wintypes.DWORD()
    kernel32.WriteFile(h, buf, 65, ctypes.byref(written), None)

def read_reply(h):
    buf = (ctypes.c_ubyte * 65)()
    read_bytes = wintypes.DWORD()
    kernel32.ReadFile(h, buf, 65, ctypes.byref(read_bytes), None)
    return [buf[i] for i in range(read_bytes.value)]

def run_test():
    h = kernel32.CreateFileW(PATH, 0xC0000000, 3, None, 3, 0, None)
    if h == -1 or h == 0:
        print("[ERROR] Failed to open keyboard handle.")
        return

    try:
        # 1. Query profile
        send_cmd(h, [0x06, 0x0A])
        reply = read_reply(h)
        profile = reply[6] if len(reply) > 6 else 0x01
        print(f"Connected to keyboard. Current profile: 0x{profile:02X}")

        # 2. Set to Static Cyan (R=0, G=255, B=255)
        print("Setting keyboard to CYAN for 3 seconds...")
        cyan_cmd = [0x06, 0x0B, 0x0B, 0x00, 0x00, profile, 0x00, 0x01, 0x04, 0x01, 0x02, 0x00, 0x07, 0x00, 0xFF, 0xFF]
        send_cmd(h, cyan_cmd)
        time.sleep(3)

        # 3. Restore to Stream Rainbow Wave (Effect 0x04)
        print("Restoring back to default dynamic Rainbow Stream...")
        stream_cmd = [0x06, 0x16, 0x00, 0x00, 0x00, profile, 0x00, 0x04]
        send_cmd(h, stream_cmd)
        print("[DONE] Test complete! Keyboard returned to default rainbow mode.")

    finally:
        kernel32.CloseHandle(h)

if __name__ == '__main__':
    run_test()

