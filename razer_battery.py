#!/usr/bin/env python3
"""Read Razer wireless mouse battery via raw HID feature reports. No deps."""
import fcntl, glob, struct, time, sys

# ioctl encodings for hidraw (asm-generic)
def _IOC(d, t, nr, size): return (d << 30) | (size << 16) | (ord(t) << 8) | nr
_WR = 1 | 2  # _IOC_WRITE | _IOC_READ
def HIDIOCSFEATURE(l): return _IOC(_WR, 'H', 0x06, l)
def HIDIOCGFEATURE(l): return _IOC(_WR, 'H', 0x07, l)

def razer_crc(msg):  # xor over bytes 2..87 of the 90-byte payload
    c = 0
    for b in msg[2:88]:
        c ^= b
    return c

def build(txid, cclass, cid, dsize):
    m = bytearray(90)
    m[0] = 0x00            # status: new command
    m[1] = txid            # transaction id (device-specific)
    m[5] = dsize           # data size
    m[6] = cclass          # command class
    m[7] = cid             # command id
    m[88] = razer_crc(m)   # crc
    return bytes(m)

def query(path, txid, cid):
    payload = build(txid, 0x07, cid, 0x02)
    with open(path, 'wb+', buffering=0) as f:
        # SET_FEATURE: buffer = report_id(0) + 90 payload bytes
        buf = bytearray(b'\x00' + payload)
        fcntl.ioctl(f, HIDIOCSFEATURE(len(buf)), buf, True)
        time.sleep(0.06)
        rbuf = bytearray(91)
        rbuf[0] = 0x00
        fcntl.ioctl(f, HIDIOCGFEATURE(len(rbuf)), rbuf, True)
        return rbuf[1:]  # strip report id -> 90-byte response

def find_hidraws():
    out = []
    for hp in glob.glob('/sys/class/hidraw/hidraw*'):
        try:
            ue = open(hp + '/device/uevent').read()
        except OSError:
            continue
        if '1532' in ue and '00B4' in ue.upper():
            out.append('/dev/' + hp.rsplit('/', 1)[1])
    return out

def main():
    devs = find_hidraws()
    if not devs:
        print("No Razer Naga V2 HyperSpeed hidraw node found.", file=sys.stderr)
        sys.exit(1)
    # transaction ids seen across Razer wireless receivers; first sane hit wins
    txids = [0x1f, 0x3f, 0x9f, 0xff, 0x08, 0x88, 0x00]
    for dev in devs:
        for txid in txids:
            try:
                r = query(dev, txid, 0x80)  # 0x80 = get battery level
            except OSError:
                break  # this node doesn't take feature reports; next node
            if razer_crc(r) != r[88] or r[6] != 0x07 or r[7] != 0x80:
                continue
            level = r[9]
            if not 0 < level <= 255:
                continue
            pct = round(level / 255 * 100)
            charging = None
            try:
                c = query(dev, txid, 0x84)  # 0x84 = charging status
                if c[6] == 0x07 and c[7] == 0x84:
                    charging = bool(c[9])
            except OSError:
                pass
            state = " (charging)" if charging else ""
            print(f"Razer Naga V2 HyperSpeed battery: {pct}%{state}"
                  f"   [raw {level}/255, txid 0x{txid:02x}, {dev}]")
            return
    print("Could not read battery (no transaction id responded). "
          "Mouse may be asleep — move it and retry.", file=sys.stderr)
    sys.exit(2)

if __name__ == '__main__':
    main()
