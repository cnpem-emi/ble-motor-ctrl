from ble_motor_ctrl import application
import json

with open("config/config.json", "r") as config_file:
    config = json.load(config_file)

application.register(config.get("pvs"), config.get("name"))
