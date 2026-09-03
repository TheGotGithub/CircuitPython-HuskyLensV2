import time
import board
from circuitPyHuskyLibV2 import (
    HuskyLensLibraryV2,
    ALGORITHM_OBJECT_TRACKING,
    COLOR_GREEN,
    COLOR_YELLOW,
)

huskylens = HuskyLensLibraryV2("I2C", SCL=board.GP27, SDA=board.GP26)
print("knock:", huskylens.knock())
print("switch algorithm:", huskylens.algorithm(ALGORITHM_OBJECT_TRACKING))

while True:
    result = huskylens.getResult()
    blocks = huskylens.blocks() if result else []

    if blocks:
        b = blocks[0]
        # drawUniqueRect clears the previous frame's box automatically,
        # so the overlay tracks the object instead of piling up.
        huskylens.drawUniqueRect(
            b.x - b.width // 2, b.y - b.height // 2, b.width, b.height,
            color=COLOR_GREEN,
        )
        huskylens.drawText(
            b.x - b.width // 2, b.y - b.height // 2 - 20,
            "ID:{}".format(b.ID), color=COLOR_YELLOW,
        )
    else:
        huskylens.clearRect()
        huskylens.clearText()

    time.sleep(0.1)
