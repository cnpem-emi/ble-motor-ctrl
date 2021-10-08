import dbus
from epics import caget, caput

from advertisement import Advertisement
from service import Application, Service, Characteristic, Descriptor

GATT_CHRC_IFACE = "org.bluez.GattCharacteristic1"
NOTIFY_TIMEOUT = 10000


class MotorAdvertisement(Advertisement):
    def __init__(self, index):
        Advertisement.__init__(self, index, "peripheral")
        self.add_local_name("Motor - Monochromator 1")
        self.add_manufacturer_data(0x000D, [0, 0])  # Texas Instruments
        self.include_tx_power = True


class MotorService(Service):
    MOTOR_SVC_UUID = "84e7f883-7c80-4b64-88a5-6077ce2e8925"

    def __init__(self, index):
        Service.__init__(self, index, self.MOTOR_SVC_UUID, True)
        self.add_characteristic(PosCharacteristic(self))
        self.add_characteristic(PosCharacteristic(self, pv_name="test2", id=3))
        self.add_characteristic(PosCharacteristic(self, pv_name="test3", id=4))

        self.add_characteristic(MovnCharacteristic(self, id=6))
        self.add_characteristic(MovnCharacteristic(self, pv_name="test2", id=7))
        self.add_characteristic(MovnCharacteristic(self, pv_name="test3", id=8))

        self.add_characteristic(UnitCharacteristic(self))


class PosCharacteristic(Characteristic):
    def __init__(self, service, pv_name="test1", id=2):
        self.notifying = False
        self.POS_CHARACTERISTIC_UUID = f"0000000{id}-710e-4a5b-8d75-3e5b444bc3cf"

        Characteristic.__init__(self, self.POS_CHARACTERISTIC_UUID, ["write", "read", "notify"], service)
        self.pv_name = pv_name
        self.value = 0
        self.add_descriptor(DescDescriptor(self))
        self.add_descriptor(TargetPosDescriptor(self))
        self.add_descriptor(PVDescriptor(self))
        self.add_descriptor(RlvPosDescriptor(self))

    def get_position(self):
        strtemp = str(round(caget(f"{self.pv_name}-RB.VAL"), 5))
        return [dbus.Byte(c.encode()) for c in strtemp]

    def set_pos_callback(self):
        if self.notifying:
            value = self.get_position()
            if value != self.value:
                self.PropertiesChanged(GATT_CHRC_IFACE, {"Value": value}, [])
                self.value = value

        return self.notifying

    def StartNotify(self):
        if self.notifying:
            return

        self.notifying = True

        value = self.get_position()
        self.PropertiesChanged(GATT_CHRC_IFACE, {"Value": value}, [])
        self.add_timeout(NOTIFY_TIMEOUT, self.set_pos_callback)

    def StopNotify(self):
        self.notifying = False

    def ReadValue(self, options):
        # Real pos
        return self.get_position()

    def WriteValue(self, value, options):
        # Target pos
        caput(self.pv_name+"-SP", "".join([str(v) for v in value]))
        return value


class DescDescriptor(Descriptor):
    POS_DESCRIPTOR_UUID = "2910"

    def __init__(self, characteristic):
        self.characteristic = characteristic
        Descriptor.__init__(self, self.POS_DESCRIPTOR_UUID, ["read"], characteristic)

    def ReadValue(self, options):
        value = []
        desc = caget(f"{self.characteristic.pv_name}-RB.DESC")

        for c in desc:
            value.append(dbus.Byte(c.encode()))

        return value


class TargetPosDescriptor(Descriptor):
    POS_DESCRIPTOR_UUID = "2911"

    def __init__(self, characteristic):
        self.characteristic = characteristic
        Descriptor.__init__(self, self.POS_DESCRIPTOR_UUID, ["read"], characteristic)

    def ReadValue(self, options):
        strtemp = str(round(caget(f"{self.characteristic.pv_name}-RB.VAL"), 5))
        return [dbus.Byte(c.encode()) for c in strtemp]

class PVDescriptor(Descriptor):
    POS_DESCRIPTOR_UUID = "2912"

    def __init__(self, characteristic):
        self.characteristic = characteristic
        Descriptor.__init__(self, self.POS_DESCRIPTOR_UUID, ["read"], characteristic)

    def ReadValue(self, options):
        return [dbus.Byte(c.encode()) for c in self.characteristic.pv_name]

class RlvPosDescriptor(Descriptor):
    POS_DESCRIPTOR_UUID = "2913"

    def __init__(self, characteristic):
        self.characteristic = characteristic
        Descriptor.__init__(self, self.POS_DESCRIPTOR_UUID, ["read", "write"], characteristic)

    def ReadValue(self, options):
        try:
            strtemp = str(round(caget(f"{self.characteristic.pv_name}-SP.VAL"), 5))
            return [dbus.Byte(c.encode()) for c in strtemp]
        except Exception as e:
            print(e)

    def WriteValue(self, value, options):
        caput(self.characteristic.pv_name + "-SP", "".join([str(v) for v in value]))
        return value

class MovnCharacteristic(Characteristic):
    def __init__(self, service, pv_name="test1", id=6):
        self.notifying = False
        self.POS_CHARACTERISTIC_UUID = f"0000000{id}-710e-4a5b-8d75-3e5b444bc3cf"

        Characteristic.__init__(self, self.POS_CHARACTERISTIC_UUID, ["read", "notify"], service)
        self.pv_name = pv_name
        self.moving = 0

    def get_status(self):
        strtemp = "1" if float(caget(f"{self.pv_name}-SP.VAL")) else "0"
        return [dbus.Byte(c.encode()) for c in strtemp]

    def set_status_callback(self):
        if self.notifying:
            status = self.get_status()
            if status != self.moving:
                self.PropertiesChanged(GATT_CHRC_IFACE, {"Value": status}, [])
                self.moving = status

        return self.notifying

    def StartNotify(self):
        if self.notifying:
            return

        self.notifying = True

        status = self.get_status()
        self.PropertiesChanged(GATT_CHRC_IFACE, {"Value": status}, [])
        self.add_timeout(NOTIFY_TIMEOUT, self.set_status_callback)

    def StopNotify(self):
        self.notifying = False

    def ReadValue(self, options):
        return self.get_status()


class UnitCharacteristic(Characteristic):
    UNIT_CHARACTERISTIC_UUID = "0000000f-710e-4a5b-8d75-3e5b444bc3cf"

    def __init__(self, service, pv_name="test1"):
        self.pv_name = pv_name
        Characteristic.__init__(self, self.UNIT_CHARACTERISTIC_UUID, ["read"], service)

    def ReadValue(self, options):
        return [dbus.Byte(caget(f"{self.pv_name}-RB.EGU").encode())]


app = Application()
app.add_service(MotorService(0))
app.register()

adv = MotorAdvertisement(0)
adv.register()

try:
    app.run()
except KeyboardInterrupt:
    app.quit()
