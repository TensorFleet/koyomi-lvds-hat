# Koyomi RGB compact R2.4 sideband verification

Date: 2026-08-13

## Defect addressed

R2.3 excluded the legacy J3–J8 connector footprints, but three panel-sideband
nets then had only one production PCB pad each. Schematic ERC did not reveal
that board-level endpoint loss because the excluded DNP symbols still existed
in the schematic.

R2.4 assigns three redundant contacts of the existing 40-contact system FFC:

| Net | System FFC | Panel connector |
| --- | --- | --- |
| `PANEL_ID0` | JFFC1.17 | J2.10 |
| `PANEL_ID1` | JFFC1.34 | J2.21 |
| `LCD_INS` | JFFC1.39 | J2.30 |

One duplicate +3.3 V contact and two ground contacts were repurposed. The FFC
still carries one +3.3 V contact, two +5 V contacts, and six ground contacts.
The displaced +3.3 V contact's former layer-joining function is restored with
a separate local bridge and 0.50/0.25 mm via.

## Production-interface audit

The KiCad IPC audit in `interface-audit.json` passes all eleven relevant nets:

- `PANEL_ID0`, `PANEL_ID1`, and `LCD_INS`: JFFC1 to J2;
- `EN` and `PWM`: JFFC1 to JBL1;
- `VCD1` through `VCD6`: J2 to JBL1;
- no physical J3–J8 footprints are present.

The audit verifies the exact net name on both intended pads and records track
and via counts. Together with KiCad DRC reporting zero unconnected items, this
demonstrates that the named endpoints have continuous routed copper rather
than merely matching schematic labels.

## Fresh KiCad gates

Checks use the repository's bundled KiCad 10.99 nightly dated 2026-07-22.

- PCB DRC, error-only: **0 violations, 0 unconnected items**.
- PCB DRC, all-severity: **13 inherited `lib_footprint_mismatch` warnings**,
  **0 unconnected items**, and no other findings.
- Schematic ERC, error-only: the same **3 inherited
  `power_pin_not_driven` errors** on +5 V, +3.3 V, and GND as R2.3.
- Schematic ERC, all-severity: **85 findings**, exactly matching the R2.3
  category counts: 3 power errors, 61 off-grid warnings, 16 library-copy
  mismatches, 1 unavailable-library warning, and 4 unconnected-pin warnings.
- No exclusions or new waivers were added.

Authoritative outputs are `drc-errors.rpt`, `drc-all.rpt`, `erc-errors.rpt`,
`erc-all.rpt`, `r2.4.net`, and `interface-audit.json` in this directory.

## Compatibility gate

The FFC pinout has changed. A carrier that still ties contact 17 to +3.3 V or
contacts 34/39 to ground is **not compatible** with R2.4 and must not be joined
to it. The matching CM5-carrier revision must assign these contacts to the
three sideband nets before the system cable is installed.

PCB routing is complete and electrically equivalent to the R2.3 gate plus the
three repaired sidebands. Fabrication remains closed on the inherited
schematic power-source decision and on a matching carrier-side pinout.
