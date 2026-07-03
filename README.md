**This project contains:**

- Arduino + MAX232 Uno code and wiring for the Teletype 33 (with RS232 compatibility)
- Related utilities

**Why would anyone want such a thing you ask? Well.. Here's the background:**

A friend, Marcus Mera, sent me home with his KSR-33 Teletype — Automatic Send and Receive — and if you don’t know what one is, it is literally a marvel of mechanical, electrical, and computing theory.

The Teletype is an insanely intricate, clockwork-style machine that can type, encode, transmit, decode, receive, and print. It is one of the “missing links” in computing history: a great point of confluence where mechanical engineering, electrical signaling, and information theory all meet.

Connecting the Teletype to a modern PC turned out to be more challenging than I originally thought.

I run Linux, so I figured I could just grab a USB-to-RS-232 cable, open `/dev/ttyUSB0`, set it to 110 baud, 7E2, and start communicating.

Not so fast (no pun intended)

Teletypes do not speak RS-232. They use a 20 mA current loop. That said, there are conversion kits, like the DeRamp card, and Marcus’s machine already has one. So in theory, you can go from USB to the Teletype over RS-232 with an off-the-shelf cable for a couple of bucks.

It doesn't work. I know. I saw me try and fail (for days)

Long story short: everything will report that you are running at the right baud rate, but the Teletype just cannot quite keep up, and the laptop cannot quite “go slow enough” to frame the signal perfectly for the machine.
So you can either buy a really expensive cable ... 

Or you can spend another $28 and build your own USB-to-RS-232 bridge using an Arduino, a little code, and a MAX232 IC. The PC talks to the Arduino at a comfortable modern baud rate (e.g. 9600), and the Arduino carefully steps the signal down to a real 110 baud for the DeRamp / Teletype interface. Which I think is more fun anyway! CuriousMarc seems to be a leading expert in Teletype restoration. A true master. He figured out years ago that "this" was an issue and built a solution (and some features) using the Ardino Mega, a MAXRS232 chip and some C code. I didn't have the exact same components but he confirmed my suspicions and put me on to the path of success.

A bit of hacking and voilà! You now have a Teletype that can send and receive from a modern PC, connect to the internet, and participate in all manner of shenanigans. 

So yes, connecting the Teletype to my PC was more involved than I thought it would be. 

BUT MORE IMPORTANTLY:
Working up close with this machine has really made me appreciate the long chain of theory, mechanical engineering, electrical engineering, and computing ideas that built on one another to get us to where we are today.
And where we are today seems far from the teletype: a device with one foot in the modern computing era and the other in the clockwork era. News flash: The Teletype was still in use well into the 1970s. The journey has been long, and it continues still, working its way down to the nanoscale.
Fascinating and wonderful.
