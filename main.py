import dbus
from epics import caget, caput

from advertisement import Advertisement
from service import Application, Service, Characteristic, Descriptor

GATT_CHRC_IFACE = "org.bluez.GattCharacteristic1"
NOTIFY_TIMEOUT = 15000


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
        self.add_characteristic(UnitCharacteristic(self))


class PosCharacteristic(Characteristic):
    def __init__(self, service, pv_name="test1", id=2):
        self.notifying = False
        self.POS_CHARACTERISTIC_UUID = f"0000000{id}-710e-4a5b-8d75-3e5b444bc3cf"

        Characteristic.__init__(self, self.POS_CHARACTERISTIC_UUID, ["write", "read", "notify"], service)
        self.pv_name = pv_name
        self.add_descriptor(PosDescriptor(self))
        self.add_descriptor(RealPosDescriptor(self))
        self.add_descriptor(PVDescriptor(self))

    def get_position(self):
        strtemp = str(round(caget(f"{self.pv_name}-RB.VAL"), 5))
        return [dbus.Byte(c.encode()) for c in strtemp]

    def set_pos_callback(self):
        if self.notifying:
            value = self.get_position()
            self.PropertiesChanged(GATT_CHRC_IFACE, {"Value": value}, [])

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
        return self.get_position()

    def WriteValue(self, value, options):
        try:
            caput(self.pv_name, "".join([str(v) for v in value]))
        except Exception as e:
            print(e)
        return value


class PosDescriptor(Descriptor):
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


class RealPosDescriptor(Descriptor):
    POS_DESCRIPTOR_UUID = "2911"

    def __init__(self, characteristic):
        self.characteristic = characteristic
        Descriptor.__init__(self, self.POS_DESCRIPTOR_UUID, ["read"], characteristic)

    def ReadValue(self, options):
        try:                             
            strtemp = str(round(caget(f"{self.characteristic.pv_name}-RB.VAL"), 5))
            return [dbus.Byte(c.encode()) for c in strtemp]
        except Exception as e:
            print(e)


class PVDescriptor(Descriptor):
    POS_DESCRIPTOR_UUID = "2912"

    def __init__(self, characteristic):
        self.characteristic = characteristic
        Descriptor.__init__(self, self.POS_DESCRIPTOR_UUID, ["read"], characteristic)

    def ReadValue(self, options):
        try:
            return [dbus.Byte(c.encode()) for c in self.characteristic.pv_name]
        except Exception as e:
            print(e)


class UnitCharacteristic(Characteristic):
    UNIT_CHARACTERISTIC_UUID = "00000006-710e-4a5b-8d75-3e5b444bc3cf"

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
