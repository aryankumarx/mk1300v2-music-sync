import ctypes
from ctypes import wintypes
import colorsys
import time
import sys

PATH = r'\\?\HID#VID_36AE&PID_FE12&MI_02#8&1cdcfa05&0&0000#{4d1e55b2-f16f-11cf-88cb-001111000030}'
kernel32 = ctypes.windll.kernel32

def open_device():
    h = kernel32.CreateFileW(PATH, 0xC0000000, 3, None, 3, 0, None)
    if h == -1 or h == 0:
        return None
    return h

def send_packet(h, payload):
    buf = (ctypes.c_ubyte * 65)()
    buf[0] = 0x00
    for i, b in enumerate(payload):
        if i + 1 < 65:
            buf[i + 1] = b
    written = wintypes.DWORD()
    return kernel32.WriteFile(h, buf, 65, ctypes.byref(written), None)

def read_packet(h):
    buf = (ctypes.c_ubyte * 65)()
    read_bytes = wintypes.DWORD()
    if kernel32.ReadFile(h, buf, 65, ctypes.byref(read_bytes), None) and read_bytes.value > 0:
        return [buf[i] for i in range(read_bytes.value)]
    return None

def set_hardware_color(h, r, g, b, mode=1, brightness=4, speed=1):
    """
    Sets keyboard color using the exact SDCX web-app protocol:
    e.h: Math.floor(h_degrees / 360 * 255)
    e.s: Math.floor(s_percent / 100 * 255)
    e.v: Math.floor(v_percent / 100 * 255)
    payload: [0x06, 0x0B, 11, 0, 0, 1, 0, mode, brightness, speed, direction=0, color=1, singleColorIdx=0, h_byte, s_byte, v_byte]
    """
    # Convert RGB (0..255) to HSV
    hf, sf, vf = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    h_deg = hf * 360.0
    s_pct = sf * 100.0
    v_pct = vf * 100.0

    h_byte = int(h_deg / 360.0 * 255.0) & 0xFF
    s_byte = int(s_pct / 100.0 * 255.0) & 0xFF
    v_byte = int(v_pct / 100.0 * 255.0) & 0xFF

    # 1. Switch mode via 0x16: 06 16 00 00 00 01 00 [mode]
    send_packet(h, [0x06, 0x16, 0x00, 0x00, 0x00, 0x01, 0x00, mode])
    read_packet(h)
    time.sleep(0.05)

    # 2. Configure light state via 0x0B
    # a = [type=1, 0, mode, brightness, speed, direction=0, color=1, singleColorIndex=0, h, s, v]
    # packet: 06 0B 11 00 00 [a]
    a = [1, 0, mode, brightness, speed, 0, 1, 0, h_byte, s_byte, v_byte]
    cmd = [0x06, 0x0B, len(a), 0, 0] + a
    send_packet(h, cmd)
    reply = read_packet(h)
    return reply

def main():
    h = open_device()
    if not h:
        print("Cannot open keyboard!")
        return 1

    try:
        # Test 1: Solid Red (mode 1 = Static)
        print(">>> Testing Solid RED for 3 seconds...")
        set_hardware_color(h, 255, 0, 0, mode=1, brightness=4)
        time.sleep(3)

        # Test 2: Solid Green
        print(">>> Testing Solid GREEN for 3 seconds...")
        set_hardware_color(h, 0, 255, 0, mode=1, brightness=4)
        time.sleep(3)

        # Test 3: Solid Blue
        print(">>> Testing Solid BLUE for 3 seconds...")
        set_hardware_color(h, 0, 0, 255, mode=1, brightness=4)
        time.sleep(3)

        # Restore Rainbow Wave (mode 4 = Stream)
        print(">>> Restoring dynamic Rainbow Stream...")
        set_hardware_color(h, 255, 255, 255, mode=4, brightness=4)
        print("Done!")

    finally:
        kernel32.CloseHandle(h)

if __name__ == '__main__':
    main()

