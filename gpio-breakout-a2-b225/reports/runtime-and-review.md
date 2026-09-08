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
available via layers. The final DRC has zero findings and zero unconnected
items. The final source hash is recorded in interface-audit.json.

Top and cable-entry-side images were visually reviewed. The gray rectangular
J1 body is a nominal envelope only. It contains no contact, latch, or aperture
geometry and cannot qualify physical mating. The exact official Samtec page
was inspected on 2026-09-08; its CAD downloads require an email/privacy-consent
submission. No email address was supplied or message sent. The future LCD
endpoint, exact catalog cable assembly and detailed model remain release gates.

Published telemetry contains this run's phase times, failures, script hashes,
and a source/artifact manifest. Unrelated parent-workspace inventory and its
private repository details are omitted from the public addon repository.
