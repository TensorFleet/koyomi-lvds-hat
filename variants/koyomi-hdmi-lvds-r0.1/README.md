# Project Koyomi - HDMI-LVDS adapter

## TensorFleet r0.1 provenance and status

This directory is an engineering import of
[`exentio/koyomi-hdmi-lvds`](https://github.com/exentio/koyomi-hdmi-lvds) at
commit `7faa32d`. It is retained as the HDMI-input reference for the
TensorFleet Koyomi family. The source remains covered by the included
CERN-OHL-S-2.0 license.

This revision is **not fabrication-approved**. Upstream explicitly describes
the circuit as untested, and TensorFleet has not yet independently closed its
ERC, DRC, source-parity, BOM, placement, or HDMI signal-integrity gates. No
Gerbers, assembly files, or JLCPCB upload may be generated from this folder
until those gates are recorded here.

The GPIO/DPI and HDMI/TFP401 inputs must never drive the SN75LVDS83B input bus
at the same time. The production option will be implemented as mutually
exclusive variants or with explicit isolation/stuffing links; it will not
simply connect both sources in parallel.

This is part of the development of Project Koyomi, read [this blog post](https://blog.exentio.sexy/2023/12/11/project-koyomi-planning.html)
for more.  
The purpose of this adapter is to test and play around with the display of the
Vaio P before further development of the motherboard and to be used in
hand-wired builds.  

**⚠️ WARNING: at the moment of writing, the board hasn't been tested.**  

The board uses Texas Instruments' SN75LVDS83B LVDS transmitter and TFP401 DVI
receiver to send video out to the display.  

The display connector is made by I-PEX, and the model numbers are
`20374-030E-31`/`20374-R30E-31`, they're the same but the 0 variant seems to be
more common.  
The display, in my case a LT080EE04100 by Toshiba (it should be the same for
all Vaio Ps), has no backlight driver, and for that the backlight pins are
broken out, allowing testing of different drivers.  

Reference timings from [this post on patters' blog](https://pcloadletter.co.uk/2012/07/06/iemgd-for-vaio-p/),
huge thank you!  

Pixel clock in Hz: `83600000`  
Horizontal active pixels: `1600`  
Horizontal front porch: `32`  
Horizontal sync time: `65`  
Horizontal back porch: `97`  
Horizontal blank time (HFP+HST+HBP): `194`  
Vertical active pixels: `768`  
Vertical front porch: `1`  
Vertical sync time: `1`  
Vertical back porch: `8`  
Vertical blank time (VFP+VST+VBP): `10`  

---

Huge thanks to Arya ([@CRImier](https://github.com/CRImier)) for her help during most phases of the design!
