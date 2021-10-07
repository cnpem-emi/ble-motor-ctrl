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
    POS_CHARACTERISTIC_UUID = "00000002-710e-4a5b-8d75-3e5b444bc3cf"

    def __init__(self, service):
        self.notifying = False

        Characteristic.__init__(self, self.POS_CHARACTERISTIC_UUID, ["write", "read", "notify"], service)
        self.add_descriptor(PosDescriptor(self))
        self.add_descriptor(RealPosDescriptor(self))
        self.add_descriptor(PVDescriptor(self))

    def get_position(self):
        strtemp = str(round(caget("test1-SP.VAL"), 5))
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
            caput("test1-SP", "".join([str(v) for v in value]))
        except Exception as e:
            print(e)
        return value


class PosDescriptor(Descriptor):
    POS_DESCRIPTOR_UUID = "2910"

    def __init__(self, characteristic):
        Descriptor.__init__(self, self.POS_DESCRIPTOR_UUID, ["read"], characteristic)

    def ReadValue(self, options):
        value = []
        desc = caget("test1-RB.DESC")

        for c in desc:
            value.append(dbus.Byte(c.encode()))

        return value


class RealPosDescriptor(Descriptor):
    POS_DESCRIPTOR_UUID = "2911"

    def __init__(self, characteristic):
        Descriptor.__init__(self, self.POS_DESCRIPTOR_UUID, ["read"], characteristic)

    def ReadValue(self, options):
        strtemp = str(round(caget("test1-RB.VAL"), 5))
        return [dbus.Byte(c.encode()) for c in strtemp]


class PVDescriptor(Descriptor):
    POS_DESCRIPTOR_UUID = "2912"

    def __init__(self, characteristic):
        Descriptor.__init__(self, self.POS_DESCRIPTOR_UUID, ["read"], characteristic)

    def ReadValue(self, options):
        return [dbus.Byte(c.encode()) for c in "input1"]


class UnitCharacteristic(Characteristic):
    UNIT_CHARACTERISTIC_UUID = "00000006-710e-4a5b-8d75-3e5b444bc3cf"

    def __init__(self, service):
        Characteristic.__init__(self, self.UNIT_CHARACTERISTIC_UUID, ["read"], service)
        self.add_descriptor(UnitDescriptor(self))

    def ReadValue(self, options):
        return [dbus.Byte(caget("test1-RB.EGU").encode())]


class UnitDescriptor(Descriptor):
    UNIT_DESCRIPTOR_UUID = "2901"
    UNIT_DESCRIPTOR_VALUE = "Unit"

    def __init__(self, characteristic):
        Descriptor.__init__(self, self.UNIT_DESCRIPTOR_UUID, ["read"], characteristic)

    def ReadValue(self, options):
        value = []
        desc = self.UNIT_DESCRIPTOR_VALUE

        for c in desc:
            value.append(dbus.Byte(c.encode()))

        return value


app = Application()
app.add_service(MotorService(0))
app.register()

adv = MotorAdvertisement(0)
adv.register()

try:
    app.run()
except KeyboardInterrupt:
    app.quit()
