/*
 * ASR-33 bridge — full duplex
 *
 * Same as uno_tty_bridge but with keyboard RX on pin 5.
 * Upload this sketch OR copy into uno_tty_bridge/uno_tty_bridge.ino
 *
 * Wiring:
 *   pin 4 -> MAX3232 TTL TXD  -> DB-9 pin 3 -> green -> DB-25 pin 2 (print)
 *   pin 5 <- MAX3232 TTL RXD  <- DB-9 pin 2 <- red   <- DB-25 pin 3 (keyboard)
 */

#define USE_8N2 0
#define LOCAL_ECHO 1   // keyboard -> print on teletype + forward to PC

const uint8_t TTY_TX_PIN = 4;
const uint8_t TTY_RX_PIN = 5;
const unsigned long BIT_US = 9091;
const unsigned long CHAR_GAP_MS = 130;
// Minimum CR settle; actual gap scales with columns printed on the line.
const unsigned long CR_GAP_MIN_MS = 250;
const unsigned long CR_MS_PER_COL = 8;
const unsigned long CR_GAP_MAX_MS = 900;
// Pause after LF before the next print character.
const unsigned long LF_GAP_MS = 350;
// Double CR: reliable return without extra paper advance.
const uint8_t NEWLINE_CR_COUNT = 2;
const uint8_t NEWLINE_LF_COUNT = 1;
// Worst-case bytes hostToTty may push for one host byte.
const uint8_t HOST_EXPAND_MAX = 3;
const unsigned long HOST_BAUD = 9600;

const size_t BUF_SIZE = 512;

uint8_t ring[BUF_SIZE];
size_t head = 0;
size_t tail = 0;
unsigned long lastTxMs = 0;
unsigned long nextGapMs = CHAR_GAP_MS;
uint8_t printCol = 0;

bool bufFull() {
  return ((head + 1) % BUF_SIZE) == tail;
}

bool bufEmpty() {
  return head == tail;
}

bool bufPush(uint8_t b) {
  if (bufFull()) return false;
  ring[head] = b;
  head = (head + 1) % BUF_SIZE;
  return true;
}

bool bufPop(uint8_t *b) {
  if (bufEmpty()) return false;
  *b = ring[tail];
  tail = (tail + 1) % BUF_SIZE;
  return true;
}

size_t bufFree() {
  if (head >= tail) {
    return BUF_SIZE - 1 - (head - tail);
  }
  return tail - head - 1;
}

unsigned long crGapForCol(uint8_t col) {
  unsigned long gap = CR_GAP_MIN_MS + (unsigned long)col * CR_MS_PER_COL;
  if (gap > CR_GAP_MAX_MS) {
    gap = CR_GAP_MAX_MS;
  }
  return gap;
}

void flushHostSerial() {
  while (Serial.available()) {
    Serial.read();
  }
}

void ttyIdle() {
  digitalWrite(TTY_TX_PIN, HIGH);
}

void ttyWriteBit(bool bit) {
  digitalWrite(TTY_TX_PIN, bit ? HIGH : LOW);
  delayMicroseconds(BIT_US);
}

bool ttyReadBit() {
  delayMicroseconds(BIT_US);
  return digitalRead(TTY_RX_PIN) == HIGH;
}

void ttySend7E2(uint8_t c) {
  uint8_t data = c & 0x7F;
  uint8_t ones = 0;
  for (uint8_t i = 0; i < 7; i++) {
    if (data & (1u << i)) ones++;
  }
  bool parity = (ones % 2) != 0;

  ttyWriteBit(false);
  for (uint8_t i = 0; i < 7; i++) {
    ttyWriteBit((data >> i) & 1);
  }
  ttyWriteBit(parity);
  ttyWriteBit(true);
  ttyWriteBit(true);
}

