import ctypes
from ctypes import wintypes

PATH = r'\\?\HID#VID_36AE&PID_FE12&MI_02#8&1cdcfa05&0&0000#{4d1e55b2-f16f-11cf-88cb-001111000030}'
kernel32 = ctypes.windll.kernel32
h = kernel32.CreateFileW(PATH, 0xC0000000, 3, None, 3, 0, None)
if h != -1:
    entries = []
    written = wintypes.DWORD()
    read_bytes = wintypes.DWORD()
    for off in range(0, 336, 56):
        buf = (ctypes.c_ubyte * 65)()
        buf[1] = 0x06
        buf[2] = 0x08
        buf[3] = 0x3A
        buf[4] = off
        kernel32.WriteFile(h, buf, 65, ctypes.byref(written), None)
        in_buf = (ctypes.c_ubyte * 65)()
        if kernel32.ReadFile(h, in_buf, 65, ctypes.byref(read_bytes), None) and read_bytes.value > 8:
            data = [in_buf[i] for i in range(8, read_bytes.value)]
            for j in range(0, len(data) - 3, 4):
                entries.append(data[j:j+4])
    print(f"Total key positions read: {len(entries)}")
    for i, e in enumerate(entries[:80]):
        hex_str = ' '.join(f"{b:02X}" for b in e)
        print(f"pos {i:2d}: {hex_str}")
    kernel32.CloseHandle(h)
else:
    print("Failed to open handle")

