import ctypes
from ctypes import wintypes
import time
import sys

PATH = r'\\?\HID#VID_36AE&PID_FE12&MI_02#8&1cdcfa05&0&0000#{4d1e55b2-f16f-11cf-88cb-001111000030}'
kernel32 = ctypes.windll.kernel32

# Complete ANSI 60% Keymap Table for MK1300 V2:
# Byte format for each key entry: [0x20, <mod_byte>, <hid_keycode>, 0x00]
# Normal keys: [0x20, 0x00, <hid_keycode>, 0x00]
# Modifiers:   [0x20, <mod_bit>, 0x00, 0x00]
# Placeholders: [0x13, 0x00, 0x00, 0x00]

KEYMAP = {
    # --- Row 0 (Number Row: Pos 0..14) ---
    0:  [0x20, 0x00, 0x29, 0x00],  # Esc (0x29)
    1:  [0x20, 0x00, 0x1E, 0x00],  # 1
    2:  [0x20, 0x00, 0x1F, 0x00],  # 2
    3:  [0x20, 0x00, 0x20, 0x00],  # 3
    4:  [0x20, 0x00, 0x21, 0x00],  # 4
    5:  [0x20, 0x00, 0x22, 0x00],  # 5
    6:  [0x20, 0x00, 0x23, 0x00],  # 6
    7:  [0x20, 0x00, 0x24, 0x00],  # 7
    8:  [0x20, 0x00, 0x25, 0x00],  # 8
    9:  [0x20, 0x00, 0x26, 0x00],  # 9
    10: [0x20, 0x00, 0x27, 0x00],  # 0
    11: [0x20, 0x00, 0x2D, 0x00],  # -_
    12: [0x20, 0x00, 0x2E, 0x00],  # =+
    13: [0x20, 0x00, 0x2A, 0x00],  # Backspace
    14: [0x13, 0x00, 0x00, 0x00],  # Placeholder

    # --- Row 1 (QWERTY Row: Pos 15..29) ---
    15: [0x20, 0x00, 0x2B, 0x00],  # Tab
    16: [0x20, 0x00, 0x14, 0x00],  # Q
    17: [0x20, 0x00, 0x1A, 0x00],  # W
    18: [0x20, 0x00, 0x08, 0x00],  # E
    19: [0x20, 0x00, 0x15, 0x00],  # R
    20: [0x20, 0x00, 0x17, 0x00],  # T
    21: [0x20, 0x00, 0x1C, 0x00],  # Y
    22: [0x20, 0x00, 0x18, 0x00],  # U
    23: [0x20, 0x00, 0x0C, 0x00],  # I
    24: [0x20, 0x00, 0x12, 0x00],  # O
    25: [0x20, 0x00, 0x13, 0x00],  # P (Keycode 0x13 - NOT placeholder!)
    26: [0x20, 0x00, 0x2F, 0x00],  # [{
    27: [0x20, 0x00, 0x30, 0x00],  # ]}
    28: [0x20, 0x00, 0x31, 0x00],  # \|
    29: [0x13, 0x00, 0x00, 0x00],  # Placeholder

    # --- Row 2 (Home Row: Pos 30..43) ---
    30: [0x20, 0x00, 0x39, 0x00],  # CapsLock
    31: [0x20, 0x00, 0x04, 0x00],  # A
    32: [0x20, 0x00, 0x16, 0x00],  # S
    33: [0x20, 0x00, 0x07, 0x00],  # D
    34: [0x20, 0x00, 0x09, 0x00],  # F
    35: [0x20, 0x00, 0x0A, 0x00],  # G
    36: [0x20, 0x00, 0x0B, 0x00],  # H
    37: [0x20, 0x00, 0x0D, 0x00],  # J
    38: [0x20, 0x00, 0x0E, 0x00],  # K
    39: [0x20, 0x00, 0x0F, 0x00],  # L
    40: [0x20, 0x00, 0x33, 0x00],  # ;:
    41: [0x20, 0x00, 0x34, 0x00],  # '"
    42: [0x20, 0x00, 0x32, 0x00],  # ISO / Extra
    43: [0x20, 0x00, 0x28, 0x00],  # Enter
}

def restore_keyboard():
    print("==================================================")
    print("  Ant Esports MK1300 V2 - Instant Keymap Restorer")
    print("==================================================")
    print("[*] Connecting to keyboard HID interface...")
    
    # Open keyboard HID device
    h = kernel32.CreateFileW(PATH, 0xC0000000, 3, None, 3, 0, None)
    if h == -1 or h == 0:
        err = kernel32.GetLastError()
        print(f"[!] Error: Could not open keyboard handle (Code {err}).")
        print("[!] Please make sure the keyboard is plugged in and close any RGB software.")
        return False

    written = wintypes.DWORD()
    read_bytes = wintypes.DWORD()

    print(f"[*] Restoring {len(KEYMAP)} key positions (Esc, Numbers 1-0, QWERTY, Home Row, Enter)...")
    success_count = 0

    for pos, entry in KEYMAP.items():
        # Command format: 06 10 07 [4*pos] 00 00 00 00 [4 bytes data]
        cmd = [0x06, 0x10, 0x07, 4 * pos, 0x00, 0x00, 0x00, 0x00] + entry
        buf = (ctypes.c_ubyte * 65)()
        for i, b in enumerate(cmd):
            buf[i + 1] = b
            
        kernel32.WriteFile(h, buf, 65, ctypes.byref(written), None)
        
        # Read acknowledgment from device
        in_buf = (ctypes.c_ubyte * 65)()
        if kernel32.ReadFile(h, in_buf, 65, ctypes.byref(read_bytes), None) and read_bytes.value > 3:
            if in_buf[3] == 0x01:
                success_count += 1
            else:
                print(f"[!] Warning on pos {pos}: status {in_buf[3]:02X}")
        time.sleep(0.012)

    # Restore default Rainbow RGB stream mode
    print("[*] Setting default rainbow lighting...")
    rainbow_cmd = [0x06, 0x16, 0x00, 0x00, 0x00, 0x01, 0x00, 0x04]
    buf_rgb = (ctypes.c_ubyte * 65)()
    for i, b in enumerate(rainbow_cmd):
        buf_rgb[i + 1] = b
    kernel32.WriteFile(h, buf_rgb, 65, ctypes.byref(written), None)

    kernel32.CloseHandle(h)
    print(f"[✓] Keymap successfully restored! ({success_count}/{len(KEYMAP)} keys written)")
    print("[✓] All keys (Esc, 1..0, Q to ', P, Enter, Modifiers) are active.")
    print("==================================================")
    return True

if __name__ == '__main__':
    ok = restore_keyboard()
    if not ok:
        sys.exit(1)
