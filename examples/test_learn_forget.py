import time
import board
from circuitPyHuskyLibV2 import HuskyLensLibraryV2, ALGORITHM_OBJECT_RECOGNITION

huskylens = HuskyLensLibraryV2("I2C", SCL=board.GP27, SDA=board.GP26)
print("knock:", huskylens.knock())
print("switch algorithm:", huskylens.algorithm(ALGORITHM_OBJECT_RECOGNITION))

print("point HuskyLens at the target object, learning in 2s...")
time.sleep(2)

learned_id = huskylens.learn()
print("learned ID:", learned_id)  # 0 means learning failed

print("watching for the learned object for 10s...")
for _ in range(20):
    huskylens.getResult()
    matches = huskylens.getBlocksByID(learned_id)
    print("target visible:", len(matches) > 0)
    time.sleep(0.5)

print("forget:", huskylens.forget())
