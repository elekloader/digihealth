# digiremote: remote keys on an otherwise stock Digitone

`standalone/patch.py` patches digihealth's remote keys and encoder turns,
and nothing else, into a stock Digitone mk1 OS 1.44 file. It is for tests
that need keys and turns from a computer, on firmware that is as close to
stock as remote input allows.

It does not use an elekloader core or any other mod. elekloader is used only
to read the stock file and to pack and verify the output.

```bash
python standalone/patch.py --stock Digitone_and_Digitone_Keys_OS1.44.syx --out RK44.syx
```

The unit shows version RK44. Give `--version` for another 4-character name
and `--elekloader DIR` if elekloader is not importable. The build needs the
m68k cross toolchain, as for digihealth: native, inside WSL on Windows, or a
prefix set in `CROSS`. A manifest goes next to the output (`.syx.json`) with
each site, the layout and the hashes. The same stock file always gives the
same output.

## Read this before flashing

- **It is a test image, not something to leave on a unit you play.** Remote keys
  are always on and there is no switch: any USB MIDI host can press the unit's
  buttons and turn its encoders, which is enough to open menus or save over or
  delete a project.
- **The same channel answers `PEEK`**, which reads any address in the 128 MB of DDR and the
  64 KB SRAM. That is everything the unit holds in memory.
  It is read-only, but it is open to whatever is plugged into the USB port.
- Keys do not answer for about 40 s after a reboot.
- Go back to stock with the stock OS file (RK44 to stock was checked in digiemu's USB
  upgrade and on a unit).

## What it is

- **The same USB channel and client.** `tools/digiusb.py` works unchanged
  (it sees key protocol revision 4, as on a digihealth Digitone 1.44 build):
  HELLO answers `digiremote 1.0` and the uptime, and `keys`, `turn` and `peek`
  work as usual. `stats` answers "unknown command".
- **Remote keys are always on.** There is no SETTINGS row.
- **The desktop Digitone mk1 only.** On a Digitone Keys, the button helper
  refuses keys, as digihealth does.
- **The key and encoder code is digihealth's own** (`remote_keys.c`,
  `core_candidate.c/.s`), unchanged.

## How it differs from digihealth

| | digihealth (on core-dn1) | digiremote |
|---|---|---|
| SETTINGS | SYSTEM INFO row (and the core's own menu) | stock |
| top-bar readout, STATS | yes | no |
| timing in the audio render and the task switch | yes | no |
| once-a-second heap walk | yes | no |
| the core's hooks (UI, MIDI, pages, voices, project data) | yes | no |
| sites | 3 + the core's | 4 |

The four sites are an early start-up call (to copy the code to the mods' RAM
area), the UI's periodic tick (to pace taps, holds and turns), the SysEx
input (for the channel) and the panel's button driver (to merge remote keys
with the panel's). Only the main OS changes. The output is refused unless
every other section, the bootstrap included, is the stock file's byte for
byte.

## Where its code runs

The code is appended to the main OS, and the boot call copies it to
0x47BE0000-0x47C00000 (the device profile's `ddr` area in elekloader's
`digitone_mk1.py`; patch.py reads the area from the profile) and zeroes its RAM there.
Nothing reserves that area from the OS, and the stock OS needs none: its stack
starts at 0x48000000 and runs down, and nothing it does touches that 128 KB. That
comes from two checks recorded in elekloader's Digitone profile, which are what the claim
rests on:

- no instruction operand in the OS's code points between 0x43EB0000 and the stack (the
  highest is 0x4BEA72C8, the uncached view of 0x43EA72C8), and
- in a settled emulator run, no DDR page from 0x43400000 to 0x47C00000 is ever mapped.

Static operands do not see an address the OS computes (a pointer walked past the end of
a buffer, a stack that grows far deeper than the emulator run shows), so this is
evidence, not a proof. On a unit it has run the flash, SETTINGS over remote keys and
FILTER encoder turns; a long session with large samples has not been run. If a
unit ever behaves differently after RK44 than stock does at the same
steps, the first thing to check is that area.

## What still differs from stock

These come from remote input itself:

- The button driver always runs with interrupts masked.
- Remote encoder counts arrive once per UI tick from the UI task, not from
  the panel, so a remote turn is not the same as a hand turn of the same
  counts.
- SysEx messages to device 0x7D on USB are answered. A stock OS ignores them.
- A few instructions run per UI tick and per incoming SysEx message.
- The main OS is packed by elekloader's packer: the same unpacked image, but
  a different layout in flash.
- Taps and holds are timed by the UI tick (30 a second), not by DTIM0. A
  stock OS need not have DTIM0 running, and this patch leaves it alone.

So results that do not go through the button driver or the encoder input
can be compared with stock directly. For results that do, check them with
the same input on the stock image in the emulator.
