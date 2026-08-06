# razer-battery-status

A tiny, sudo-free battery readout for a Razer wireless mouse on Linux, using the
[OpenRazer](https://openrazer.github.io/) daemon.

The Razer app is Windows-only, so this reads the battery straight from the
`openrazer-daemon` instead.

## Requirements

- `openrazer-meta` installed and its DKMS driver built (see *Install* below).
- Your user in the `plugdev` group.
- `openrazer-daemon` running in your session (systemd `--user` service).

## Usage

```sh
./razer-battery            # Razer Naga V2 HyperSpeed: 74% (charging)
./razer-battery --percent  # 74
./razer-battery --emoji    # 🔋 74%
./razer-battery --bar      # 🔋 ███████░░░ 74%
./razer-battery --notify   # KDE passive popup: "Razer Mouse Battery / 74%" (needs kdialog)
```

## Install (Debian 13, kernel 6.12)

```sh
sudo apt-get install openrazer-meta
sudo gpasswd -a "$USER" plugdev      # if not already a member; then re-login
systemctl --user enable --now openrazer-daemon.service
```

On kernel 6.12 the packaged 3.10.2 driver needs a one-line fix
(`hid_report_raw_event` gained a `bufsize` argument):

```sh
sudo sed -i 's/hid_report_raw_event(hdev, HID_INPUT_REPORT, xdata, sizeof(xdata), 0);/hid_report_raw_event(hdev, HID_INPUT_REPORT, xdata, sizeof(xdata), sizeof(xdata), 0);/g' \
  /usr/src/openrazer-driver-3.10.2/driver/razerkbd_driver.c
sudo dpkg --configure -a             # rebuilds the DKMS module
```

Then replug the wireless dongle so the `razermouse` driver binds.

## KDE shortcut (Meta+B)

Bind the notification to a hotkey so you can check the battery any time:

1. **System Settings → Keyboard → Shortcuts**.
2. Click **`Add New ▾` → Command or Script…**.
3. Paste the full command and press Enter:

   ```
   /srv/dev/repos/razer-battery-status/razer-battery --notify
   ```

4. Click the entry's **Add Shortcut** button and press **Meta+B**
   (accept the reassignment, or pick another combo if it's taken).
5. Click **Apply**.

Now **Meta+B** pops up `Razer Mouse Battery / 74%`, which auto-hides after a few
seconds. It works whenever `openrazer-daemon` is running in your session.

## Tested devices

- Razer Naga V2 HyperSpeed (`1532:00b4`)

Any Razer device OpenRazer supports and that reports a battery will work.
