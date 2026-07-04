#!/usr/bin/env python3.10
"""Send a text file to the Teletype via the UNO bridge.

Paces at teletype speed so the Arduino ring buffer never overflows (overflow
used to silently drop CR/LF and corrupt prints like ASCII art).

Firmware expands each LF to CR CR LF and scales CR settle time by line length.
Re-upload uno_tty_bridge_duplex.ino before using.

  python3.10 tools/tty_send.py tools/cc.txt
  python3.10 tools/tty_send.py tools/cc.txt -d /dev/ttyACM0

Ctrl-C aborts the send.
"""
from __future__ import annotations

import argparse
import sys
import time

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bridge_serial import DEFAULT_BAUD, DEFAULT_DEVICE, connect

# Must stay >= firmware CHAR_GAP_MS / CR / LF budgets or the ring fills.
CHAR_S = 0.15
CR_MIN_S = 0.25
CR_PER_COL_S = 0.008
CR_MAX_S = 0.90
LF_S = 0.38
# Firmware NEWLINE_CR_COUNT
CR_COUNT = 2


def prepare_lines(raw: bytes) -> list[str]:
    text = raw.decode("utf-8", errors="replace")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines: list[str] = []
    for line in text.split("\n"):
        out = []
        for ch in line:
            b = ord(ch)
            if b == 0x09:  # tab -> spaces
                out.append(" ")
                continue
            if b == 0x7F or b > 0x7F:
                continue
            if b < 0x20:
                continue
            out.append(ch)
        lines.append("".join(out))
    # split("\n") drops a trailing empty only if file ends with newline;
    # keep a final empty line only when the file had a trailing newline.
    if text.endswith("\n") and (not lines or lines[-1] != ""):
        pass
    return lines


def cr_settle_s(cols: int) -> float:
    return min(CR_MAX_S, CR_MIN_S + cols * CR_PER_COL_S)


def newline_budget_s(cols: int) -> float:
    # CR (scaled) + CR (min) + LF, matching firmware gaps.
    return cr_settle_s(cols) + cr_settle_s(0) + LF_S


def send_file(ser, lines: list[str]) -> None:
    total_chars = sum(len(line) for line in lines) + len(lines)
    if total_chars == 0:
        print("Nothing to send.", file=sys.stderr)
        return

    print(
        f"Sending {len(lines)} lines ({total_chars} host bytes) to {ser.port} …",
        file=sys.stderr,
    )
    sent = 0
    try:
        for line_no, line in enumerate(lines, start=1):
            for ch in line:
                ser.write(ch.encode("ascii"))
                ser.flush()
                sent += 1
                time.sleep(CHAR_S)
            # One LF; firmware expands to CR CR LF with column-scaled CR gaps.
            ser.write(b"\n")
            ser.flush()
            sent += 1
            time.sleep(newline_budget_s(len(line)))
            print(
                f"\rline {line_no}/{len(lines)}  bytes {sent}/{total_chars}",
                end="",
                file=sys.stderr,
                flush=True,
            )
    except KeyboardInterrupt:
        print(f"\nAborted after {sent}/{total_chars} bytes.", file=sys.stderr)
        raise SystemExit(130) from None
    print("\nDone.", file=sys.stderr)


def main() -> None:
    p = argparse.ArgumentParser(
        description="Send a text file to the Teletype at teletype speed"
    )
    p.add_argument("file", type=Path, help="ASCII/UTF-8 text file to print")
    p.add_argument("-d", "--device", default=DEFAULT_DEVICE)
    p.add_argument("-b", "--baud", type=int, default=DEFAULT_BAUD)
    p.add_argument(
        "--form-feed",
        action="store_true",
        help="send a form feed (FF) after the file",
    )
    args = p.parse_args()

    if not args.file.is_file():
        print(f"Not a file: {args.file}", file=sys.stderr)
        raise SystemExit(1)

    lines = prepare_lines(args.file.read_bytes())
    # Estimate wall time so the user knows it is slow on purpose.
    est = sum(len(line) * CHAR_S + newline_budget_s(len(line)) for line in lines)
    print(f"Estimated print time: {est / 60:.1f} min", file=sys.stderr)

    ser = connect(args.device, args.baud)
    # Allow USB backpressure to block instead of timing out mid-line.
    ser.write_timeout = None
    try:
        time.sleep(0.3)
        send_file(ser, lines)
        if args.form_feed:
            ser.write(b"\f")
            ser.flush()
            time.sleep(CHAR_S)
        # Final drain for last newline expansion.
        if lines:
            time.sleep(newline_budget_s(len(lines[-1])))
    finally:
        ser.close()


if __name__ == "__main__":
    main()
