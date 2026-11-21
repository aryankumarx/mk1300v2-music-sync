import ctypes
from ctypes import wintypes
import time

PATH = r'\\?\HID#VID_36AE&PID_FE12&MI_02#8&1cdcfa05&0&0000#{4d1e55b2-f16f-11cf-88cb-001111000030}'
kernel32 = ctypes.windll.kernel32

h = kernel32.CreateFileW(PATH, 0xC0000000, 3, None, 3, 0, None)
written = wintypes.DWORD()
read_bytes = wintypes.DWORD()

# Let's fix pos 6, 7, 8, 9, 25
corrections = [
    (6,  [0x20, 0x00, 0x23, 0x00]), # 6 (0x23)
    (7,  [0x20, 0x00, 0x24, 0x00]), # 7 (0x24)
    (8,  [0x20, 0x00, 0x25, 0x00]), # 8 (0x25)
    (9,  [0x20, 0x00, 0x26, 0x00]), # 9 (0x26)
    (25, [0x20, 0x00, 0x13, 0x00]), # P (0x13)
]

print("Applying specific corrections...")
for pos, entry in corrections:
    cmd = [0x06, 0x10, 0x07, 4 * pos, 0, 0, 0, 0] + entry
    buf = (ctypes.c_ubyte * 65)()
    for i, b in enumerate(cmd): buf[i + 1] = b
    kernel32.WriteFile(h, buf, 65, ctypes.byref(written), None)
    in_buf = (ctypes.c_ubyte * 65)()
    kernel32.ReadFile(h, in_buf, 65, ctypes.byref(read_bytes), None)
    time.sleep(0.015)

# Also ensure Rainbow stream mode is active so lighting is completely restored:
# 06 16 00 00 00 01 00 04
buf = (ctypes.c_ubyte * 65)()
cmd_rainbow = [0x06, 0x16, 0x00, 0x00, 0x00, 0x01, 0x00, 0x04]
for i, b in enumerate(cmd_rainbow): buf[i + 1] = b
kernel32.WriteFile(h, buf, 65, ctypes.byref(written), None)

kernel32.CloseHandle(h)
print("Corrections applied successfully!")

