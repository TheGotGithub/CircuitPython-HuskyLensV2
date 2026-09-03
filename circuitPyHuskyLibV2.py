# HUSKYLENS V2 CircuitPython Library (core subset)
# Target: Raspberry Pi Pico 2 W (RP2350) and other CircuitPython boards
#
# Protocol reference:
# https://github.com/ (DFRobot_HuskylensV2) HuskyLens2_Protocol.md
# and the official Python reference implementation:
# DFRobot_HuskylensV2/python/smbus2/dfrobot_huskylensv2.py
#
# NOTE: HuskyLens V2 uses a DIFFERENT wire protocol than the original
# HuskyLens (V1). This library is NOT compatible with V1 hardware, and
# circuitPyHuskyLib.py (the V1 library) is NOT compatible with V2 hardware.
#
# This is a "core subset" port: handshake, algorithm switching, reading
# block/arrow results, learn/forget, and drawing (rect/text) on the
# HuskyLens screen. Advanced V2 features (play music, save/load knowledge,
# photo/video recording, algorithm parameters, multi-algorithm) are
# intentionally left out of this pass.
#
# Example:
'''
import board
from circuitPyHuskyLibV2 import HuskyLensLibraryV2, ALGORITHM_OBJECT_TRACKING

# I2C (default wiring for this project)
huskylens = HuskyLensLibraryV2("I2C", SCL=board.GP27, SDA=board.GP26)

# UART
# huskylens = HuskyLensLibraryV2("UART", TX=board.GP8, RX=board.GP9)

print(huskylens.knock())
huskylens.algorithm(ALGORITHM_OBJECT_TRACKING)

while True:
    if huskylens.getResult() is not None:
        for block in huskylens.blocks():
            print(block.ID, block.x, block.y, block.width, block.height)
'''

import time
import busio
import adafruit_bus_device.i2c_device as i2c_device

__version__ = "0.1.0"

# --- Packet layout (55 AA CMD ALGO LEN [data...] CHECKSUM) ---
HEADER0_INDEX = 0
HEADER1_INDEX = 1
COMMAND_INDEX = 2
ALGO_INDEX = 3
LENGTH_INDEX = 4
CONTENT_INDEX = 5

# --- Commands (core subset only) ---
COMMAND_KNOCK = 0x00
COMMAND_GET_RESULT = 0x01
COMMAND_SET_ALGORITHM = 0x0A
COMMAND_ACTION_LEARN = 0x22
COMMAND_ACTION_FORGET = 0x23
COMMAND_ACTION_DRAW_RECT = 0x26
COMMAND_ACTION_CLEAR_RECT = 0x27
COMMAND_ACTION_DRAW_TEXT = 0x28
COMMAND_ACTION_CLEAR_TEXT = 0x29
COMMAND_ACTION_LEARN_BLOCK = 0x2C
COMMAND_ACTION_DRAW_UNIQUE_RECT = 0x2D

COMMAND_RETURN_ARGS = 0x1A
COMMAND_RETURN_INFO = 0x1B
COMMAND_RETURN_BLOCK = 0x1C
COMMAND_RETURN_ARROW = 0x1D

# --- Algorithm IDs (per HuskyLens2_Protocol.md) ---
ALGORITHM_ANY = 0
ALGORITHM_FACE_RECOGNITION = 1
ALGORITHM_OBJECT_RECOGNITION = 2
ALGORITHM_OBJECT_TRACKING = 3
ALGORITHM_COLOR_RECOGNITION = 4
ALGORITHM_OBJECT_CLASSIFICATION = 5
ALGORITHM_SELF_LEARNING_CLASSIFICATION = 6
ALGORITHM_SEGMENT = 7
ALGORITHM_HAND_RECOGNITION = 8
ALGORITHM_POSE_RECOGNITION = 9
ALGORITHM_LICENSE_RECOGNITION = 10
ALGORITHM_OCR_RECOGNITION = 11
ALGORITHM_LINE_TRACKING = 12
ALGORITHM_EMOTION_RECOGNITION = 13
ALGORITHM_GAZE_RECOGNITION = 14
ALGORITHM_FACE_ORIENTATION = 15
ALGORITHM_TAG_RECOGNITION = 16
ALGORITHM_BARCODE_RECOGNITION = 17
ALGORITHM_QRCODE_RECOGNITION = 18
ALGORITHM_FALLDOWN_RECOGNITION = 19

