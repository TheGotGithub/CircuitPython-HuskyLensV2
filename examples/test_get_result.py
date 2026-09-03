import time
import board
from circuitPyHuskyLibV2 import HuskyLensLibraryV2, ALGORITHM_OBJECT_TRACKING

huskylens = HuskyLensLibraryV2("I2C", SCL=board.GP27, SDA=board.GP26)
print("knock:", huskylens.knock())
print("switch algorithm:", huskylens.algorithm(ALGORITHM_OBJECT_TRACKING))

print("point HuskyLens at an object...")

while True:
    result = huskylens.getResult()
    if result:
        for block in huskylens.blocks():
            print("ID={} x={} y={} w={} h={}".format(
                block.ID, block.x, block.y, block.width, block.height))
    time.sleep(0.1)
