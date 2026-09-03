import board
from circuitPyHuskyLibV2 import HuskyLensLibraryV2

huskylens = HuskyLensLibraryV2("I2C", SCL=board.GP27, SDA=board.GP26)

if huskylens.knock():
    print("PASS: connected to HuskyLens over I2C")
else:
    print("FAIL: no response (check wiring and Protocol Type on HuskyLens)")