# --- Color macros for drawRect()/drawText() (24-bit RGB, per DFRobot_HuskylensV2.h) ---
COLOR_WHITE = 0xFFFFFF
COLOR_RED = 0xFF0000
COLOR_ORANGE = 0xFFA500
COLOR_YELLOW = 0xFFFF00
COLOR_GREEN = 0x00FF00
COLOR_CYAN = 0x00FFFF
COLOR_BLUE = 0x0000FF
COLOR_PURPLE = 0x800080
COLOR_PINK = 0xFFC0CB
COLOR_GRAY = 0x808080
COLOR_BLACK = 0x000000
COLOR_BROWN = 0xA52A2A
COLOR_OLIVE = 0x808000
COLOR_TEAL = 0x008080
COLOR_INDIGO = 0x4B0082
COLOR_MAGENTA = 0xFF00FF


class Block:
    def __init__(self, ID, algo, x, y, width, height, name, content):
        self.ID = ID
        self.algo = algo
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.name = name
        self.content = content
        self.learned = ID > 0
        self.type = "BLOCK"


class Arrow:
    # NOTE: HuskyLens2_Protocol.md lists offsets 6 and 7 for angle/length,
    # which overlap (each field is 2 bytes). This implementation uses the
    # consistent 2-byte spacing (angle@6, length@8) seen elsewhere in the
    # protocol doc. Verify against real hardware if precise arrow length
    # matters for your application.
    def __init__(self, ID, xTarget, yTarget, angle, length):
        self.ID = ID
        self.xTarget = xTarget
        self.yTarget = yTarget
        self.angle = angle
        self.length = length
        self.learned = ID > 0
        self.type = "ARROW"


def _u16(buf, idx):
    return buf[idx] | (buf[idx + 1] << 8)


def _s16(buf, idx):
    v = _u16(buf, idx)
    return v - 0x10000 if v > 0x7FFF else v


def _pack_i16(v):
    return bytes([v & 0xFF, (v >> 8) & 0xFF])


def _pack_i32(v):
    return bytes([v & 0xFF, (v >> 8) & 0xFF, (v >> 16) & 0xFF, (v >> 24) & 0xFF])


def _pack_str(s):
    data = s.encode("utf-8")
    return bytes([len(data)]) + data


