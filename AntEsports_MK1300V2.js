export function Name() { return "Ant Esports MK1300 V2"; }
export function VendorId() { return 0x36AE; }
export function ProductId() { return 0xFE12; }
export function Publisher() { return "Community"; }
export function Size() { return [15, 5]; }
export function DefaultPosition() { return [75, 50]; }
export function DefaultScale() { return 8.0; }
export function DeviceType() { return "keyboard"; }
export function Type() { return "hid"; }

// Target Interface 2 (Vendor Configuration Interface)
export function Validate(endpoint) {
    return endpoint.interface === 2;
}

/* global
lightingMode:readonly
forcedColor:readonly
*/
export function ControllableParameters() {
    return [
        {
            property: "lightingMode",
            group: "lighting",
            label: "Lighting Mode",
            type: "combobox",
            values: ["Canvas Live Sync", "Forced Solid Color", "Hardware Rainbow Stream"],
            default: "Canvas Live Sync"
        },
        {
            property: "forcedColor",
            group: "lighting",
            label: "Forced Color",
            type: "color",
            default: "#FF00FF"
        }
    ];
}

const vKeyNames = [
    // Row 0
    "Escape", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "=", "Backspace",
    // Row 1
    "Tab", "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", "[", "]", "\\",
    // Row 2
    "CapsLock", "A", "S", "D", "F", "G", "H", "J", "K", "L", ";", "'", "Enter",
    // Row 3
    "LeftShift", "Z", "X", "C", "V", "B", "N", "M", ",", ".", "/", "RightShift",
    // Row 4
    "LeftControl", "LeftWindows", "LeftAlt", "Space", "RightAlt", "Fn", "Menu", "RightControl"
];

const vKeyPositions = [
    // Row 0
    [0, 0], [1, 0], [2, 0], [3, 0], [4, 0], [5, 0], [6, 0], [7, 0], [8, 0], [9, 0], [10, 0], [11, 0], [12, 0], [13.5, 0],
    // Row 1
    [0.2, 1], [1.5, 1], [2.5, 1], [3.5, 1], [4.5, 1], [5.5, 1], [6.5, 1], [7.5, 1], [8.5, 1], [9.5, 1], [10.5, 1], [11.5, 1], [12.5, 1], [13.8, 1],
    // Row 2
    [0.3, 2], [1.8, 2], [2.8, 2], [3.8, 2], [4.8, 2], [5.8, 2], [6.8, 2], [7.8, 2], [8.8, 2], [9.8, 2], [10.8, 2], [11.8, 2], [13.3, 2],
    // Row 3
    [0.5, 3], [2.1, 3], [3.1, 3], [4.1, 3], [5.1, 3], [6.1, 3], [7.1, 3], [8.1, 3], [9.1, 3], [10.1, 3], [11.1, 3], [13.0, 3],
    // Row 4
    [0.2, 4], [1.4, 4], [2.6, 4], [6.2, 4], [9.8, 4], [11.0, 4], [12.2, 4], [13.4, 4]
];

export function LedNames() {
    return vKeyNames;
}

export function LedPositions() {
    return vKeyPositions;
}

let lastUpdate = 0;
let lastR = -1;
let lastG = -1;
let lastB = -1;
let modeActive = "";

function hexToRgb(hex) {
    let cleanHex = hex.replace("#", "");
    if (cleanHex.length === 3) {
        cleanHex = cleanHex[0] + cleanHex[0] + cleanHex[1] + cleanHex[1] + cleanHex[2] + cleanHex[2];
    }
    let num = parseInt(cleanHex, 16);
    return [(num >> 16) & 255, (num >> 8) & 255, num & 255];
}

export function Initialize() {
    device.setName("Ant Esports MK1300 V2");
    device.setSize([15, 5]);
    device.setControllableLeds(vKeyNames, vKeyPositions);
    device.addFeature("keyboard");

    // Switch to UserLight Mode (Effect 0x07)
    let switchCmd = [0x00, 0x06, 0x16, 0x00, 0x00, 0x00, 0x01, 0x00, 0x07];
    device.write(switchCmd, 65);
    modeActive = "UserLight";
    device.log("Initialized Ant Esports MK1300 V2 UserLight Mode.");
}

function sendColorBuffer(r, g, b) {
    const totalBytes = 119 * 3;
    const chunkSize = 56;
    const chunks = 7;

    for (let i = 0; i < chunks; i++) {
        let offset = chunkSize * i;
        let remaining = totalBytes - offset;
        let thisChunk = remaining < chunkSize ? remaining : chunkSize;
        let isLast = (i === chunks - 1);

        let pkt = new Array(65).fill(0);
        pkt[0] = 0;  // Report ID
        pkt[1] = 6;  // Command group
        pkt[2] = 18; // Opcode 18: chunked write
        pkt[3] = (isLast && (remaining % chunkSize > 0)) ? ((remaining % chunkSize) + 3) : (chunkSize + 3);
        pkt[4] = offset & 0xFF;
        pkt[5] = (offset >> 8) & 0xFF;
        pkt[6] = 0;
        pkt[7] = 0;
        pkt[8] = 0;

        for (let j = 0; j < thisChunk; j++) {
            let ch = (offset + j) % 3;
            pkt[9 + j] = ch === 0 ? r : (ch === 1 ? g : b);
        }

        device.write(pkt, 65);
        device.pause(2); // Prevent USB packet drop
    }
}

export function Render() {
    let currentMode = device.getProperty("lightingMode");

    if (currentMode === "Hardware Rainbow Stream") {
        if (modeActive !== "Stream") {
            let streamPkt = [0x00, 0x06, 0x16, 0x00, 0x00, 0x00, 0x01, 0x00, 0x04];
            device.write(streamPkt, 65);
            modeActive = "Stream";
        }
        return;
    }

    if (modeActive !== "UserLight") {
        let switchCmd = [0x00, 0x06, 0x16, 0x00, 0x00, 0x00, 0x01, 0x00, 0x07];
        device.write(switchCmd, 65);
        modeActive = "UserLight";
    }

    let r = 255, g = 0, b = 255;

    if (currentMode === "Forced Solid Color") {
        let hex = device.getProperty("forcedColor") || "#FF00FF";
        let rgb = hexToRgb(hex);
        r = rgb[0]; g = rgb[1]; b = rgb[2];
    } else {
        // Canvas Live Sync: sample colors across canvas
        let c1 = device.color(7, 2) || [0, 0, 0];
        let c2 = device.color(3, 1) || [0, 0, 0];
        let c3 = device.color(11, 3) || [0, 0, 0];

        r = Math.round((c1[0] + c2[0] + c3[0]) / 3);
        g = Math.round((c1[1] + c2[1] + c3[1]) / 3);
        b = Math.round((c1[2] + c2[2] + c3[2]) / 3);
    }

    let now = Date.now();
    // Throttle to 80ms (~12 FPS)
    if (now - lastUpdate < 80) {
        return;
    }

    // Skip redundant updates
    if (Math.abs(r - lastR) < 3 && Math.abs(g - lastG) < 3 && Math.abs(b - lastB) < 3) {
        return;
    }

    lastUpdate = now;
    lastR = r;
    lastG = g;
    lastB = b;

    sendColorBuffer(r, g, b);
}

export function Shutdown() {
    let streamCmd = [0x00, 0x06, 0x16, 0x00, 0x00, 0x00, 0x01, 0x00, 0x04];
    device.write(streamCmd, 65);
    modeActive = "Stream";
}
