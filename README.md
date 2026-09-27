# razer-battery-status

A tiny, sudo-free, dependency-free battery readout for a Razer wireless mouse on
Linux. It talks to the mouse directly over **raw HID** (`/dev/hidraw*`) — no
OpenRazer, no kernel module, no daemon.

The Razer app is Windows-only. This performs the same feature-report exchange the
OpenRazer driver uses to read the battery, but from userspace, so it keeps working
across kernel upgrades (the OpenRazer DKMS module historically fails to build on
each new kernel — which is why this was rewritten off it).

## Usage

```sh
./razer-battery            # Razer Naga V2 HyperSpeed: 74% (charging)
./razer-battery --percent  # 74
./razer-battery --emoji    # 🔋 74%
./razer-battery --bar      # 🔋 ███████░░░ 74%
./razer-battery --notify   # KDE passive popup: "Razer Mouse Battery / 74%" (needs kdialog)
```

Pure Python 3 standard library — no `pip install`, no `openrazer`, no `hidapi`.

## Requirements

- Python 3.
- Read/write access to the mouse's `/dev/hidraw*` node. Those nodes are root-only
  by default, so a udev rule is needed (see below). No membership in any Razer/
  OpenRazer group is required.

## Install (the udev rule)

`/dev/hidraw*` is root-only out of the box. Grant your login group access to Razer
HID nodes with a udev rule, e.g. `/etc/udev/rules.d/60-razer-battery.rules`:

```
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="1532", GROUP="plugdev", MODE="0660"
```

Use whichever group your user is in (`plugdev` is standard). Then reload:

```sh
sudo udevadm control --reload-rules
sudo udevadm trigger --subsystem-match=hidraw --action=add
```

Drop the script somewhere on your `PATH`:

```sh
install -Dm755 razer-battery ~/.local/bin/razer-battery
```

> On the author's workstation this is deployed as config-as-code: the udev rule
> lives in the `my-system` repo (`system/etc-udev-rules.d/60-razer-battery.rules`,
> group `developers`) and the script in `users/ethan/localbin/`, both applied by
> `install.sh`.

## How it works

For each Razer HID interface (found via `/sys/class/hidraw/*/device/uevent`,
vendor `1532`), it sends a 90-byte Razer report as a HID feature report
(command class `0x07`, id `0x80` battery / `0x84` charging, XOR checksum over
bytes 2–87), waits, reads the reply back, and scales byte 9 from `0–255` to a
percentage. Report ids, transaction id and scaling all come from OpenRazer's
driver.

The per-device HID **transaction id** defaults to `0x1f`, which covers the current
HyperSpeed/receiver generation. For an untested device that answers on a different
id (OpenRazer also uses `0x3f` and `0xff`), override it:

```sh
RAZER_TRANSACTION_ID=0x3f ./razer-battery
```

## Hotkey (optional)

`--notify` pops a passive KDE popup and exits, which makes it a good target for a
global hotkey. Bind `razer-battery --notify` to any key via your desktop's
keyboard-shortcut settings.

## Tested devices

- Razer Naga V2 HyperSpeed (`1532:00b4`, transaction id `0x1f`)

Any Razer device that reports a battery should work; set `RAZER_TRANSACTION_ID`
if the default id doesn't answer.
