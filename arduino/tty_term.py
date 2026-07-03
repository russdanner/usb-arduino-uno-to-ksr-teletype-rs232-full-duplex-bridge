#!/usr/bin/env python3.10
"""Two-way terminal: PC keyboard <-> UNO bridge @ 9600 <-> ASR-33.

Upload arduino/uno_tty_bridge/uno_tty_bridge.ino (TX pin 4, RX pin 5 wired).

  python3.10 arduino/tty_term.py
  python3.10 arduino/tty_term.py -d /dev/ttyACM0
  python3.10 arduino/tty_term.py --hex          # show keyboard bytes as hex

Type on the PC keyboard to print on the teletype.
Type on the teletype keyboard — echoed to printer + shown here (P-Z clean on this machine).
Ctrl-C to quit.
"""
from __future__ import annotations

import argparse
import os
import select
import sys
import termios
import tty

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bridge_serial import DEFAULT_BAUD, DEFAULT_DEVICE, connect


def run_bridge(ser, hex_mode: bool, local_echo: bool) -> None:
    fd = ser.fileno()
    stdin_fd = sys.stdin.fileno()
    old = termios.tcgetattr(stdin_fd)
    tty.setcbreak(stdin_fd)

    print(
        f"Bridge open: {ser.port} @ {ser.baudrate}  "
        f"(local echo {'on' if local_echo and not hex_mode else 'off'}, Ctrl-C quit)\n",
        flush=True,
    )

    try:
        while True:
            rlist, _, _ = select.select([stdin_fd, fd], [], [], 0.05)
            if stdin_fd in rlist:
                data = os.read(stdin_fd, 256)
                if not data:
                    break
                ser.write(data)
                ser.flush()
            if fd in rlist:
                data = ser.read(ser.in_waiting or 256)
                if not data:
                    continue
                if local_echo and not hex_mode:
                    ser.write(data)
                    ser.flush()
                if hex_mode:
                    text = " ".join(f"{b:02x}" for b in data)
                    sys.stdout.write(text + "\n")
                else:
                    sys.stdout.buffer.write(data)
                sys.stdout.flush()
    except KeyboardInterrupt:
        print("\n[quit]", flush=True)
    finally:
        termios.tcsetattr(stdin_fd, termios.TCSADRAIN, old)


def main() -> None:
    p = argparse.ArgumentParser(
        description="Full-duplex terminal via UNO ASR-33 bridge @ 9600"
    )
    p.add_argument("-d", "--device", default=DEFAULT_DEVICE)
    p.add_argument("-b", "--baud", type=int, default=DEFAULT_BAUD)
    p.add_argument(
        "--hex",
        action="store_true",
        help="Print teletype RX as hex lines (debug keyboard wire values)",
    )
    p.add_argument(
        "--no-local-echo",
        action="store_true",
        help="Do not echo teletype keys back to printer (use if firmware has LOCAL_ECHO)",
    )
    args = p.parse_args()

    ser = connect(args.device, args.baud)
    try:
        run_bridge(ser, args.hex, local_echo=not args.no_local_echo)
    finally:
        ser.close()


if __name__ == "__main__":
    main()
