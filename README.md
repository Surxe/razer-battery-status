# razer-battery-status

Read the battery level of a Razer wireless mouse on Linux without OpenRazer.

The Razer app is Windows-only, and the Linux kernel doesn't expose the battery
of the Naga V2 HyperSpeed anywhere (`/sys/class/power_supply`, `upower` — nothing).
This script sends Razer's HID feature-report protocol straight to the wireless
dongle and prints the battery percentage. Pure Python, **no dependencies**
(`hidapi`/`pyusb` not required — it uses raw `ioctl`).

## Usage

The device node (`/dev/hidrawN`) is root-owned, so the query needs root:

```sh
sudo ./razer_battery.py
```

Wake the mouse first (give it a wiggle) — a sleeping mouse won't answer.

Example output:

```
Razer Naga V2 HyperSpeed battery: 74%   [raw 189/255, txid 0x1f, /dev/hidraw10]
```

## How it works

It builds Razer's 90-byte report (command class `0x07`, command id `0x80` for
battery level, `0x84` for charging status), sends it via `HIDIOCSFEATURE`, reads
the reply via `HIDIOCGFEATURE`, and validates the checksum. Razer uses a
per-model "transaction id" byte, so the script tries a list of known values and
accepts the first reply with a valid CRC and a sane 0–100% reading.

## Avoiding sudo (optional)

Install a udev rule so your user can read the device without root:

```sh
# /etc/udev/rules.d/99-razer-battery.rules
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="1532", ATTRS{idProduct}=="00b4", MODE="0660", GROUP="plugdev"
```

Then `sudo udevadm control --reload && sudo udevadm trigger`, ensure your user is
in `plugdev`, and replug the dongle.

## Tested devices

- Razer Naga V2 HyperSpeed (`1532:00b4`)

Other Razer wireless mice likely work too — update the product id in the udev
rule and the transaction-id list if needed.
