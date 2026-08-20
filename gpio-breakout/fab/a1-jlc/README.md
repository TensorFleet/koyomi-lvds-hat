# gpio-breakout A1 — JLCPCB order package (2026-08-20)

- PCB: 63.5 x 32 mm, 4 layers, min drill 0.30 mm (standard capability, no
  fine-hole surcharge). Gerbers: `gpio-breakout-a1-gerbers.zip`.
- Assembly: TOP side, TWO placed parts only — J1 (FH41 FFC receptacle,
  C596805, extended part) and F1 (0.5 A PTC 1206, C106264; alternate
  C315893). `assembly/bom.csv` + `assembly/positions.csv`.
- NOT placed: J2 (hand-fit 2x20 stacking socket from the bottom face),
  JP1-JP5 (bare solder jumpers; JP4/JP5 factory state = bridged copper,
  JP1-JP3 open), TP1-TP5, H1/H2.
- Order flags: enable "Confirm Production File"; review parts placement
  manually (FFC orientation: opening toward top board edge).
- Cable note (contract remediation): the 40P 0.5 mm FFC purchase is a
  separate decision — shielded per Hirose D31607 preferred; unshielded
  AWM 20624 acceptable bench-only. This package does not order cables.
