"""Shared USB-serial open for UNO bridge tools (PC side @ 9600)."""
from __future__ import annotations

import sys

try:
    import serial
except ImportError as e:
    raise SystemExit(
        "pyserial is required: pip install pyserial  (or: apt install python3-serial)"
    ) from e

DEFAULT_BAUD = 9600
DEFAULT_DEVICE = "/dev/ttyACM0"


def connect(device: str = DEFAULT_DEVICE, baud: int = DEFAULT_BAUD):
    """Open the Arduino USB serial port; return a pyserial Serial instance."""
    try:
        ser = serial.Serial(
            port=device,
            baudrate=baud,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.05,
            write_timeout=1.0,
        )
    except serial.SerialException as e:
        print(f"Cannot open {device} @ {baud}: {e}", file=sys.stderr)
        raise SystemExit(1) from e
    # Drop any bootloader / READY noise so the terminal starts clean.
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    return ser