class HuskyLensLibraryV2:
    # HuskyLens V2 default working resolution
    SHAPE = (640, 480)

    def __init__(self, proto, TX=None, RX=None, SCL=None, SDA=None,
                 baudrate=115200, address=0x50, verbose=True):
        self.proto = proto
        self.verbose = verbose
        self.algo = ALGORITHM_ANY
        self.timeout = 3.0
        self._rx_buf = bytearray()
        self._rx_pos = 0
        self._blocks = []
        self._arrows = []
        self._maxID = 0

        if proto == "UART":
            self._uart = busio.UART(TX, RX, baudrate=baudrate, timeout=0.05)
            self._i2c_device = None
        elif proto == "I2C":
            i2c = busio.I2C(SCL, SDA)
            self._i2c_device = i2c_device.I2CDevice(i2c, address)
            self._uart = None
        else:
            raise ValueError("Only support UART or I2C protocol")

    # ---------------- low level: transport ----------------

    def _write(self, buf):
        if self.proto == "UART":
            self._uart.write(buf)
        else:
            # HuskyLens V2 I2C follows the official smbus2 reference, which
            # writes/reads through a leading 0x00 "register" byte.
            with self._i2c_device as i2c:
                i2c.write(bytes([0]) + bytes(buf))
        time.sleep(0.01)

    def _fill_rx_buffer(self):
        if self.proto == "UART":
            data = self._uart.read(32)
            self._rx_buf = bytearray(data) if data else bytearray()
        else:
            buf = bytearray(32)
            try:
                with self._i2c_device as i2c:
                    i2c.write_then_readinto(bytes([0]), buf)
                self._rx_buf = buf
            except OSError:
                self._rx_buf = bytearray()
        self._rx_pos = 0

    def _read_byte(self):
        if self._rx_pos >= len(self._rx_buf):
            self._fill_rx_buffer()
        if self._rx_pos >= len(self._rx_buf):
            return None
        b = self._rx_buf[self._rx_pos]
        self._rx_pos += 1
        return b

    # ---------------- low level: packet framing ----------------

    def _checksum(self, buf, length):
        s = 0
        for i in range(length):
            s += buf[i]
        return s & 0xFF

    def _write_packet(self, algo, command, data=b""):
        buf = bytearray(CONTENT_INDEX + len(data) + 1)
        buf[HEADER0_INDEX] = 0x55
        buf[HEADER1_INDEX] = 0xAA
        buf[COMMAND_INDEX] = command
        buf[ALGO_INDEX] = algo
        buf[LENGTH_INDEX] = len(data)
        buf[CONTENT_INDEX:CONTENT_INDEX + len(data)] = data
        buf[CONTENT_INDEX + len(data)] = self._checksum(buf, CONTENT_INDEX + len(data))
        self._write(buf)

    def _read_packet(self):
        start = time.monotonic()
        state = 0
        buf = bytearray()
        remaining = 0
        while time.monotonic() - start < self.timeout:
            b = self._read_byte()
            if b is None:
                continue
            if state == 0:
                if b == 0x55:
                    buf = bytearray([b])
                    state = 1
            elif state == 1:
                if b == 0xAA:
                    buf.append(b)
                    state = 2
                else:
                    state = 0
            elif state == 2 or state == 3:
                buf.append(b)
                state += 1
            elif state == 4:
                buf.append(b)
                remaining = b + 1  # content bytes + checksum byte (always >= 1)
                state = 5
            elif state == 5:
                buf.append(b)
                remaining -= 1
                if remaining == 0:
                    if self._checksum(buf, len(buf) - 1) == buf[-1]:
                        return buf
                    state = 0
        return None

    def _execute(self, algo, command, data=b"", wait_cmd=COMMAND_RETURN_ARGS, retries=3):
        for _ in range(retries):
            self._write_packet(algo, command, data)
            pkt = self._read_packet()
            if pkt is not None and pkt[COMMAND_INDEX] == wait_cmd:
                return pkt
        return None

    def _parse_args(self, pkt):
        content_size = pkt[LENGTH_INDEX]
        content_end = CONTENT_INDEX + content_size
        total_int_args = pkt[CONTENT_INDEX]
        ret_value = pkt[CONTENT_INDEX + 1]

        ints = []
        offset = CONTENT_INDEX + 2
        for _ in range(total_int_args):
            ints.append(_u16(pkt, offset))
            offset += 2

        strs = []
        offset = CONTENT_INDEX + 10
        while offset < content_end:
            length = pkt[offset]
            if length == 0:
                break
            offset += 1
            strs.append(bytes(pkt[offset:offset + length]).decode("utf-8", "ignore"))
            offset += length

        return ret_value == 0, ints, strs

    def _parse_block(self, pkt):
        base = CONTENT_INDEX
        ID = pkt[base]
        algo = pkt[base + 1]
        x = _u16(pkt, base + 2)
        y = _u16(pkt, base + 4)
        width = _u16(pkt, base + 6)
        height = _u16(pkt, base + 8)
        name_len = pkt[base + 10]
        idx = base + 11
        name = bytes(pkt[idx:idx + name_len]).decode("utf-8", "ignore") if name_len else ""
        idx += name_len
        content_len = pkt[idx]
        idx += 1
        content = bytes(pkt[idx:idx + content_len]).decode("utf-8", "ignore") if content_len else ""
        return Block(ID, algo, x, y, width, height, name, content)

    def _parse_arrow(self, pkt):
        base = CONTENT_INDEX
        ID = pkt[base]
        xTarget = _u16(pkt, base + 2)
        yTarget = _u16(pkt, base + 4)
        angle = _s16(pkt, base + 6)
        length = _u16(pkt, base + 8)
        return Arrow(ID, xTarget, yTarget, angle, length)

    # ---------------- public API ----------------

    def knock(self):
        # boardType=1 (large-RAM host) -- matches the official Python
        # reference; a Pico's SRAM is closer to that profile than an AVR.
        pkt = self._execute(ALGORITHM_ANY, COMMAND_KNOCK, bytes([1]) + bytes(9))
        if pkt is None:
            return False
        ok, _, _ = self._parse_args(pkt)
        return ok

    def algorithm(self, algo):
        data = bytes([algo & 0xFF]) + bytes(9)
        pkt = self._execute(ALGORITHM_ANY, COMMAND_SET_ALGORITHM, data)
        if pkt is None:
            return False
        ok, _, _ = self._parse_args(pkt)
        if ok:
            self.algo = algo
        return ok

    def learn(self, algo=None):
        algo = self.algo if algo is None else algo
        pkt = self._execute(algo, COMMAND_ACTION_LEARN, b"")
        if pkt is None:
            return 0
        ok, ints, _ = self._parse_args(pkt)
        return ints[0] if ok and ints else 0

    def forget(self, algo=None):
        algo = self.algo if algo is None else algo
        pkt = self._execute(algo, COMMAND_ACTION_FORGET, b"")
        if pkt is None:
            return False
        ok, _, _ = self._parse_args(pkt)
        return ok

    def learnBlock(self, x, y, width, height, algo=None):
        # Currently only supported by HuskyLens V2 for object tracking.
        algo = self.algo if algo is None else algo
        data = bytearray(10)
        data[2] = x & 0xFF
        data[3] = (x >> 8) & 0xFF
        data[4] = y & 0xFF
        data[5] = (y >> 8) & 0xFF
        data[6] = width & 0xFF
        data[7] = (width >> 8) & 0xFF
        data[8] = height & 0xFF
        data[9] = (height >> 8) & 0xFF
        pkt = self._execute(algo, COMMAND_ACTION_LEARN_BLOCK, bytes(data))
        if pkt is None:
            return 0
        ok, ints, _ = self._parse_args(pkt)
        return ints[0] if ok and ints else 0

    def _draw_rect_data(self, x, y, width, height, color, lineWidth):
        return (
            bytes([0, lineWidth & 0xFF])
            + _pack_i16(x) + _pack_i16(y) + _pack_i16(width) + _pack_i16(height)
            + _pack_i16(0)
            + _pack_i32(color)
        )

    def drawRect(self, x, y, width, height, color=COLOR_RED, lineWidth=2):
        """Draw a rectangle overlay on the HuskyLens screen. Persists until
        clearRect() or the next drawUniqueRect()/algorithm switch."""
        data = self._draw_rect_data(x, y, width, height, color, lineWidth)
        pkt = self._execute(ALGORITHM_ANY, COMMAND_ACTION_DRAW_RECT, data)
        if pkt is None:
            return False
        ok, _, _ = self._parse_args(pkt)
        return ok

    def drawUniqueRect(self, x, y, width, height, color=COLOR_RED, lineWidth=2):
        """Like drawRect(), but first clears any rectangle previously drawn
        this way -- handy for a single "tracking box" that moves each frame."""
        data = self._draw_rect_data(x, y, width, height, color, lineWidth)
        pkt = self._execute(ALGORITHM_ANY, COMMAND_ACTION_DRAW_UNIQUE_RECT, data)
        if pkt is None:
            return False
        ok, _, _ = self._parse_args(pkt)
        return ok

    def clearRect(self):
        """Clear all rectangles drawn via drawRect()/drawUniqueRect()."""
        pkt = self._execute(ALGORITHM_ANY, COMMAND_ACTION_CLEAR_RECT, b"")
        if pkt is None:
            return False
        ok, _, _ = self._parse_args(pkt)
        return ok

    def drawText(self, x, y, text, color=COLOR_WHITE, fontSize=16):
        """Draw a text overlay on the HuskyLens screen. Each (x, y) slot can
        be reused to update that text in place."""
        data = (
            bytes([0, fontSize & 0xFF])
            + _pack_i16(x) + _pack_i16(y)
            + _pack_i16(0) + _pack_i16(0)
            + _pack_str(text)
            + bytes([0])
            + _pack_i32(color)
        )
        pkt = self._execute(ALGORITHM_ANY, COMMAND_ACTION_DRAW_TEXT, data)
        if pkt is None:
            return False
        ok, _, _ = self._parse_args(pkt)
        return ok

    def clearText(self):
        """Clear all text drawn via drawText()."""
        pkt = self._execute(ALGORITHM_ANY, COMMAND_ACTION_CLEAR_TEXT, b"")
        if pkt is None:
            return False
        ok, _, _ = self._parse_args(pkt)
        return ok

    def getResult(self, algo=None):
        """Request fresh block/arrow data from HuskyLens. Populates the
        internal cache; use blocks()/arrows()/getBlocksByID()/etc. to read
        it. Returns total result count, or None on failure."""
        algo = self.algo if algo is None else algo
        self._write_packet(algo, COMMAND_GET_RESULT)

        info_pkt = self._read_packet()
        if info_pkt is None or info_pkt[COMMAND_INDEX] != COMMAND_RETURN_INFO:
            if self.verbose:
                print("HuskyLensV2: no result / object not found")
            return None

        base = CONTENT_INDEX
        self._maxID = info_pkt[base]
        total_results = _u16(info_pkt, base + 2)
        total_blocks = _u16(info_pkt, base + 6)
        total_arrows = total_results - total_blocks

        blocks = []
        for _ in range(total_blocks):
            pkt = self._read_packet()
            if pkt is None or pkt[COMMAND_INDEX] != COMMAND_RETURN_BLOCK:
                return None
            blocks.append(self._parse_block(pkt))

        arrows = []
        for _ in range(total_arrows):
            pkt = self._read_packet()
            if pkt is None or pkt[COMMAND_INDEX] != COMMAND_RETURN_ARROW:
                return None
            arrows.append(self._parse_arrow(pkt))

        self._blocks = blocks
        self._arrows = arrows
        return total_results

    def blocks(self):
        return list(self._blocks)

    def arrows(self):
        return list(self._arrows)

    def count(self):
        return len(self._blocks) + len(self._arrows)

    def maxID(self):
        return self._maxID

    def getBlocksByID(self, ID):
        return [b for b in self._blocks if b.ID == ID]

    def getArrowsByID(self, ID):
        return [a for a in self._arrows if a.ID == ID]

    def getByID(self, ID):
        return self.getBlocksByID(ID) + self.getArrowsByID(ID)
