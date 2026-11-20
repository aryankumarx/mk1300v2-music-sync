import ctypes
from ctypes import wintypes
import sys

# Windows API constants
GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
OPEN_EXISTING = 3
FILE_ATTRIBUTE_NORMAL = 0x80
INVALID_HANDLE_VALUE = -1

# Load HID and SetupAPI
hid = ctypes.windll.hid
setupapi = ctypes.windll.setupapi
kernel32 = ctypes.windll.kernel32

class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", wintypes.BYTE * 8)
    ]

class SP_DEVICE_INTERFACE_DATA(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("InterfaceClassGuid", GUID),
        ("Flags", wintypes.DWORD),
        ("Reserved", ctypes.POINTER(ctypes.c_ulong))
    ]

class HIDD_ATTRIBUTES(ctypes.Structure):
    _fields_ = [
        ("Size", wintypes.DWORD),
        ("VendorID", wintypes.USHORT),
        ("ProductID", wintypes.USHORT),
        ("VersionNumber", wintypes.USHORT)
    ]

# Get HID Guid
hid_guid = GUID()
hid.HidD_GetHidGuid(ctypes.byref(hid_guid))

# Enumerate HID devices
dev_info = setupapi.SetupDiGetClassDevsW(
    ctypes.byref(hid_guid),
    None,
    None,
    0x10 | 0x02 # DIGCF_DEVICEINTERFACE | DIGCF_PRESENT
)

if dev_info == INVALID_HANDLE_VALUE:
    print("Failed to get device info set")
    sys.exit(1)

interface_data = SP_DEVICE_INTERFACE_DATA()
interface_data.cbSize = ctypes.sizeof(SP_DEVICE_INTERFACE_DATA)

index = 0
found_devices = []

while setupapi.SetupDiEnumDeviceInterfaces(dev_info, None, ctypes.byref(hid_guid), index, ctypes.byref(interface_data)):
    required_size = wintypes.DWORD()
    setupapi.SetupDiGetDeviceInterfaceDetailW(
        dev_info,
        ctypes.byref(interface_data),
        None,
        0,
        ctypes.byref(required_size),
        None
    )
    
    if required_size.value > 0:
        detail_data_buffer = (ctypes.c_byte * required_size.value)()
        # cbSize on Windows 64-bit is 8 (or 5 on 32-bit, 64-bit struct packing)
        ctypes.cast(ctypes.byref(detail_data_buffer), ctypes.POINTER(wintypes.DWORD))[0] = 8 if ctypes.sizeof(ctypes.c_void_p) == 8 else 5
        
        if setupapi.SetupDiGetDeviceInterfaceDetailW(
            dev_info,
            ctypes.byref(interface_data),
            ctypes.byref(detail_data_buffer),
            required_size.value,
            None,
            None
        ):
            # Device path starts after cbSize
            device_path = ctypes.wstring_at(ctypes.addressof(detail_data_buffer) + 4)
            if "36ae" in device_path.lower() or "fe12" in device_path.lower():
                found_devices.append(device_path)
    index += 1

setupapi.SetupDiDestroyDeviceInfoList(dev_info)

print(f"Found {len(found_devices)} matching Ant Esports / SDCINNOVATION HID interfaces:")
for p in found_devices:
    print(" - Path:", p)
    # Check if we can open handle
    h = kernel32.CreateFileW(
        p,
        GENERIC_READ | GENERIC_WRITE,
        FILE_SHARE_READ | FILE_SHARE_WRITE,
        None,
        OPEN_EXISTING,
        0,
        None
    )
    if h != INVALID_HANDLE_VALUE and h != 0:
        attrs = HIDD_ATTRIBUTES()
        attrs.Size = ctypes.sizeof(HIDD_ATTRIBUTES)
        hid.HidD_GetAttributes(h, ctypes.byref(attrs))
        print(f"   --> OPENED SUCCESS! VID=0x{attrs.VendorID:04X}, PID=0x{attrs.ProductID:04X}, Ver=0x{attrs.VersionNumber:04X}")
        kernel32.CloseHandle(h)
    else:
        err = kernel32.GetLastError()
        print(f"   --> Cannot open with Read/Write (Error code: {err})")

