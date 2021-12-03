from ble_motor_ctrl import application
import json
from epics import caget

with open("config/config.json", "r") as config_file:
    config = json.load(config_file)

pvs = []

for pv in config.get("pvs"):
    if caget(pv, timeout=1) is not None:
        pvs.append(pv)

application.register(pvs, config.get("name"))
