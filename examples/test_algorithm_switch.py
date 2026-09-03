import time
import board
from circuitPyHuskyLibV2 import (
    HuskyLensLibraryV2,
    ALGORITHM_OBJECT_TRACKING,
    ALGORITHM_FACE_RECOGNITION,
    ALGORITHM_COLOR_RECOGNITION,
    ALGORITHM_LINE_TRACKING,
)

huskylens = HuskyLensLibraryV2("I2C", SCL=board.GP27, SDA=board.GP26)
print("knock:", huskylens.knock())

print("switch to OBJECT_TRACKING:", huskylens.algorithm(ALGORITHM_OBJECT_TRACKING))
time.sleep(0.5)

print("switch to FACE_RECOGNITION:", huskylens.algorithm(ALGORITHM_FACE_RECOGNITION))
time.sleep(0.5)

print("switch to COLOR_RECOGNITION:", huskylens.algorithm(ALGORITHM_COLOR_RECOGNITION))
time.sleep(0.5)

print("switch to LINE_TRACKING:", huskylens.algorithm(ALGORITHM_LINE_TRACKING))
time.sleep(0.5)
