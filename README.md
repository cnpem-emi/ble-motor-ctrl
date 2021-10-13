# BLE Motor Control

# What is it?
An EPICS motor control interface that communicates through Bluetooth LE with any BLE capable device.

# Installation

```bash
apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0
pip3 install dbus-python 
```

# Running 
```bash
python3 main.py
```

# Structure

## Services

`84e7f883-7c80-4b64-88a5-6077ce2e8925` - Motor Control

## Characteristics and descriptors

All characteristics are terminated in `-4a5b-8d75-3e5b444bc3cf`

### `00000002-710e` through `00000005-710e`

* Holds movement control and identification data. When read/notifying, returns the `.RBV` field (current position). When written to, writes to the `.VAL` field (target position).
* Permissions: Read, Write, Notify

#### 0x2910 - Description

* Holds the `.DESC` field for the PV that is being communicated with
* Permissions: Read

#### 0x2911 - Target position

* Holds the `.VAL` field for the PV that is being communicated with (target position). To write the desired position, write to the parent characteristic.
* Permissions: Read

#### 0x2912 - PV name

* Holds the name of the PV being communicated with.
* Permissions: Read

#### 0x2913 - Relative position

* Reads/writes to the `.RLV` field (relative position).
* Permissions: Read, Write

#### 0x2914 - Limit violation

* Holds the `.LVIO` field (limit violation). Returns `1` when the target position is outside the limit range, `0` for no limit violation.
* Permissions: Read

#### 0x2915 - Stop movement

* Stops movement for the motor when `1` is written to it. Refers to the `.STOP` field.
* Permissions: Write

### `00000002-710f` through `00000005-710f` (Movement status)

* Holds `.MOVN` field (movement status). Returns `1` when moving, `0` when stopped.
* Permissions: Read, Notify
`
