# Third-Party Notices

This project (`circuitPyHuskyLibV2.py` and the examples in `examples/`) is an
independent CircuitPython implementation. It was written by reading, and is
derived from, the wire protocol and reference logic published by DFRobot in:

- **DFRobot_HuskylensV2** -- https://github.com/DFRobot/DFRobot_HuskylensV2

Specifically, the following were ported/adapted from that project:

- Packet framing (`55 AA CMD ALGO LEN ... CHECKSUM`) and checksum algorithm,
  from `HuskyLens2_Protocol.md` and `ProtocolV2.cpp`.
- Command IDs, algorithm IDs, and color macros, from `HuskyLens2_Protocol.md`
  and `DFRobot_HuskylensV2.h`.
- The byte layout for drawing commands (`drawRect`, `drawUniqueRect`,
  `drawText`) and the I2C leading-byte read/write pattern, from
  `python/smbus2/dfrobot_huskylensv2.py`.

No source files from DFRobot_HuskylensV2 were copied verbatim; this is a
from-scratch CircuitPython port. It is included here in accordance with the
MIT License terms below, under which DFRobot_HuskylensV2 is distributed.

---

## DFRobot_HuskylensV2 License

```
MIT License

Copyright (c) 2020 DFRobot

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
