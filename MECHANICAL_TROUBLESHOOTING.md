# Mechanical Troubleshooting

- [TTY-33 Theory of Operation (DeRamp)](https://deramp.com/downloads/teletype/Model%2033/TTY-33%20Theory%20of%20Operation.pdf) — keyboard, typing unit, and interface overview
- [Soemtron Teletype manuals (ASR/KSR 33)](https://www.soemtron.org/teletypemanuals.html) — Bulletin 310B service set; especially **574-122-100TC** (typing unit) and **574-121-100TC** (keyboard)

---

## How the Model 33 actually routes data (background)

This matters for interpreting symptoms. Per the Teletype service literature and widely cited descriptions of the mechanism:

**KSR keyboard (send side)** — largely mechanical:

1. Depressing a key on the **KSR keyboard** moves a subset of **KSR keyboard coding bars** (a parallel 7-bit-plus-parity mechanical bus).
2. The **typing distributor** (rotating brush on a contact ring) serializes those levels into **110 baud, 7 data bits + even parity + 2 stop bits** (7E2).
3. In **LINE** mode, that serial stream goes to the RS-232 send pair. With echo assumed (see above), it returns on the receive pair and prints.
4. In **LOCAL** mode, the same serialized stream is routed **internally** to the typing-unit selector — see Section **574-123-100TC** (call control / mode switching).

**Typing unit (receive / print side)**:

1. Incoming serial pulses (from the line or from LOCAL loopback) pass through the **selector magnet driver**, which amplifies the 20 mA loop signal to drive the **selector magnets** (~500 mA).
2. As the **selector shaft** rotates once per character, staggered cams align each serial pulse with the correct magnet. A marking pulse pulls in a magnet and moves a **blocking lever**.
3. Blocked levers hold selected **printer code bars**; the remaining bars lift to position the **typebox** (typewheel).
4. The **print hammer** strikes the typebox against the ribbon and paper.

So: KSR keyboard encoding and printing both involve “code bars,” but they are **different mechanisms** — KSR keyboard coding bars for transmit, printer code bars positioned by the selector for print. The [Old Computer Hut ASR-33 walkthrough](http://www.oldcomputers.arcula.co.uk/perf1.htm) is a readable plain-language version of this same flow.

### Bit numbering note

This document uses **software convention** (bit 0 = LSB of 7-bit ASCII, value `0x10` = bit 4).

Teletype manuals number **intelligence bits 1–7** with **bit 1 = LSB** (first data bit on the wire). In that convention, this fault is **intelligence bit 5** — the fifth data pulse after the start bit. When reading **574-122-700TC** (typing unit adjustments), translate between the two numbering schemes.

---

## Related reading

### Official manuals (recommended)

| Resource | Contents |
|----------|----------|
| [TTY-33 Theory of Operation (DeRamp PDF)](https://deramp.com/downloads/teletype/Model%2033/TTY-33%20Theory%20of%20Operation.pdf) | High-level keyboard, typing unit, and interface theory |
| [Soemtron — Teletype ASR33 / KSR33 manuals](https://www.soemtron.org/teletypemanuals.html) | Full Bulletin **310B** service library (zipped PDFs) |
| Bulletin 310B **574-122-100TC** | Typing unit — description and operation |
| Bulletin 310B **574-122-700TC** | Typing unit — adjustments (~100 pages) |
| Bulletin 310B **574-122-701TC** | Typing unit — lubrication |
| Bulletin 310B **574-121-100TC** | KSR keyboard — description and operation |
| Bulletin 310B **574-123-100TC** | Call control unit — LOCAL / LINE / OFF |

### Community

- [CuriousMarc — Teletype restoration](https://www.youtube.com/@CuriousMarc) — practical Model 33 service and typing-unit work

### Other useful descriptions

- [Old Computer Hut — ASR-33 mechanism walkthrough](http://www.oldcomputers.arcula.co.uk/perf1.htm) — coding bars, distributor, selector, code bars, typewheel
- [Wikipedia — Teletype Model 33](https://en.wikipedia.org/wiki/Teletype_Model_33) — variants (ASR/KSR/RO), 7E2, typebox

---

## Case study: wrong letter prints on keys A–O (one bit flips)

On a KSR-33, pressing keys on the **KSR keyboard** in the **A–O** range printed a **wrong but consistent** character when idle or slow (**A** → **Q**), but printed **correctly** while typing the same key rapidly — reverting to the wrong character after a pause.

### Symptom table

| KSR key pressed | At rest / slow | While typing fast | 7-bit pattern (intended) | 7-bit pattern (wrong) |
|-------------|------------------|-------------------------|------------------------|
| A | Q | A | `1000001` (0x41) | `1010001` (0x51) |
| B | R | B | `1000010` (0x42) | `1010010` (0x52) |
| C | S | C | `1000011` (0x43) | `1010011` (0x53) |
| D | T | D | `1000100` (0x44) | `1010100` (0x54) |
| E | U | E | `1000101` (0x45) | `1010101` (0x55) |
| F | V | F | `1000110` (0x46) | `1010110` (0x56) |
| G | W | G | `1000111` (0x47) | `1010111` (0x57) |
| H | X | H | `1001000` (0x48) | `1011000` (0x58) |
| … | … | … | … |


- Wrong characters were produced sending via RS232 and via Keyboard in local mode.
- Based on this I focused on the typing unit forward excluding receive and keyboard.
- Ultimately I found that the issue was a bad "signal" generated by the 5th crossbar which was produced by stiction in the drive train leading up to the representation configuration.

The solution was to clean the drive train parts, lightly lubricate and then work them until they were moving freely.