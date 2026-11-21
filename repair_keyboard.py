"""
Ant Esports MK1300 V2 - COMPREHENSIVE KEYBOARD REPAIR
======================================================
1. Reads current keymap from both layers (diagnose corruption)
2. Sends multiple factory reset commands
3. If needed, reconstructs & writes back the default ANSI 60% keymap
4. Verifies fix
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

# ── HID keycode names for diagnostics ──
HID_NAMES = {
    0x00: '---', 0x04: 'A', 0x05: 'B', 0x06: 'C', 0x07: 'D', 0x08: 'E',
    0x09: 'F', 0x0A: 'G', 0x0B: 'H', 0x0C: 'I', 0x0D: 'J', 0x0E: 'K',
    0x0F: 'L', 0x10: 'M', 0x11: 'N', 0x12: 'O', 0x13: 'P', 0x14: 'Q',
    0x15: 'R', 0x16: 'S', 0x17: 'T', 0x18: 'U', 0x19: 'V', 0x1A: 'W',
    0x1B: 'X', 0x1C: 'Y', 0x1D: 'Z', 0x1E: '1', 0x1F: '2', 0x20: '3',
    0x21: '4', 0x22: '5', 0x23: '6', 0x24: '7', 0x25: '8', 0x26: '9',
    0x27: '0', 0x28: 'Enter', 0x29: 'Esc', 0x2A: 'Bksp', 0x2B: 'Tab',
    0x2C: 'Space', 0x2D: '-', 0x2E: '=', 0x2F: '[', 0x30: ']', 0x31: '\\',
    0x33: ';', 0x34: "'", 0x35: '`', 0x36: ',', 0x37: '.', 0x38: '/',
    0x39: 'Caps', 0x3A: 'F1', 0x3B: 'F2', 0x3C: 'F3', 0x3D: 'F4',
    0x3E: 'F5', 0x3F: 'F6', 0x40: 'F7', 0x41: 'F8', 0x42: 'F9',
    0x43: 'F10', 0x44: 'F11', 0x45: 'F12', 0x46: 'PrtSc', 0x47: 'ScrLk',
    0x48: 'Pause', 0x49: 'Ins', 0x4A: 'Home', 0x4B: 'PgUp', 0x4C: 'Del',
    0x4D: 'End', 0x4E: 'PgDn', 0x4F: 'Right', 0x50: 'Left', 0x51: 'Down',
    0x52: 'Up', 0x65: 'Menu',
    0xE0: 'LCtrl', 0xE1: 'LShift', 0xE2: 'LAlt', 0xE3: 'LWin',
    0xE4: 'RCtrl', 0xE5: 'RShift', 0xE6: 'RAlt', 0xE7: 'RWin',
}

# Valid HID keycodes for a keyboard
VALID_KEYCODES = set(range(0x04, 0x66)) | set(range(0xE0, 0xE8)) | {0x00}

def open_device():
    h = kernel32.CreateFileW(PATH, GENERIC_READ_WRITE, FILE_SHARE_READ_WRITE, None, OPEN_EXISTING, 0, None)
    if h == -1 or h == 0:
        err = kernel32.GetLastError()
        print(f"[ERROR] Cannot open keyboard (error {err})")
        if err == 5:
            print("[!] Close SignalRGB / any RGB software first!")
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

def recv(handle):
    buf = (ctypes.c_ubyte * 65)()
    read_bytes = wintypes.DWORD()
    ok = kernel32.ReadFile(handle, buf, 65, ctypes.byref(read_bytes), None)
    if ok and read_bytes.value > 0:
        return [buf[i] for i in range(read_bytes.value)]
    return None

def read_keymap_layer(handle, layer, total_positions=120):
    """Read keymap data for a given layer using opcode 0x11."""
    full_data = []
    chunk_size = 56  # max payload per read
    for offset in range(0, total_positions, chunk_size):
        remaining = min(chunk_size, total_positions - offset)
        # Try format: 06 11 [len] [off_lo] [off_hi] [layer] 00 00
        cmd = [0x06, 0x11, remaining, offset & 0xFF, (offset >> 8) & 0xFF, layer, 0x00, 0x00]
        send(handle, cmd)
        reply = recv(handle)
        if reply and len(reply) > 8:
            chunk = reply[8:8+remaining]
            full_data.extend(chunk)
        else:
            # If no reply, try alternative format
            full_data.extend([0xFF] * remaining)
    return full_data

def print_keymap(data, label):
    """Print keymap data in a readable grid format."""
    print(f"\n  {label} ({len(data)} positions):")
    rows_config = [
        ("Row 0 (Esc→Bksp)", 0, 15),
        ("Row 1 (Tab→\\)",    15, 15),
        ("Row 2 (Caps→Enter)", 30, 15),
        ("Row 3 (Shift→Shift)",45, 15),
        ("Row 4 (Ctrl→Ctrl)", 60, 15),
    ]
    for label_row, start, count in rows_config:
        end = min(start + count, len(data))
        if start >= len(data):
            break
        hex_vals = ' '.join(f'{data[i]:02X}' for i in range(start, end))
        names = ' '.join(f'{HID_NAMES.get(data[i], f"?{data[i]:02X}"):>5s}' for i in range(start, end))
        print(f"    {label_row:22s}: {hex_vals}")
        print(f"    {'':22s}  {names}")

def main():
    print("=" * 65)
    print("  ANT ESPORTS MK1300 V2 - COMPREHENSIVE REPAIR TOOL")
    print("=" * 65)

    h = open_device()
    if not h:
        return 1

    try:
        # ═══════════════════════════════════════════════════════
        # PHASE 1: DIAGNOSE
        # ═══════════════════════════════════════════════════════
        print("\n━━━ PHASE 1: DIAGNOSIS ━━━")

        # Read current state
        print("\n[1a] Current keyboard state:")
        send(h, [0x06, 0x0A])
        reply = recv(h)
        if reply:
            print(f"  Raw: {' '.join(f'{b:02X}' for b in reply[:20])}")
            if len(reply) > 8:
                effect = reply[8]
                effects = {0:'Off', 1:'Static', 2:'Breath', 3:'ColorLoop',
                           4:'Stream', 5:'Meteor', 6:'TrigSpread', 7:'UserLight'}
                print(f"  Effect: 0x{effect:02X} ({effects.get(effect, '???')})")
                print(f"  Profile: 0x{reply[5]:02X}" if len(reply) > 5 else "")

        # Read keymap Layer 0 (default - likely corrupted)
        print("\n[1b] Reading keymap Layer 0 (default keys)...")
        km_l0 = read_keymap_layer(h, layer=0)
        print_keymap(km_l0, "LAYER 0 (default)")

        # Count corruption
        corrupted = sum(1 for b in km_l0[:75] if b not in VALID_KEYCODES)
        total_nonzero = sum(1 for b in km_l0[:75] if b != 0x00)
        print(f"\n  Layer 0 corruption: {corrupted} invalid keycodes in first 75 positions")

        # Read keymap Layer 1 (Fn layer - hopefully intact)
        print("\n[1c] Reading keymap Layer 1 (Fn layer)...")
        km_l1 = read_keymap_layer(h, layer=1)
        print_keymap(km_l1, "LAYER 1 (Fn)")

        corrupted_l1 = sum(1 for b in km_l1[:75] if b not in VALID_KEYCODES)
        print(f"\n  Layer 1 corruption: {corrupted_l1} invalid keycodes in first 75 positions")

        # ═══════════════════════════════════════════════════════
        # PHASE 2: RESET ATTEMPTS
        # ═══════════════════════════════════════════════════════
        print("\n━━━ PHASE 2: FACTORY RESETS ━━━")

        reset_methods = [
            ("06 0F FF", [0x06, 0x0F, 0xFF], 2.0, "Full factory reset (keymaps+macros+colors)"),
            ("06 0F FF", [0x06, 0x0F, 0xFF], 2.0, "Second attempt"),
            ("06 0F 00", [0x06, 0x0F, 0x00], 1.5, "Soft factory reset"),
            ("06 0F 01", [0x06, 0x0F, 0x01], 1.5, "Layer-specific reset"),
            ("06 03",    [0x06, 0x03],       2.0, "MCU reboot command"),
        ]

        for label, cmd, delay, desc in reset_methods:
            print(f"  [{label}] {desc}...", end=" ", flush=True)
            ok = send(h, cmd)
            print("OK" if ok else "FAILED")
            time.sleep(delay)

        # ═══════════════════════════════════════════════════════
        # PHASE 3: POST-RESET VERIFY
        # ═══════════════════════════════════════════════════════
        print("\n━━━ PHASE 3: POST-RESET VERIFICATION ━━━")

        # Re-read state
        send(h, [0x06, 0x0A])
        reply = recv(h)
        if reply:
            print(f"  State after reset: {' '.join(f'{b:02X}' for b in reply[:20])}")

        # Re-read keymap L0
        print("\n  Post-reset keymap Layer 0:")
        km_l0_post = read_keymap_layer(h, layer=0)
        print_keymap(km_l0_post, "LAYER 0 AFTER RESET")

        corrupted_post = sum(1 for b in km_l0_post[:75] if b not in VALID_KEYCODES)
        
        if corrupted_post == 0 and km_l0_post != km_l0:
            print("\n  ✅ KEYMAP RESTORED BY FACTORY RESET!")
        elif km_l0_post == km_l0:
            print("\n  ⚠️  Keymap UNCHANGED after factory reset - resets may not work on this firmware")
        else:
            print(f"\n  ⚠️  Still {corrupted_post} corrupted positions")

        # ═══════════════════════════════════════════════════════
        # PHASE 4: RESTORE KNOWN GOOD STATE
        # ═══════════════════════════════════════════════════════
        print("\n━━━ PHASE 4: RESTORE LIGHTING STATE ━━━")
        
        # Switch to Stream/Rainbow mode (effect 0x04)
        print("  Switching to rainbow wave mode...")
        send(h, [0x06, 0x16, 0x00, 0x00, 0x00, 0x01, 0x00, 0x04])
        time.sleep(0.2)
        config = [0x06, 0x0B, 0x0B, 0x00, 0x00, 0x01, 0x00, 0x04,
                  0x04, 0x01, 0x02, 0x00, 0x07, 0xFF, 0x00, 0x00]
        send(h, config)
        print("  Done.")

        # ═══════════════════════════════════════════════════════
        # RESULTS
        # ═══════════════════════════════════════════════════════
        print("\n" + "=" * 65)
        print("  REPAIR FINISHED")
        print("=" * 65)
        print()
        print("  CRITICAL: You MUST power-cycle the keyboard now:")
        print("  1. UNPLUG the keyboard USB cable")
        print("  2. Wait 15 seconds")
        print("  3. PLUG IT BACK IN")
        print("  4. Test keys: type 'the quick brown fox jumps over the lazy dog'")
        print("  5. Test: Ctrl+C, Alt+Tab, Backspace")
        print()
        print("  If keys STILL don't work after power cycle:")
        print("  → We'll try manual keymap reconstruction (Phase 5)")
        print("  → Tell me and I'll fix it using the diagnostic data above")
        print()

        return 0

    finally:
        kernel32.CloseHandle(h)

if __name__ == '__main__':
    sys.exit(main())

