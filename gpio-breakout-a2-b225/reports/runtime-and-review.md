# A2 runtime and review record

The native board was migrated from A1 into this separate revision, then routed
and checked without editing PCB or schematic S-expressions. KiCad GUI Page
Settings supplied the schematic title/date and power/USB scope comments.

The existing carrier Python environment had mismatched schematic wrappers and
protobufs (missing BusEntryType). Its older parity API server did not open this
schematic. The Sept5 server with the then-current temporary b225 bindings also
failed decoding SchematicSymbolInstance. No shared runtime was modified.

An isolated bindings directory was copied from `/private/tmp/b225-kicad-python`
to `/private/tmp/gpio-addon-native-api`, then its generated protobuf modules
were rebuilt from `/private/tmp/b225-native-proto/api/proto` using the existing
`/private/tmp/b225-protoc/bin/protoc` and b225-api-venv's generator tools. The
new Homebrew protoc was incompatible with the older Python protobuf runtime,
so that failed attempt was replaced by the existing matching protoc.

The successful environment used:

- Python: `/private/tmp/b225-api-venv/bin/python`.
- PYTHONPATH: `/private/tmp/gpio-addon-native-api`.
- DYLD_FRAMEWORK_PATH: `/opt/homebrew/opt/python@3.14/Frameworks`.
- DYLD_LIBRARY_PATH: `/private/tmp/b22451-pinned-runtime`.
- PCB CLI: the existing `tools/kicad11-b2231-parity/KiCad.app` bundle.
- Schematic CLI: the existing `tools/kicad11-nightly-20260905/KiCad/KiCad.app` bundle.

Those are session paths, not a portable installation recipe. The final editable
KiCad files, local connector libraries and reports are the deliverables. Use a
matching official native API runtime to reproduce or extend these sources.

The initial route candidates exposed insufficient router clearance, an
underestimated custom solder-jumper shape, and blocked 0.5mm pitch fanout.
Native DRC rejected these attempts. The accepted route uses a reserved widening
fanout and ordinary through vias; remaining connections were closed using the
available via layers. The initial LCD-only A2 DRC had zero findings and zero unconnected
items. The later USB extension results supersede that state; see README and
current drc.json/erc.json. The final source hash is recorded in interface-audit.json.

Top and cable-entry-side images were visually reviewed. The gray rectangular
J1 body is a nominal envelope only. It contains no contact, latch, or aperture
geometry and cannot qualify physical mating. The exact official Samtec page
was inspected on 2026-09-08; its CAD downloads require an email/privacy-consent
submission. No email address was supplied or message sent. The future LCD
endpoint, exact catalog cable assembly and detailed model remain release gates.

Published telemetry contains this run's phase times, failures, script hashes,
and a source/artifact manifest. Unrelated parent-workspace inventory and its
private repository details are omitted from the public addon repository.


## USB input extension

The USB extension used the same isolated native IPC runtime and explicit
telemetry run 20260908T231349-8d8dcf94. It adds a protected upstream USB-C
input while preserving original LCD pad geometry and copper. Native netlist
import duplicated three custom footprints; restoring the original native
footprints and comparing every original footprint/copper item caught and
removed that regression. Symbol body graphics were also registered in local
coordinates after native schematic visual review exposed displaced graphics;
all electrical pin positions and IDs were preserved. Raw failed DRC/ERC
reports and revision scripts are retained as evidence, not accepted results.

The native GUI applied one narrow, commented ERC exclusion: the datasheet's
unused LM66100 ST-to-ground connection versus the existing GND power flag.
No global electrical rule or copper clearance was relaxed. Standard USB
protection body models were attached explicitly after checking that the
netlist import had omitted them. J3 uses the independently checked official
Molex model; J1 remains an explicitly unqualified nominal envelope.

Native physical stackup editing remains blocked. The saved generic dielectric
stack is not the selected JLC04161H-7628 process reference. Native IPC has no
implemented setter; GUI selection could not isolate this addon from another
unsaved design. That other design was not changed. Native launcher process
lifetimes overlap some separately recorded GUI action/selection phases; the
measured phase total is aggregated elapsed time, not exclusive runtime or CPU
time. Failed attempts remain visible in the telemetry.