void ttySend8N2(uint8_t c) {
  uint8_t data = c & 0xFF;
  ttyWriteBit(false);
  for (uint8_t i = 0; i < 8; i++) {
    ttyWriteBit((data >> i) & 1);
  }
  ttyWriteBit(true);
  ttyWriteBit(true);
}

void ttySendWire(uint8_t c) {
#if USE_8N2
  ttySend8N2(c);
#else
  ttySend7E2(c);
#endif
}

bool ttyReceive7E2(uint8_t *out) {
  if (digitalRead(TTY_RX_PIN) != LOW) {
    return false;
  }

  delayMicroseconds(BIT_US / 2);
  if (digitalRead(TTY_RX_PIN) != LOW) {
    return false;
  }

  uint8_t data = 0;
  for (uint8_t i = 0; i < 7; i++) {
    if (ttyReadBit()) {
      data |= (1u << i);
    }
  }
  (void)ttyReadBit();

  if (!ttyReadBit()) {
    return false;
  }
  if (!ttyReadBit()) {
    return false;
  }

  *out = data & 0x7F;
  return true;
}

bool ttyReceive8N2(uint8_t *out) {
  if (digitalRead(TTY_RX_PIN) != LOW) {
    return false;
  }

  delayMicroseconds(BIT_US / 2);
  if (digitalRead(TTY_RX_PIN) != LOW) {
    return false;
  }

  uint8_t data = 0;
  for (uint8_t i = 0; i < 8; i++) {
    if (ttyReadBit()) {
      data |= (1u << i);
    }
  }

  if (!ttyReadBit()) {
    return false;
  }
  if (!ttyReadBit()) {
    return false;
  }

  *out = data;
  return true;
}

bool ttyReceiveWire(uint8_t *out) {
#if USE_8N2
  return ttyReceive8N2(out);
#else
  return ttyReceive7E2(out);
#endif
}

void hostToTty(uint8_t c) {
  // Teletype needs CR (return) + LF (paper advance). Host may send LF, CR, or CRLF.
  // Ignore bare CR; expand LF to N×CR + M×LF (defaults: CR CR LF).
  // Caller must ensure bufFree() >= HOST_EXPAND_MAX so nothing is dropped.
  if (c == '\r') {
    return;
  }
  if (c == '\n') {
    for (uint8_t i = 0; i < NEWLINE_CR_COUNT; i++) {
      bufPush('\r');
    }
    for (uint8_t i = 0; i < NEWLINE_LF_COUNT; i++) {
      bufPush('\n');
    }
    return;
  }
  bufPush(c);
}

void setup() {
  pinMode(TTY_TX_PIN, OUTPUT);
  pinMode(TTY_RX_PIN, INPUT);
  ttyIdle();
  Serial.begin(HOST_BAUD);

  delay(400);
  flushHostSerial();
  delay(100);
  flushHostSerial();

  Serial.println(F("READY"));
  Serial.flush();
  lastTxMs = millis();
}

void loop() {
  // Backpressure: never read host bytes we cannot queue. Dropped bytes were
  // the main cause of missing CR/LF and corrupted file prints.
  while (Serial.available() && bufFree() >= HOST_EXPAND_MAX) {
    hostToTty((uint8_t)Serial.read());
  }

  if (!bufEmpty() && (millis() - lastTxMs) >= nextGapMs) {
    uint8_t c;
    if (bufPop(&c)) {
      ttySendWire(c);
      lastTxMs = millis();
      if (c == '\r') {
        nextGapMs = crGapForCol(printCol);
        printCol = 0;
      } else if (c == '\n') {
        nextGapMs = LF_GAP_MS;
        printCol = 0;
      } else {
        if (c >= 0x20 && printCol < 255) {
          printCol++;
        }
        nextGapMs = CHAR_GAP_MS;
      }
    }
  }

  uint8_t rx;
  if (ttyReceiveWire(&rx)) {
    Serial.write(rx);
#if LOCAL_ECHO
    if (bufFree() >= 1) {
      bufPush(rx);
    }
#endif
  }
}
