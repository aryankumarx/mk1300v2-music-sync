"""
Ant Esports MK1300 V2 - FULL FACTORY RESET
============================================
Sends the firmware factory reset command (06 0F FF) to restore ALL
keyboard settings to factory defaults: keymap, macros, colors, effects.

This is the nuclear option - it resets EVERYTHING.

After running this:
1. Unplug the keyboard
2. Wait 10 seconds
3. Plug it back in
4. Keys should work again, RGB should be back to default rainbow
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

def open_device():
    h = kernel32.CreateFileW(PATH, GENERIC_READ_WRITE, FILE_SHARE_READ_WRITE, None, OPEN_EXISTING, 0, None)
    if h == -1 or h == 0:
        err = kernel32.GetLastError()
        print(f"[ERROR] Cannot open keyboard (error {err})")
        if err == 5:
            print("[!] Access Denied - close SignalRGB and any other RGB software first!")
        return None
    return h

def send(handle, payload):
    buf = (ctypes.c_ubyte * 65)()
    buf[0] = 0x00
    for i, b in enumerate(payload):
        if i + 1 < 65:
            buf[i + 1] = b
    written = wintypes.DWORD()
    ok = kernel32.WriteFile(handle, buf, 65, ctypes.byref(written), None)
    return bool(ok)

def read_reply(handle, timeout_ms=500):
    buf = (ctypes.c_ubyte * 65)()
    read_bytes = wintypes.DWORD()
    ok = kernel32.ReadFile(handle, buf, 65, ctypes.byref(read_bytes), None)
    if ok and read_bytes.value > 0:
        return [buf[i] for i in range(read_bytes.value)]
    return None

def main():
    print("=" * 60)
    print("  ANT ESPORTS MK1300 V2 - FULL FACTORY RESET")
    print("=" * 60)
    print()

    h = open_device()
    if not h:
        return 1

    try:
        # Step 1: Query current state
        print("[1/5] Querying keyboard state...")
        send(h, [0x06, 0x0A])
        reply = read_reply(h)
        if reply:
            profile = reply[6] if len(reply) > 6 else 0x01
            print(f"      Profile: 0x{profile:02X}")
            print(f"      Reply bytes: {' '.join(f'{b:02X}' for b in reply[:16])}")
        else:
            print("      No reply (keyboard may be in stuck state)")
            profile = 0x01

        # Step 2: Send FACTORY RESET command (06 0F FF)
        print("[2/5] Sending factory reset command (06 0F FF)...")
        ok = send(h, [0x06, 0x0F, 0xFF])
        print(f"      WriteFile result: {'OK' if ok else 'FAILED'}")
        time.sleep(1.0)  # Give firmware time to process reset

        # Step 3: Try reading reply after reset
        print("[3/5] Reading post-reset reply...")
        reply2 = read_reply(h)
        if reply2:
            print(f"      Reply: {' '.join(f'{b:02X}' for b in reply2[:16])}")
        else:
            print("      No reply (expected after factory reset)")

        # Step 4: Try switching to default Stream/Rainbow effect
        print("[4/5] Setting default rainbow wave effect...")
        send(h, [0x06, 0x16, 0x00, 0x00, 0x00, 0x01, 0x00, 0x04])
        time.sleep(0.2)
        
        # Set default brightness & speed for rainbow
        config = [0x06, 0x0B, 0x0B, 0x00, 0x00, 0x01, 0x00, 0x04, 0x04, 0x01, 0x02, 0x00, 0x07, 0xFF, 0x00, 0x00]
        send(h, config)
        time.sleep(0.1)

        # Step 5: Verify
        print("[5/5] Verifying post-reset state...")
        send(h, [0x06, 0x0A])
        reply3 = read_reply(h)
        if reply3:
            print(f"      Post-reset reply: {' '.join(f'{b:02X}' for b in reply3[:16])}")
        
        print()
        print("=" * 60)
        print("  FACTORY RESET SENT!")
        print("=" * 60)
        print()
        print("  NOW DO THIS:")
        print("  1. UNPLUG your keyboard USB cable")
        print("  2. Wait 10 seconds")
        print("  3. PLUG IT BACK IN")
        print("  4. Test if keys work (type something)")
        print("  5. Check if RGB rainbow is back")
        print()
        print("  If keys STILL don't work after re-plugging:")
        print("  - Hold Fn + Esc for 5 seconds (alternate reset)")
        print("  - Or try Fn + Space for 5 seconds")
        print("  - If nothing works, we may need the web configurator")
        print()
        return 0

    finally:
        kernel32.CloseHandle(h)

if __name__ == '__main__':
    sys.exit(main())

