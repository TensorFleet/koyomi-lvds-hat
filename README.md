# Project Koyomi - display testing hat

This is the first part of the development of Project Koyomi, read [this blog post](https://blog.exentio.sexy/2023/12/11/project-koyomi-planning.html)
for more.  
The purpose of this Raspberry Pi hat is to test and play around with the
display of the Vaio P before further development of the motherboard.  

The board is currently tested and working [as shown here](https://blog.exentio.sexy/2024/05/09/project-koyomi-update-3.html)!

The board uses Texas Instruments' SN75LVDS83B LVDS transmitter using the Pi's
DPI signals to send video out to the display. The final motherboard will use a
DVI receiver to free up the Raspberry's GPIO, a small converter board is in
development and [you can find it here](https://github.com/exentio/koyomi-hdmi-lvds).  

The display connector is made by I-PEX, and the model numbers are
`20374-030E-31`/`20374-R30E-31`, they're the same but the 0 variant seems to be
more common.  
The display, in my case a LT080EE04100 by Toshiba (it should be the same for
all Vaio Ps), has no backlight driver, and for that the backlight pins are
broken out, allowing testing of different drivers.  
The driver will be controlled using software I2C since all the hardware I2C
pins are already used by DPI. The assigned GPIOs are 23 for SDA and 24 for SCL.
More info about software I2C on [this page](https://learn.adafruit.com/raspberry-pi-i2c-clock-stretching-fixes/software-i2c).

The current settings used in `config.txt` (on top of the default) is:  
```
dtparam=i2c_arm=off
dtparam=spi=off
display_auto_detect=0
dtoverlay=vc4-kms-dpi-generic
dtparam=hactive=1600,hfp=32,hsync=65,hbp=97
dtparam=vactive=768,vfp=1,vsync=1,vbp=8
dtparam=width-mm=182,height-mm=87
dtparam=clock-frequency=83600000,rgb666
framebuffer_width=1600
framebuffer_height=768
dtoverlay=i2c-gpio,i2c_gpio_sda=23,i2c_gpio_scl=24
disable_overscan=1
```
---

Huge thanks to Arya ([@CRImier](https://github.com/CRImier)) for her help during most phases of the design!

---

## Note on this copy (TensorFleet)

This is a **modified copy** of [exentio/koyomi-lvds-hat](https://github.com/exentio/koyomi-lvds-hat),
redistributed under CERN-OHL-S-2.0. It exists because GitHub would not let us fork the upstream
repository (`403: You can't fork this repository at this time`), so we could not open a pull request.

**Modification made** (CERN-OHL-S-2.0 §3.3 requires modifications to be identified):

- `Add F.Mask to DLP2ADN121HL4L pads so FL1/FL2 are solderable` — the
  `Murata_DLP2ADN121HL4L` footprint declared its pads as `(layers "F.Cu" "F.Paste")` with no
  `"F.Mask"`, so no solder mask openings were generated for FL1/FL2 and all 16 pads were covered by
  solder mask. Fixed in the library footprint and in both placed instances. Exporting the F.Mask layer
  before and after gives 197 → 213 flashes: exactly 16 new openings, all at the FL1/FL2 pad
  coordinates, nothing else changed.

  Found when JLCPCB flagged it during production-file preparation for a batch of these boards. Note
  that KiCad's DRC does **not** check for missing solder mask openings, so this passes a clean DRC.

Everything else is unmodified upstream work by Exentio. `gerbers/` is upstream's snapshot and has
**not** been regenerated, so it still reflects the pre-fix state — regenerate from source before
fabricating.

Upstream author: if you're reading this, the fix is a two-line change and we'd happily send it as a PR
if forking becomes possible. Thanks for publishing the design.

## TensorFleet development variants

This repository is the authoritative home for TensorFleet changes to the Koyomi LCD controller.
The VAIO P system repository may contain research notes and historical fabrication snapshots, but
new KiCad source revisions, release packages, renders, and component decisions belong here.

- `variants/koyomi-lvds-hat-ffc-r1.2/` replaces the Raspberry Pi 2x20 header with the exact
  Hirose FH41-40S-0.5SH(05) / JLCPCB C596805 flex connector used by the compact CM5 carrier.
- `variants/koyomi-hdmi-lvds-r0.1/` is the imported Exentio HDMI/TFP401 reference at commit
  `7faa32d`. It is intentionally fabrication-blocked because upstream labels it untested.
- The planned selectable-input revision will isolate the GPIO/DPI and HDMI/TFP401 sources with
  mutually exclusive stuffing options. The two buses must never be wired as parallel drivers.
- The flex contract is straight-through: contact `n` maps to Raspberry Pi physical pin `n` for
  contacts 1 through 40. Cable continuity must therefore verify 1-to-1 and 40-to-40.
- r1.2 is a permanent mechanical/interface floorplan, not a fabrication release. Its tracked DRC
  evidence and verification report keep fabrication blocked until the native four-layer r1.3
  reroute is complete.
