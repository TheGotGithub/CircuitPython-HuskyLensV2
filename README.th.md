# CircuitPython-HuskyLensV2

*[English version](README.md)*

ไลบรารี CircuitPython สำหรับ **HuskyLens V2** (DFRobot SEN0638) ใช้กับ
Raspberry Pi Pico / Pico 2 W และบอร์ด CircuitPython อื่นๆ

> **HuskyLens V2 ใช้โปรโตคอลสื่อสารคนละแบบกับ HuskyLens ตัวแรก (V1)**
> ไลบรารีนี้ใช้ได้กับฮาร์ดแวร์ V2 เท่านั้น ถ้าคุณมี HuskyLens ตัวแรก
> (SEN0305) ให้ใช้ [`CircuitPython-HuskyLens`](../CircuitPython-HuskyLens)
> แทน -- ทั้งสองไลบรารีและอุปกรณ์ทั้งสองรุ่นใช้แทนกันไม่ได้

## สถานะปัจจุบัน

นี่คือ **core subset** เท่านั้น: การเชื่อมต่อ/handshake, สลับอัลกอริทึม,
อ่านผลลัพธ์การตรวจจับ, learn/forget, และวาดกราฟิกบนจอ HuskyLens ทดสอบแล้ว
ว่าใช้งานได้จริงกับฮาร์ดแวร์ HuskyLens V2 ดู
[ฟีเจอร์ที่ยังไม่ได้ทำ](#ฟีเจอร์ที่ยังไม่ได้ทำ) สำหรับสิ่งที่ยังขาดอยู่

## เริ่มต้นใช้งาน -- ไลบรารีที่ต้องมี

> นำไฟล์ [`circuitPyHuskyLibV2.py`](circuitPyHuskyLibV2.py) ไปวางไว้ใน
> **CIRCUITPY/lib**
>
> ต้องมี **adafruit_bus_device** อยู่ใน **CIRCUITPY/lib** ด้วย ดาวน์โหลดได้จาก
> [CircuitPython Library Bundle](https://circuitpython.org/libraries)
> (เลือกเวอร์ชัน bundle ให้ตรงกับเวอร์ชัน CircuitPython ที่ใช้)

## การต่อสาย (ค่าเริ่มต้น: I2C)

| HuskyLens V2 | Pico / Pico 2 W |
|---|---|
| SCL | GP27 |
| SDA | GP26 |
| GND | GND |
| VCC | ดูสเปกแรงดันไฟจากคู่มือฮาร์ดแวร์ของ HuskyLens V2 |

ตั้งค่า **Protocol Type = I2C** ในเมนูหน้าจอของ HuskyLens ให้ตรงกัน

รองรับการต่อแบบ UART ด้วย ดูตัวอย่างที่
[`examples/test_connection_uart.py`](examples/test_connection_uart.py)
(TX->GP8, RX->GP9) ไม่ว่าจะต่อแบบไหน ต้องตั้ง **Protocol Type** บนหน้าจอ
HuskyLens ให้ตรงกับที่ต่อจริง ไม่งั้นสื่อสารกันไม่ได้

## ตัวอย่างเริ่มต้นแบบง่าย

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

## ทดสอบกับฮาร์ดแวร์จริง

[`examples/`](examples/) เป็นชุดทดสอบแบบ manual ขนาดเล็ก -- ไฟล์ละ 1
ฟีเจอร์ แต่ละไฟล์ standalone ในตัวเอง (ไม่ต้องพึ่งไฟล์อื่น) พิมพ์ผลลัพธ์
ผ่าน `print()` ตรงๆ (`PASS`/`FAIL` เมื่อมีเกณฑ์สำเร็จ/ล้มเหลวชัดเจน
หรือพิมพ์ค่าที่อ่านได้ให้ดูตรงๆ) เพราะ CircuitPython บนบอร์ดไม่มี test
runner ในตัว วิธีใช้คือ copy ไฟล์ที่ต้องการไปเป็น `code.py` บน
`CIRCUITPY/` แล้วดู serial output -- ใช้รันทีละไฟล์กับ HuskyLens V2 จริง
ไม่ใช่ automated test สำหรับ CI

| ไฟล์ | ทดสอบอะไร |
|---|---|
| `test_connection_i2c.py` | `knock()` สำเร็จผ่าน I2C -- รันไฟล์นี้ก่อนเสมอ |
| `test_connection_uart.py` | `knock()` สำเร็จผ่าน UART |
| `test_algorithm_switch.py` | `algorithm()` สลับได้หลายอัลกอริทึม |
| `test_get_result.py` | `getResult()`/`blocks()` ได้ข้อมูลจากวัตถุจริงในเฟรม |
| `test_learn_forget.py` | `learn()` ได้ ID ใหม่, ID นั้นปรากฏใน `getResult()` ถัดไป, และ `forget()` ล้างได้ |
| `test_draw_ui.py` | `drawRect()`/`drawUniqueRect()`/`drawText()`/`clearRect()`/`clearText()` คืนค่าสำเร็จ (เช็คผลจริงด้วยตาบนจอ HuskyLens) |

# API Reference

## `HuskyLensLibraryV2(proto, TX=None, RX=None, SCL=None, SDA=None, baudrate=115200, address=0x50, verbose=True)`

สร้าง object เชื่อมต่อกับ HuskyLens V2

- `proto`: `"UART"` หรือ `"I2C"`
- `TX`, `RX`: ขา UART (เมื่อ `proto="UART"`)
- `SCL`, `SDA`: ขา I2C (เมื่อ `proto="I2C"`)
- `baudrate`: baudrate ของ UART (ค่าเริ่มต้น `115200` ตรงกับค่า default ของ HuskyLens V2)
- `address`: I2C address (ค่าเริ่มต้น `0x50` -- ของ V2; V1 ใช้ `0x32`)
- `verbose`: พิมพ์ข้อความเมื่อ `getResult()` ไม่เจออะไรเลย

**Attributes**
- `SHAPE`: `(640, 480)` -- ความละเอียดที่ HuskyLens V2 ทำงานอยู่
- `algo`: ID อัลกอริทึมล่าสุดที่ตั้งผ่าน `algorithm()`; ใช้เป็นค่า default
  ให้ฟังก์ชันอื่นเมื่อไม่ระบุ `algo` เอง
- `timeout`: เวลา (วินาที) ที่รอคำตอบก่อนยอมแพ้ (ค่าเริ่มต้น `3.0`)

## การเชื่อมต่อ

### `knock()`
Handshake กับ HuskyLens V2 คืนค่า `True` เมื่อสำเร็จ, `False` เมื่อไม่สำเร็จ
เรียกครั้งเดียวหลังสร้าง object เพื่อยืนยันว่าต่อสาย/ตั้ง protocol ถูกต้อง

### `algorithm(algo)`
สลับไปใช้ค่าคงที่ `ALGORITHM_*` ตัวใดตัวหนึ่ง (ดูรายการด้านล่าง) คืนค่า
`True` เมื่อสำเร็จ และจะอัปเดต `self.algo` ด้วย ซึ่งฟังก์ชันอื่นจะใช้เป็น
target อัลกอริทึม default

## การอ่านผลลัพธ์

### `getResult(algo=None)`
ขอข้อมูลการตรวจจับล่าสุดแล้วแคชไว้ในตัว object คืนค่าจำนวนผลลัพธ์ทั้งหมด
(`int`) หรือ `None` เมื่อล้มเหลว/ไม่มีข้อมูล เรียกครั้งเดียวต่อรอบ loop
ก่อนอ่าน `blocks()`/`arrows()`

### `blocks()` / `arrows()`
คืนลิสต์ `Block` / `Arrow` ที่แคชไว้จาก `getResult()` ครั้งล่าสุด

### `getBlocksByID(ID)` / `getArrowsByID(ID)` / `getByID(ID)`
กรองผลลัพธ์ที่แคชไว้เฉพาะ ID ที่เคย learn ไว้

### `count()`
จำนวน block + arrow ที่แคชไว้ทั้งหมด

### `maxID()`
ID สูงสุดที่ HuskyLens รายงานสำหรับอัลกอริทึมปัจจุบัน

### `Block`
`ID`, `algo`, `x`, `y`, `width`, `height`, `name`, `content`, `learned`
(bool, มาจาก `ID > 0`), `type` (`"BLOCK"`)

### `Arrow`
`ID`, `xTarget`, `yTarget`, `angle`, `length`, `learned` (bool, มาจาก
`ID > 0`), `type` (`"ARROW"`) ได้จากโหมด Line Tracking เท่านั้น

## การสอนจำ (Learning)

### `learn(algo=None)`
สอนจำวัตถุที่อยู่กลางเฟรมตอนนี้ คืนค่า ID ใหม่ที่ได้ (`int`) หรือ `0`
ถ้าสอนไม่สำเร็จ ต่างจากไลบรารี V1 ตรงที่ **กำหนด ID เองไม่ได้** --
HuskyLens เป็นคน assign ให้ ถ้าต้องการ ID ที่คาดเดาได้ ให้ `forget()`
ก่อนแล้วค่อย `learn()` ทีละตัวตามลำดับที่ต้องการ

### `learnBlock(x, y, width, height, algo=None)`
เหมือน `learn()` แต่กำหนดกรอบ (bounding box) เองได้แทนที่จะให้ HuskyLens
เลือกเอง ตามเอกสารโปรโตคอลของ DFRobot **รองรับเฉพาะโหมด Object Tracking
เท่านั้น** คืนค่า ID ที่ได้ หรือ `0` เมื่อล้มเหลว

### `forget(algo=None)`
ลบ ID ที่เคย learn ไว้ทั้งหมดของอัลกอริทึมนั้น คืนค่า `True` เมื่อสำเร็จ

## การวาดกราฟิกบนจอ HuskyLens

### `drawRect(x, y, width, height, color=COLOR_RED, lineWidth=2)`
วาดกรอบสี่เหลี่ยม ค้างอยู่บนจอจนกว่าจะเรียก `clearRect()`

### `drawUniqueRect(x, y, width, height, color=COLOR_RED, lineWidth=2)`
เหมือน `drawRect()` แต่ล้างกรอบเก่าที่วาดด้วยฟังก์ชันนี้ให้ก่อนโดย
อัตโนมัติ -- เหมาะกับกรอบที่ขยับตามวัตถุทุกเฟรม ไม่ต้องเรียก
`clearRect()` เอง

### `clearRect()`
ล้างกรอบทั้งหมด

### `drawText(x, y, text, color=COLOR_WHITE, fontSize=16)`
วาดข้อความ วาดซ้ำที่ตำแหน่ง `(x, y)` เดิม = แทนที่ข้อความเก่า

### `clearText()`
ล้างข้อความทั้งหมด

ค่าคงที่สี: `COLOR_WHITE`, `COLOR_RED`, `COLOR_ORANGE`, `COLOR_YELLOW`,
`COLOR_GREEN`, `COLOR_CYAN`, `COLOR_BLUE`, `COLOR_PURPLE`, `COLOR_PINK`,
`COLOR_GRAY`, `COLOR_BLACK`, `COLOR_BROWN`, `COLOR_OLIVE`, `COLOR_TEAL`,
`COLOR_INDIGO`, `COLOR_MAGENTA`

## รายการ Algorithm ID

```
ALGORITHM_ANY                          = 0   (สำหรับ handshake / คำสั่งทั่วไป)
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

`blocks()`/`arrows()` ถอดรหัสเฉพาะฟิลด์ที่ทุกอัลกอริทึมมีร่วมกัน
(ตำแหน่ง, ขนาด, ID, ชื่อ, เนื้อหา) ข้อมูลเฉพาะของแต่ละอัลกอริทึม
(เช่น จุด landmark บนใบหน้า, จุดข้อต่อมือ/ร่างกาย) ยัง**ไม่ได้ถูก parse**
ใน core subset นี้

## ฟีเจอร์ที่ยังไม่ได้ทำ

ฟีเจอร์เหล่านี้มีอยู่ในโปรโตคอล V2 แต่ยังไม่มี wrapper ในไลบรารีนี้:

- เล่นเพลง (`playMusic`)
- บันทึก/โหลด knowledge จาก SD card (`saveKnowledges` / `loadKnowledges`)
- ถ่ายรูป/สกรีนช็อต, บันทึกเสียง/วิดีโอ
- อ่าน/ตั้งค่าพารามิเตอร์ของอัลกอริทึม (`getAlgorithmParams` / `setAlgorithmParams`)
- รวมหลายอัลกอริทึม (`setMultiAlgorithm` / `setMultiAlgorithmRatio`)
- `setNameByID`

## กิตติกรรมประกาศ

ไลบรารีนี้เป็นการพอร์ต CircuitPython ที่เขียนขึ้นใหม่โดยอิสระ โดยอ้างอิง
โปรโตคอลสื่อสารที่ DFRobot เผยแพร่ไว้ในไลบรารี Arduino/Python ทางการของ
พวกเขา:

- https://github.com/DFRobot/DFRobot_HuskylensV2

รูปแบบแพ็กเก็ต, command ID, algorithm ID, และรูปแบบ byte ของคำสั่งวาด
กราฟิก อ้างอิงมาจาก `HuskyLens2_Protocol.md` และไลบรารีอ้างอิง Python
(`python/smbus2/dfrobot_huskylensv2.py`) ของโปรเจกต์นั้น
DFRobot_HuskylensV2 อยู่ภายใต้ MIT License, Copyright (c) 2020 DFRobot --
ดู [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) สำหรับประกาศฉบับเต็ม
และรายละเอียดว่าส่วนไหนถูกดัดแปลงมาจากที่ไหนบ้าง

รูปแบบ API ยังได้แรงบันดาลใจจากไลบรารี V1 ในโปรเจกต์นี้,
[`CircuitPython-HuskyLens`](../CircuitPython-HuskyLens)
