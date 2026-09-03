# CircuitPython-HuskyLensV2

*[ภาษาไทย](README.th.md)*

CircuitPython driver for **HuskyLens V2** (DFRobot SEN0638), targeting the
Raspberry Pi Pico / Pico 2 W and other CircuitPython boards.

> **HuskyLens V2 uses a different wire protocol than the original HuskyLens
> (V1).** This library only works with V2 hardware. If you have the original
> HuskyLens (SEN0305), use [`CircuitPython-HuskyLens`](../CircuitPython-HuskyLens)
> instead -- the two libraries and the two devices are not interchangeable.

## Status

This is a **core-subset** port: connection handshake, algorithm switching,
reading detection results, learn/forget, and drawing overlays on the
HuskyLens screen. Tested working against real HuskyLens V2 hardware. See
[Not yet implemented](#not-yet-implemented) for what's still missing.

## Quick Start -- Required Libraries

> Place [`circuitPyHuskyLibV2.py`](circuitPyHuskyLibV2.py) in your
> **CIRCUITPY/lib** folder.
>
> You also need **adafruit_bus_device** in **CIRCUITPY/lib**. Download it
> from the [CircuitPython Library Bundle](https://circuitpython.org/libraries)
> (match the bundle version to your CircuitPython version).

## Wiring (default: I2C)

| HuskyLens V2 | Pico / Pico 2 W |
|---|---|
| SCL | GP27 |
| SDA | GP26 |
| GND | GND |
| VCC | see HuskyLens V2 hardware docs for supply voltage |

Set **Protocol Type = I2C** in the HuskyLens on-screen menu to match.

UART wiring is also supported -- see
[`examples/test_connection_uart.py`](examples/test_connection_uart.py)
(TX->GP8, RX->GP9). Whichever protocol you wire, set the matching **Protocol
Type** on the HuskyLens screen or the two sides won't be able to talk to
each other.

## Quick Start -- Simple Example

```python
import board
from circuitPyHuskyLibV2 import HuskyLensLibraryV2, ALGORITHM_OBJECT_TRACKING

huskylens = HuskyLensLibraryV2("I2C", SCL=board.GP27, SDA=board.GP26)

print(huskylens.knock())
huskylens.algorithm(ALGORITHM_OBJECT_TRACKING)

while True:
    if huskylens.getResult() is not None:
        for block in huskylens.blocks():
            print(block.ID, block.x, block.y, block.width, block.height)
```

## Testing on hardware

[`examples/`](examples/) is a small manual test suite -- one self-contained
script per feature, printing plain `print()` output to the serial console
(`PASS`/`FAIL` where there's a clear success/failure, otherwise just the
values so you can read them off). There's no on-device test runner in
CircuitPython, so run these by copying the one you want to `CIRCUITPY/` as
`code.py` and watching the serial output; they're meant to be run against a
real HuskyLens V2, one at a time, not automated in CI.

| File | Verifies |
|---|---|
| `test_connection_i2c.py` | `knock()` succeeds over I2C -- run this first |
| `test_connection_uart.py` | `knock()` succeeds over UART |
| `test_algorithm_switch.py` | `algorithm()` succeeds for several algorithm IDs |
| `test_get_result.py` | `getResult()`/`blocks()` return data for a real object in frame |
| `test_learn_forget.py` | `learn()` assigns an ID, it appears in the next `getResult()`, and `forget()` clears it |
| `test_draw_ui.py` | `drawRect()`/`drawUniqueRect()`/`drawText()`/`clearRect()`/`clearText()` return success (verify visually on the HuskyLens screen) |

# API Reference

## `HuskyLensLibraryV2(proto, TX=None, RX=None, SCL=None, SDA=None, baudrate=115200, address=0x50, verbose=True)`

Create the HuskyLens V2 connection.

- `proto`: `"UART"` or `"I2C"`
- `TX`, `RX`: UART pins (when `proto="UART"`)
- `SCL`, `SDA`: I2C pins (when `proto="I2C"`)
- `baudrate`: UART baudrate (default `115200`, matching HuskyLens V2's default)
- `address`: I2C address (default `0x50` -- V2's address; V1 used `0x32`)
- `verbose`: print a message when `getResult()` finds nothing

**Attributes**
- `SHAPE`: `(640, 480)` -- HuskyLens V2's working resolution
- `algo`: the algorithm ID last set via `algorithm()`; used as the default
  for other calls when their `algo` argument is omitted
- `timeout`: seconds to wait for a response before giving up (default `3.0`)

## Connection

### `knock()`
Handshake with HuskyLens V2. Returns `True` on success, `False` otherwise.
Call this once after creating the object to confirm wiring/protocol are correct.

### `algorithm(algo)`
Switch to one of the `ALGORITHM_*` constants (see below). Returns `True` on
success. On success, also updates `self.algo`, which other methods use as
their default target algorithm.

## Reading results

### `getResult(algo=None)`
Request fresh detection data and cache it internally. Returns the total
result count (`int`), or `None` on failure/no data. Call this once per loop
iteration before reading `blocks()`/`arrows()`.

### `blocks()` / `arrows()`
Return the cached list of `Block` / `Arrow` objects from the last `getResult()`.

### `getBlocksByID(ID)` / `getArrowsByID(ID)` / `getByID(ID)`
Filter the cached results down to a specific learned ID.

### `count()`
Total number of cached blocks + arrows.

### `maxID()`
Highest learned ID reported by HuskyLens for the current algorithm.

### `Block`
`ID`, `algo`, `x`, `y`, `width`, `height`, `name`, `content`, `learned` (bool,
`ID > 0`), `type` (`"BLOCK"`).

### `Arrow`
`ID`, `xTarget`, `yTarget`, `angle`, `length`, `learned` (bool, `ID > 0`),
`type` (`"ARROW"`). Only produced by Line Tracking.

## Learning

### `learn(algo=None)`
Learn whatever HuskyLens currently has centered in frame. Returns the new
learned ID (`int`), or `0` if learning failed. Unlike the V1 library, you
cannot choose the ID yourself -- HuskyLens assigns it. To get predictable IDs,
`forget()` first, then `learn()` each target in the order you want.

### `learnBlock(x, y, width, height, algo=None)`
Like `learn()`, but you specify the bounding box to learn instead of letting
HuskyLens pick it. Per DFRobot's protocol docs, **only Object Tracking
supports this**. Returns the learned ID, or `0` on failure.

### `forget(algo=None)`
Erase all learned IDs for the given algorithm. Returns `True` on success.

## Drawing on the HuskyLens screen

### `drawRect(x, y, width, height, color=COLOR_RED, lineWidth=2)`
Draw a rectangle overlay. Stays on screen until `clearRect()`.

### `drawUniqueRect(x, y, width, height, color=COLOR_RED, lineWidth=2)`
Same as `drawRect()`, but clears the previous rectangle drawn this way first
-- use this for a box that follows a moving object each frame, without
calling `clearRect()` yourself.

### `clearRect()`
Clear all rectangles.

### `drawText(x, y, text, color=COLOR_WHITE, fontSize=16)`
Draw a text label. Drawing again at the same `(x, y)` replaces that text.

### `clearText()`
Clear all text labels.

Color constants: `COLOR_WHITE`, `COLOR_RED`, `COLOR_ORANGE`, `COLOR_YELLOW`,
`COLOR_GREEN`, `COLOR_CYAN`, `COLOR_BLUE`, `COLOR_PURPLE`, `COLOR_PINK`,
`COLOR_GRAY`, `COLOR_BLACK`, `COLOR_BROWN`, `COLOR_OLIVE`, `COLOR_TEAL`,
`COLOR_INDIGO`, `COLOR_MAGENTA`.

## Algorithm IDs

```
ALGORITHM_ANY                          = 0   (handshake / general commands)
ALGORITHM_FACE_RECOGNITION             = 1
ALGORITHM_OBJECT_RECOGNITION           = 2
ALGORITHM_OBJECT_TRACKING              = 3
ALGORITHM_COLOR_RECOGNITION            = 4
ALGORITHM_OBJECT_CLASSIFICATION        = 5
ALGORITHM_SELF_LEARNING_CLASSIFICATION = 6
ALGORITHM_SEGMENT                      = 7
ALGORITHM_HAND_RECOGNITION             = 8
ALGORITHM_POSE_RECOGNITION             = 9
ALGORITHM_LICENSE_RECOGNITION          = 10
ALGORITHM_OCR_RECOGNITION              = 11
ALGORITHM_LINE_TRACKING                = 12
ALGORITHM_EMOTION_RECOGNITION          = 13
ALGORITHM_GAZE_RECOGNITION             = 14
ALGORITHM_FACE_ORIENTATION             = 15
ALGORITHM_TAG_RECOGNITION              = 16
ALGORITHM_BARCODE_RECOGNITION          = 17
ALGORITHM_QRCODE_RECOGNITION           = 18
ALGORITHM_FALLDOWN_RECOGNITION         = 19
```

`blocks()`/`arrows()` only decode the fields common to every algorithm
(position, size, ID, name, content). Algorithm-specific private data (e.g.
face landmark points, hand/pose keypoints) is not parsed by this core subset.

## Not yet implemented

These V2 features exist in the protocol but have no wrapper here yet:

- Play music (`playMusic`)
- Save/load knowledge to SD card (`saveKnowledges` / `loadKnowledges`)
- Take photo / screenshot, record audio/video
- Get/set algorithm parameters (`getAlgorithmParams` / `setAlgorithmParams`)
- Multi-algorithm combos (`setMultiAlgorithm` / `setMultiAlgorithmRatio`)
- `setNameByID`

## Acknowledgements

This library is an independent CircuitPython port based on the wire protocol
documented by DFRobot in their official Arduino/Python library:

- https://github.com/DFRobot/DFRobot_HuskylensV2

Packet format, command IDs, algorithm IDs, and drawing-command byte layout
are derived from that project's `HuskyLens2_Protocol.md` and its Python
reference implementation (`python/smbus2/dfrobot_huskylensv2.py`).
DFRobot_HuskylensV2 is licensed under the MIT License, Copyright (c) 2020
DFRobot -- see [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) for the
full notice and a breakdown of what was adapted from it.

API shape also takes inspiration from this repo's V1 library,
[`CircuitPython-HuskyLens`](../CircuitPython-HuskyLens).
