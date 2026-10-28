# KiCad schematic (Rev B), Altium-importable

- `f722-2020-fc.kicad_sch`: full schematic, 152 parts, 106 nets, built from KiCad's official libraries plus two custom symbols (`fc.kicad_sym`: AT7456E, TPS7A2033).
- `f722-2020-fc-schematic.pdf`: printable copy.
- **Altium:** File → Import Wizard → KiCad, select the `.kicad_pro`.
- Verified: KiCad's exported netlist matches the intended design on all 422 pin connections; no single-pin nets.

## Rev B changes from the spec (noise review fixes)
- MPU6000: no VLOGIC (pin 8 is /CS); don't solder its exposed pad.
- **FLASH_CS moved PC5 → PC3**: PC5 isn't bonded out on the STM32F722 LQFP64 (PINIO2 dropped).
- Bucks: MAX17572 (60 V, 1 A each, fixed-frequency 1 MHz) — chosen because KiCad/Altium have a verified footprint. 10 V rail is limited to 1 A.
- Gyro LDO TPS7A2033 behind a ferrite π-filter; VDDA and OSD supplies ferrite-filtered.
- OSD 27 MHz crystal added; 47 Ω series resistors on all 8 motor outputs; buzzer flyback diode; LC filters on camera/VTX power.
- Barometer BMP280 (DPS310 out of stock); vertical JST-SH plugs; 0201 passives where voltage allows.

## Not done yet: PCB layout
A placement attempt showed the specified parts don't fit on 26.5 × 26.5 mm with the bottom-side plugs, USB-C, OSD and two bucks. Next step is a layout decision (drop or move the analog OSD, or move plugs to pads) before routing.

`generator/` holds the scripts that produced and checked the schematic (`design.py` is the single source of truth).
