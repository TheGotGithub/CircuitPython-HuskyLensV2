import board
from circuitPyHuskyLibV2 import HuskyLensLibraryV2

huskylens = HuskyLensLibraryV2("UART", TX=board.GP8, RX=board.GP9)

if huskylens.knock():
    print("PASS: connected to HuskyLens over UART")
else:
    print("FAIL: no response (check wiring and Protocol Type on HuskyLens)")
