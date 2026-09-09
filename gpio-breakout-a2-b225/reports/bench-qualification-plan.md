# GPIO A2 bench qualification after the circuit corrections

This is a test procedure, not a record of completed hardware measurements.
Scope remains low-power USB2 bench use. Downstream USB-A load capacity is not
increased by the startup switch or the 0.5 A PTC.

## Bring-up and power

1. With the LCD and USB loads disconnected, confirm the fitted parts and both
   default-open LCD supply links JP4/JP5. Establish a common ground and verify
   the selected power arrangement does not connect two active LCD supplies.
2. Observe upstream VBUS, U4 output (`USB_VBUS_SOFT`), and the peer's USB rail
   simultaneously during cold plug-in. Capture input current with a current
   probe or calibrated shunt. Repeat in both USB-C plug orientations.
3. U4 TPS22918 precedes the existing LM66100 reverse blocker. Its 10 nF CT
   capacitor targets a typical 26.55 ms 10–90% output rise at 5 V per TI's
   datasheet. For 120.2 uF nominal peer capacitance this corresponds to about
   18.1 mA average capacitor charging current during that interval, before
   operating load. This is a typical calculation, not a guaranteed peak limit.
4. Verify startup, reset, disconnect, rapid reconnect and an externally powered
   peer. Check host voltage droop, reverse leakage, peer undervoltage and the
   downstream rail decay. QOD is deliberately unconnected. The load switch
   does not enforce USB enumeration current limits; the PTC is not a precision
   current limiter.
5. Log settled upstream/peer voltage and input current at idle and during the
   actual bench workload. Do not infer a supported 500 mA load from the fuse's
   hold-current marking. Record ambient and F2/U1/U4 temperatures.

## USB2

Use the intended Pi host and catalog cables. Confirm high-speed enumeration,
then run repeated transfers through the hub and keyboard activity in both
Type-C orientations. Record USB speed, transfer errors, disconnects and host
logs. Inspect the full assembled channel with appropriate USB measurement
fixtures if a compliance claim is required. A board DRC pass is not an eye test.

## Display

RN1–RN6 provide one isolated series element for each of GPIO0–GPIO21 (GPIO0/1
are named ID_SD/ID_SC). Two unused elements remain unconnected. The initial
0 ohm population preserves the existing electrical interface while providing
source-side tuning; it is not a claim of impedance matching.

Confirm the Pi model, GPIO drive configuration, LCD identity and actual pixel
clock before selecting nonzero values. Existing project context suggests an
83.6 MHz RGB666 1600x768 mode, but it has not been confirmed for this new setup.
Capture clock/data at the receiving device, check its setup/hold requirements,
and compare 22/33/47 ohm source populations as needed. Reconcile the existing
receiver-side 47 ohm arrays on C1; do not assume two resistor banks constitute
correct source termination. Run stable patterns and the intended workload.

## Catalog cable and mechanical check

Both J1 and C1 J401 specify Samtec ZF5S-40-01-T-WT-K-TR. Samtec lists FJH as the
mating family; FJH-40-R-03.00-4 is the existing 76.2 mm catalog candidate. Verify
contact faces, pin-one alignment, usable length and latch/fold access in the
actual bench arrangement. Use the manufacturer drawings, not the nominal 3D
envelope, to assess the connector. Cable continuity is a TODO after the cable
choice, not the sole fabrication blocker. No custom or repinned cable is
permitted.

Record equipment, exact host/cable/peer revisions, captures and pass/fail values.
Do not fill this checklist with inferred or simulated measurements.

References: [TI TPS22918](https://www.ti.com/lit/ds/symlink/tps22918.pdf),
[Samtec connector](https://www.samtec.com/products/zf5s-40-01-t-wt-k-tr),
[Samtec catalog cable](https://www.samtec.com/products/fjh-40-r-03.00-4).
