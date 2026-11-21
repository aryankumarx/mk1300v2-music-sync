"""
Ant Esports MK1300 V2 - Restore / Factory Reset Script
Restores default hardware lighting modes and settings safely.
"""

import ctypes
from ctypes import wintypes
import time
import sys

PATH = r'\\?\HID#VID_36AE&PID_FE12&MI_02#8&1cdcfa05&0&0000#{4d1e55b2-f16f-11cf-88cb-001111000030}'
GENERIC_READ_WRITE = 0xC0000000
FILE_SHARE_READ_WRITE = 3
OPEN_EXISTING = 3

kernel32 = ctypes.windll.kernel32

def open_keyboard():
    h = kernel32.CreateFileW(
        PATH,
        GENERIC_READ_WRITE,
        FILE_SHARE_READ_WRITE,
        None,
        OPEN_EXISTING,
        0,
        None
    )
    if h == -1 or h == 0:
        return None
    return h

def send_command(handle, payload):
    out_report = (ctypes.c_ubyte * 65)()
    out_report[0] = 0x00 # Report ID
    for idx, b in enumerate(payload):
        out_report[idx + 1] = b
    
    written = wintypes.DWORD()
    success = kernel32.WriteFile(handle, out_report, 65, ctypes.byref(written), None)
    return bool(success) and written.value == 65

def read_reply(handle):
    in_report = (ctypes.c_ubyte * 65)()
    read_bytes = wintypes.DWORD()
    success = kernel32.ReadFile(handle, in_report, 65, ctypes.byref(read_bytes), None)
    if success and read_bytes.value > 0:
        return [in_report[i] for i in range(read_bytes.value)]
    return None

def reset_to_factory_stream():
    print("Opening Ant Esports MK1300 V2 controller (MI_02)...")
    handle = open_keyboard()
    if not handle:
        print("[ERROR] Could not open keyboard interface. Is it plugged in?")
        return False

    try:
        # Step 1: Read current profile
        print("Querying current profile...")
        send_command(handle, [0x06, 0x0A])
        reply = read_reply(handle)
        profile = 0x01
        if reply and len(reply) > 6:
            profile = reply[6]
            print(f"Current Profile: 0x{profile:02X}")

        # Step 2: Set effect back to Stream / Rainbow Wave (Effect 0x04)
        # Command: 06 16 00 00 00 [profile] 00 [effect=0x04]
        print("Restoring default hardware dynamic rainbow effect (Stream)...")
        stream_cmd = [0x06, 0x16, 0x00, 0x00, 0x00, profile, 0x00, 0x04]
        send_command(handle, stream_cmd)
        time.sleep(0.05)

        # Step 3: Ensure brightness and speed are standard
        # Command: 06 0B 0B 00 00 [profile] 00 [effect=0x04] [bright=0x04] [spd_hi=0x01] [spd_lo=0x02] 00 07 [RGB]
        config_cmd = [0x06, 0x0B, 0x0B, 0x00, 0x00, profile, 0x00, 0x04, 0x04, 0x01, 0x02, 0x00, 0x07, 0xFF, 0x00, 0x00]
        send_command(handle, config_cmd)

        print("\n[SUCCESS] Keyboard lighting has been reset to default hardware rainbow stream!")
        print("Hardware shortcut reminder: You can also hold 'Fn + Space' for 3 seconds anytime on the keyboard.")
        return True
    finally:
        kernel32.CloseHandle(handle)

if __name__ == '__main__':
    reset_to_factory_stream()

