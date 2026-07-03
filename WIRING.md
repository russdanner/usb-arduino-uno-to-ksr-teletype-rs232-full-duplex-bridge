# Wiring Guide

Connect a modern PC to a DeRamp-equipped Teletype Model 33 (KSR/ASR-33) through an Arduino Uno and an RS-232 level shifter. This only works for **DeRamp** (or similar) RS-232 interface on the Teletype. Raw 20 mA current-loop machines need a different interface entirely.

The PC talks to the Arduino over USB at **9600 baud**. The Arduino bit-bangs **110 baud, 7E2** on two GPIO pins for the Teletype side. A MAX232 or MAX3232 module converts between Arduino TTL and RS-232 levels.

The firmware is a full-duplex translator: it accepts fast 8-bit bytes from the PC, queues and paces them into slow 7E2 Teletype characters on GPIO, and does the reverse for keyboard input 

## Parts

| Part | Notes |
|------|-------|
| Arduino Uno (or compatible) | USB serial to the PC |
| MAX232 or MAX3232 module | RS-232 level shifter; common breakout boards work |
| DB-9 female connector (or cable) | RS-232 side toward the DeRamp interface |
| Hookup wire | 22–26 AWG is fine for a bench setup |
| USB cable | Arduino programming and host link |

Optional: breadboard, perfboard, or a small project box for a permanent build.

## Signal path
Note: I show DB-25 below because that's what ships with the DeRamp. I use (and detail) a DB9 to RJ12 below.

```
PC (USB)
  │
  ▼ 
Arduino Uno (9600 baud serial step to 110 7E2 via firmware)
  │
  ├─ pin 4 (TX) ──► MAX3232 TTL in  ──► RS-232 TX ──► DB-9 pin 3 ──► green ──► DB-25 pin 2 (print)
  │
  └─ pin 5 (RX) ◄── MAX3232 TTL out ◄── RS-232 RX ◄── DB-9 pin 2 ◄── red   ◄── DB-25 pin 3 (keyboard)
```

- **Print** = data from PC/Arduino to the Teletype printer (host → machine).
- **Keyboard** = data from the Teletype keyboard back to the PC (machine → host).

This matches the full-duplex sketch in `arduino/uno_tty_bridge_duplex/uno_tty_bridge_duplex.ino`.

## Arduino ↔ MAX232/MAX3232

Wire the **TTL side** of the level-shifter module to the Uno:

| Arduino Uno | MAX232 / MAX3232 module (TTL side) |
|-------------|-------------------------------------|
| 5V | VCC |
| GND | GND |
| Digital pin **4** | TXD in (often labeled **T1IN** or **TX**) |
| Digital pin **5** | RXD out (often labeled **R1OUT** or **RX**) |

## MAX232/MAX3232 ↔ DB-9

Wire the **RS-232 side** of the module to a **DB-9 female** (typical PC-style connector facing the cable):

| MAX232 / MAX3232 (RS-232 side) | DB-9 pin | RS-232 signal |
|----------------------------------|----------|---------------|
| TX out (e.g. **T1OUT**) | **3** | TXD |
| RX in (e.g. **R1IN**) | **2** | RXD |
| GND | **5** | Signal ground |


## DB-9 ↔ DeRamp / Teletype

Use a standard serial cable from the DB-9 to the DeRamp RS-232 port (usually **DB-25** on the Teletype interface). You can use a standard DB9 -> DB25 connector. I just wired my own DB9 to RJ12/11 connector.

On this project’s machine, the DeRamp harness uses:

| DB-9 (via cable) | Wire color | DB-25 pin | Function |
|------------------|------------|-----------|----------|
| Pin **3** (TXD) | **Green** | **2** | Print (to Teletype) |
| Pin **2** (RXD) | **Red** | **3** | Keyboard (from Teletype) |

**Ground:** tie DB-9 pin **5** to the DeRamp/signal ground. A missing or poor ground often shows up as garbage characters or no receive.

## Pin summary

| Signal | Arduino | DB-9 | DeRamp / DB-25 |
|--------|---------|------|----------------|
| To printer (TX) | D4 | 3 | 2 (green) |
| From keyboard (RX) | D5 | 2 | 3 (red) |
| Ground | GND | 5 | 7 (black) |

## Firmware

1. Open `arduino/uno_tty_bridge_duplex/uno_tty_bridge_duplex.ino` in the Arduino IDE.
2. Select board **Arduino Uno** and the correct USB port.
3. Upload the sketch.
4. Open the serial monitor at **9600 baud**; you should see `READY` after reset.

Key settings in the sketch (change only if you know you need to):

| Define | Default | Purpose |
|--------|---------|---------|
| `TTY_TX_PIN` | 4 | Teletype transmit (bit-bang) |
| `TTY_RX_PIN` | 5 | Teletype receive (bit-bang) |
| `HOST_BAUD` | 9600 | USB serial to PC |
| `USE_8N2` | 0 | `0` = 7E2 (Teletype); `1` = 8N2 |
| `LOCAL_ECHO` | 1 | Keyboard input echoed to printer on the machine |

## PC connection

After upload, the Arduino appears as a USB serial device (e.g. `/dev/ttyACM0` on Linux).

```bash
python3 tools/tty_term.py -d /dev/ttyACM0
```

## Figures
DeRamp to RJ12/11 Straight through
<img width="335" height="281" alt="image" src="https://github.com/user-attachments/assets/a99cd3af-5b0e-4b41-bb95-125eb857bf90" />

RJ12/11 to DB-25 
<img width="484" height="822" alt="image" src="https://github.com/user-attachments/assets/88f163b9-fd3b-4539-8381-9db1c3864905" />

RJ12/11 to DB-9 ◄── / ──► MAX3232 ◄── / ──► Arduino Uno
<img width="1536" height="2048" alt="image" src="https://github.com/user-attachments/assets/b1e23f70-748f-4b8c-b0c9-35a7660b47f1" />

Once you have things going, tighten and enclose everything up so it's nice and clean.

## Related reading

- [README.md](README.md) — project background and why a USB–RS-232 cable alone is not enough
