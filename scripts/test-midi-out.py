#!/usr/bin/env python3
# Try send some predetermined midi messages
# HanishKVC, 2022
#

import rtmidi
import time


mo = rtmidi.MidiOut()
print(mo.get_ports())
pid = input("Select the port to use:")
pid = int(pid)
mo.open_port(pid)

for i in range(4096):
    mo.send_message([0x90, 0x55, 0xaa])
    #time.sleep(0.001)
    #mo.send_message([0x80, 0x55, 0x55])
    mo.send_message([0x80, 0x55, 0xaa])
    time.sleep(0.002)
