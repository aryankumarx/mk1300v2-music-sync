import ctypes
from ctypes import wintypes
import time

PATH = r'\\?\HID#VID_36AE&PID_FE12&MI_02#8&1cdcfa05&0&0000#{4d1e55b2-f16f-11cf-88cb-001111000030}'
kernel32 = ctypes.windll.kernel32

# Standard ANSI 60% physical matrix mapping for this keyboard controller:
# Pos 0..14: Row 0 (Number row)
#   0: `~ (0x35)
#   1: 1 (0x1E)
#   2: 2 (0x1F)
#   3: 3 (0x20)
#   4: 4 (0x21)
#   5: 5 (0x22)
#   6: 6 (0x23)
#   7: 7 (0x24)
#   8: 8 (0x25)
#   9: 9 (0x26)
#  10: 0 (0x27)
#  11: -_ (0x2D)
#  12: =+ (0x2E)
#  13: Backspace (0x2A)
#  14: Placeholder / Del (0x4C)

# Pos 15..29: Row 1 (QWERTY row)
#  15: Tab (0x2B)
#  16: Q (0x14)
#  17: W (0x1A)
#  18: E (0x08)
#  19: R (0x15)
#  20: T (0x17)
#  21: Y (0x1C)
#  22: U (0x18)
#  23: I (0x0C)
#  24: O (0x12)
#  25: P (0x13)
#  26: [{ (0x2F)
#  27: ]} (0x30)
#  28: \| (0x31)
#  29: (Placeholder)

# Pos 30..44: Row 2 (Home row)
#  30: CapsLock (0x39)
#  31: A (0x04)
#  32: S (0x16)
#  33: D (0x07)
#  34: F (0x09)
#  35: G (0x0A)
#  36: H (0x0B)
#  37: J (0x0D)
#  38: K (0x0E)
#  39: L (0x0F)
#  40: ;: (0x33)
#  41: '" (0x34)
#  42: (ISO key or Enter)
#  43: Enter (0x28)
#  44: (Placeholder)

# Let's verify positions 41..44:
# In dump, pos 43 is already Enter (0x28)! Pos 42 is 0x32 (non-US # or enter). Pos 41 was corrupted.
# Pos 45: LShift (0x02 mod) - intact!
# Pos 46: 0x64 (non-US \)
# Pos 47: Z (0x1D) - intact!
# Pos 48: X (0x1B) - intact!
# Pos 49: C (0x06) - intact!
# Pos 50: V (0x19) - intact!
# Pos 51: B (0x05) - intact!
# Pos 52: N (0x11) - intact!
# Pos 53: M (0x10) - intact!
# Pos 54: ,< (0x36) - intact!
# Pos 55: .> (0x37) - intact!
# Pos 56: /? (0x38) - intact!
# Pos 57: 0x87 (Int'l 1)
# Pos 58: RShift (0x20 mod) - intact!
# Pos 59: Up / PgDn (0x4E) - intact!
# Pos 60: LCtrl (0x01 mod) - intact!
# Pos 61: LWin (0x08 mod) - intact!
# Pos 62: LAlt (0x04 mod) - intact!
# Pos 66: Space (0x2C) - intact!

# Positions that need restoration: pos 0 through 42!
ROW0_KEYS = [
    (0,  0x29), # Esc (or `~)
    (1,  0x1E), # 1
    (2,  0x1F), # 2
    (3,  0x20), # 3
    (4,  0x21), # 4
    (5,  0x22), # 5
    (6,  0x23), # 6
    (7,  0x24), # 7
    (8,  0x25), # 8
    (9,  0x26), # 9
    (10, 0x27), # 0
    (11, 0x2D), # -
    (12, 0x2E), # =
    (13, 0x2A), # Backspace
    (14, 0x13), # Placeholder
]

ROW1_KEYS = [
    (15, 0x2B), # Tab
    (16, 0x14), # Q
    (17, 0x1A), # W
    (18, 0x08), # E
    (19, 0x15), # R
    (20, 0x17), # T
    (21, 0x1C), # Y
    (22, 0x18), # U
    (23, 0x0C), # I
    (24, 0x12), # O
    (25, 0x13), # P
    (26, 0x2F), # [
    (27, 0x30), # ]
    (28, 0x31), # \
    (29, 0x13), # Placeholder
]

ROW2_KEYS = [
    (30, 0x39), # CapsLock
    (31, 0x04), # A
    (32, 0x16), # S
    (33, 0x07), # D
    (34, 0x09), # F
    (35, 0x0A), # G
    (36, 0x0B), # H
    (37, 0x0D), # J
    (38, 0x0E), # K
    (39, 0x0F), # L
    (40, 0x33), # ;
    (41, 0x34), # '
]

# Check bottom row keys:
# Pos 70..80: Right Alt, Fn, Menu, RCtrl
BOTTOM_ROW_RESTORE = [
    (70, 0x00, 0x04), # RAlt (mod 0x40 or 0x04)
    (71, 0x00, 0xFF), # Fn (0x20, 0x00, 0xFF, 0x00)
    (72, 0x00, 0x65), # Menu
    (73, 0x00, 0x10), # RCtrl (mod 0x10)
]

def make_entry(val):
    if val == 0x13:
        return [0x13, 0x00, 0x00, 0x00] # placeholder
    if val == 0xFF:
        return [0x20, 0x00, 0xFF, 0x00] # Fn key
    return [0x20, 0x00, val, 0x00]     # standard key

def restore_keys():
    print("Opening keyboard handle...")
    h = kernel32.CreateFileW(PATH, 0xC0000000, 3, None, 3, 0, None)
    if h == -1:
        print("Cannot open keyboard handle!")
        return False

    written = wintypes.DWORD()
    read_bytes = wintypes.DWORD()

    all_to_restore = []
    for pos, code in ROW0_KEYS:
        all_to_restore.append((pos, make_entry(code)))
    for pos, code in ROW1_KEYS:
        all_to_restore.append((pos, make_entry(code)))
    for pos, code in ROW2_KEYS:
        all_to_restore.append((pos, make_entry(code)))
    # Bottom modifiers
    all_to_restore.append((70, [0x20, 0x40, 0x00, 0x00])) # RAlt
    all_to_restore.append((71, [0x20, 0x00, 0xFF, 0x00])) # Fn key
    all_to_restore.append((72, [0x20, 0x00, 0x65, 0x00])) # App/Menu
    all_to_restore.append((73, [0x20, 0x10, 0x00, 0x00])) # RCtrl

    print(f"Restoring {len(all_to_restore)} keys into keyboard flash...")
    success_count = 0
    for pos, entry in all_to_restore:
        # Command: 06 10 07 [4*pos] 00 00 00 00 [4-byte entry]
        cmd = [0x06, 0x10, 0x07, 4 * pos, 0, 0, 0, 0] + entry
        buf = (ctypes.c_ubyte * 65)()
        for i, b in enumerate(cmd):
            buf[i + 1] = b
        kernel32.WriteFile(h, buf, 65, ctypes.byref(written), None)
        
        # Read reply (must have status 0x01 in byte 3)
        in_buf = (ctypes.c_ubyte * 65)()
        if kernel32.ReadFile(h, in_buf, 65, ctypes.byref(read_bytes), None) and read_bytes.value > 3:
            if in_buf[3] == 0x01:
                success_count += 1
            else:
                print(f"Warning: pos {pos} status {in_buf[3]:02X}")
        time.sleep(0.015)

    print(f"Successfully restored {success_count} / {len(all_to_restore)} keys!")
    kernel32.CloseHandle(h)
    return True

if __name__ == '__main__':
    restore_keys()

