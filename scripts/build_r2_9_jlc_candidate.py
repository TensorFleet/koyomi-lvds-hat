#!/usr/bin/env python3
"""Build and fail-closed audit the compact LCD R2.9 JLCPCB candidate."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import zipfile
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "variants/koyomi-lvds-hat-rgb-compact-r2.9-silkscreen-clearance"
BOARD = SOURCE / "koyomi-lvds-hat.kicad_pcb"
SCHEMATIC = SOURCE / "koyomi-lvds-hat.kicad_sch"
PROJECT = SOURCE / "koyomi-lvds-hat.kicad_pro"
TOOL_ROOT = Path("/Users/hyper/projects/tensorfleet/vaio_p_modding/tools")
KICAD_CLI = TOOL_ROOT / (
    "kicad11-nightly-20260816/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
)
KIPY_PYTHON = TOOL_ROOT / "kicad11-nightly-20260722/venv/bin/python3"
INTERCONNECT_GATE = (
    Path("/Users/hyper/projects/tensorfleet/vaio_p_modding")
    / "scripts/check_interconnect_release.py"
)
DESTINATION = ROOT / "fab/r2.9-compact-rgb-production-jlc-c91592"
PREFIX = "koyomi-lvds-rgb-compact-r2.9-jlc"
EXPECTED_REFS = {
    "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8",
    "FL1", "FL2", "IC1", "J2", "JBL1", "JFFC1", "R1", "R2",
    "RN1", "RN2", "RN3", "RN4", "RN5", "RN6", "U1",
}
PARTS = {
    "C1": ("1uF", "C1592"), "C4": ("1uF", "C1592"),
    "C2": ("100nF", "C1591"), "C5": ("100nF", "C1591"),
    "C3": ("10nF", "C1589"), "C6": ("10nF", "C1589"),
    "C7": ("4.7uF", "C1705"), "C8": ("4.7uF", "C1705"),
    "FL1": ("DLP2ADN900HL4L", "C91592"),
    "FL2": ("DLP2ADN900HL4L", "C91592"),
    "IC1": ("SN75LVDS83B", "C35164"),
    "J2": ("I-PEX 20374-R30E-31", "C5311655"),
    "JBL1": ("Hirose FH12-12S-0.5SH(55)", "C88360"),
    "JFFC1": ("Hirose FH41-40S-0.5SH(05)", "C596805"),
    "R1": ("4.7k", "C844791"), "R2": ("4.7k", "C844791"),
    "RN1": ("47 ohm array", "C425204"),
    "RN2": ("47 ohm array", "C425204"),
    "RN3": ("47 ohm array", "C425204"),
    "RN4": ("47 ohm array", "C425204"),
    "RN5": ("47 ohm array", "C425204"),
    "RN6": ("47 ohm array", "C425204"),
    "U1": ("AP2114H-2.5", "C460313"),
}
EXPECTED_DRC = Counter({
    "lib_footprint_mismatch": 14,
    "silk_overlap": 50,
})


def run(*args, capture=False):
    result = subprocess.run(
        [str(item) for item in args], check=True, text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
    )
    return result.stdout or ""


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def make_zip(source, output):
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source.iterdir()):
            archive.write(path, path.name)


def require(path, *patterns):
    text = path.read_text(encoding="utf-8")
    for pattern in patterns:
        if not re.search(pattern, text):
            raise RuntimeError(f"{path.name} failed required pattern: {pattern}")


def load_positions(path):
    with path.open(newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    refs = {row["Ref"] for row in rows}
    if refs != EXPECTED_REFS:
        raise RuntimeError(
            f"unexpected fitted set: missing={sorted(EXPECTED_REFS-refs)}, "
            f"extra={sorted(refs-EXPECTED_REFS)}"
        )
    if {row["Side"] for row in rows} != {"top"}:
        raise RuntimeError("R2.9 must remain single-side assembly")
    return rows


def write_positions(rows, output):
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(("Designator", "Mid X", "Mid Y", "Layer", "Rotation"))
        for row in rows:
            writer.writerow((
                row["Ref"], row["PosX"], row["PosY"], "Top", row["Rot"]
            ))


def write_bom(rows, output):
    groups = defaultdict(list)
    for row in rows:
        comment, code = PARTS[row["Ref"]]
        groups[(comment, row["Package"], code)].append(row["Ref"])
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream, quoting=csv.QUOTE_ALL, lineterminator="\n")
        writer.writerow(("Comment", "Designator", "Footprint", "JLCPCB Part #"))
        for key, refs in sorted(groups.items(), key=lambda item: min(item[1])):
            writer.writerow((key[0], ",".join(sorted(refs)), key[1], key[2]))


def main():
    run("python3", INTERCONNECT_GATE, "--board", "lcd")
    with tempfile.TemporaryDirectory(prefix=".lcd-r29-jlc-", dir=ROOT) as temp:
        work = Path(temp)
        assembly = work / "assembly"
        gerbers = work / "gerbers"
        reports = work / "reports"
        renders = work / "renders"
        mechanical = work / "mechanical"
        for directory in (assembly, gerbers, reports, renders, mechanical):
            directory.mkdir()

        layers = (
            "F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,F.Silkscreen,"
            "B.Silkscreen,F.Mask,B.Mask,Edge.Cuts"
        )
        run(KICAD_CLI, "pcb", "export", "gerbers", "--subtract-soldermask",
            "--layers", layers,
            "-o", gerbers, BOARD)
        run(KICAD_CLI, "pcb", "export", "drill", "--excellon-separate-th",
            "--generate-map", "--map-format", "gerberx2", "--generate-report",
            "--report-path", work / "drill-report.txt", "-o", gerbers, BOARD)
        drill_text = "\n".join(
            path.read_text(encoding="ascii", errors="ignore")
            for path in gerbers.glob("*.drl")
        )
        drills = [float(value) for value in re.findall(r"T\d+C([0-9.]+)", drill_text)]
        if not drills or min(drills) != 0.2:
            raise RuntimeError(f"expected 0.20 mm minimum drill, got {drills}")

        raw = work / "positions-raw.csv"
        run(KICAD_CLI, "pcb", "export", "pos", "--format", "csv", "--units",
            "mm", "--side", "both", "--exclude-dnp", "-o", raw, BOARD)
        rows = load_positions(raw)
        write_positions(rows, assembly / "positions.csv")
        write_bom(rows, assembly / "bom.csv")

        errors_drc = reports / "errors-only-drc.rpt"
        all_drc = reports / "all-severity-drc.rpt"
        errors_erc = reports / "errors-only-erc.rpt"
        all_erc = reports / "all-severity-erc.rpt"
        # The 2026-08-16 nightly aborts after writing a clean report when
        # --exit-code-violations is used. Keep this gate fail-closed by parsing
        # the report below for exact zero-violation and zero-open counts.
        run(KICAD_CLI, "pcb", "drc", "--severity-error", "--severity-exclusions",
            "--format", "report", "-o", errors_drc, BOARD)
        run(KICAD_CLI, "pcb", "drc", "--severity-all", "--severity-exclusions",
            "--format", "report", "-o", all_drc, BOARD)
        run(KICAD_CLI, "sch", "erc", "--severity-error",
            "--format", "report", "-o", errors_erc, SCHEMATIC)
        run(KICAD_CLI, "sch", "erc", "--severity-all", "--format", "report",
            "-o", all_erc, SCHEMATIC)
        require(errors_drc, r"Found 0 DRC violations", r"Found 0 unconnected pads")
        require(errors_erc, r"ERC messages: 0\s+Errors 0\s+Warnings 0")
        if "[excluded]" in errors_drc.read_text(encoding="utf-8"):
            raise RuntimeError("R2.9 contains an error-level DRC exclusion")
        warning_types = Counter(re.findall(
            r"^\[([^]]+)\]", all_drc.read_text(encoding="utf-8"), re.MULTILINE
        ))
        if warning_types != EXPECTED_DRC:
            raise RuntimeError(f"R2.9 all-severity baseline changed: {warning_types}")
        if any(item in warning_types for item in (
            "silk_over_copper", "silk_edge_clearance"
        )):
            raise RuntimeError("R2.9 has fabrication-clipped silkscreen")

        audit = run(
            KIPY_PYTHON, SOURCE / "scripts/audit_interface.py", BOARD,
            "--kicad-cli", KICAD_CLI,
            "--output", reports / "interface-audit.json", capture=True,
        )
        (reports / "interface-audit.txt").write_text(audit, encoding="utf-8")
        if '"result": "PASS"' not in audit:
            raise RuntimeError("R2.9 routed-interface audit failed")

        edge_audit = run(
            KIPY_PYTHON, SOURCE / "scripts/verify_edge_connectors.py", BOARD,
            "--kicad-cli", KICAD_CLI,
            "--record", SOURCE / "edge-connector-orientations.json",
            "--output", reports / "edge-connector-audit.json", capture=True,
        )
        (reports / "edge-connector-audit.txt").write_text(
            edge_audit, encoding="utf-8"
        )
        if '"result": "PASS"' not in edge_audit:
            raise RuntimeError("R2.9 edge-connector placement audit failed")

        render_specs = {
            "top.png": ("--side", "top"),
            "bottom.png": ("--side", "bottom"),
            "side.png": ("--side", "front", "--zoom", "1.12"),
            "perspective.png": (
                "--side", "top", "--perspective", "--rotate", "-24,0,-18",
                "--zoom", "1.05",
            ),
        }
        for filename, options in render_specs.items():
            run(KICAD_CLI, "pcb", "render", "--quality", "high", "--background",
                "opaque", "--floor", "--width", "1800", "--height", "1100",
                *options, "-o", renders / filename, BOARD)
        step_path = mechanical / f"{PREFIX}.step"
        run(KICAD_CLI, "pcb", "export", "step", "--force", "--no-dnp",
            "--subst-models", "-o", step_path, BOARD)
        # OpenCascade emits harmless trailing spaces. Normalize the generated
        # text so the checked-in package remains clean and deterministic.
        step_path.write_text(
            "\n".join(
                line.rstrip()
                for line in step_path.read_text(encoding="utf-8").splitlines()
            ) + "\n",
            encoding="utf-8",
        )

        (reports / "assembly-audit.txt").write_text(
            "fitted placements: 23\n"
            "top placements: 23\n"
            "bottom placements: 0\n"
            "assembly: single-sided Economic PCBA\n"
            "copper stack: four layers\n"
            "minimum via drill: 0.20 mm (fine-hole quote required)\n"
            "silkscreen over solder-mask openings: 0\n"
            "silkscreen clipped by board edge: 0\n"
            "Gerber plot: solder mask subtracted from silkscreen\n"
            "H1-H4 and JP1-JP2: excluded from BOM/CPL\n"
            "J2: C5311655; JBL1: C88360; JFFC1: C596805\n"
            "sourcing: J2 C5311655 stock 0/pre-order min 442; "
            "FL1-FL2 C91592 stock 3874 (checked 2026-08-20)\n"
            "upload: Confirm Production File must be enabled\n",
            encoding="utf-8",
        )
        (reports / "parts-sourcing.txt").write_text(
            "JLCPCB live parts-library check: 2026-08-20\n"
            "J2 C5311655 / I-PEX 20374-R30E-31: stock 0; "
            "pre-order minimum 442\n"
            "FL1,FL2 C91592 / Murata DLP2ADN900HL4L: stock 3874; minimum 1\n"
            "C91592 is the approved same-series 90-ohm substitution previously "
            "fitted on the five-board 2026-07-30 JLCPCB build.\n",
            encoding="utf-8",
        )
        make_zip(gerbers, work / f"{PREFIX}-gerbers.zip")

        if DESTINATION.exists():
            shutil.rmtree(DESTINATION)
        DESTINATION.mkdir(parents=True)
        for directory in (assembly, gerbers, reports, renders, mechanical):
            shutil.copytree(directory, DESTINATION / directory.name)
        shutil.copy2(work / f"{PREFIX}-gerbers.zip", DESTINATION)
        shutil.copy2(work / "drill-report.txt", DESTINATION)
        (DESTINATION / "README.md").write_text(
            "# Compact RGB LCD R2.9 JLCPCB fabrication candidate\n\n"
            "Upload the Gerber ZIP, `assembly/bom.csv`, and "
            "`assembly/positions.csv`. Select **four layers**, 1.6 mm, ENIG, "
            "a **0.20 mm minimum via-hole process**, ordinary tented vias, and "
            "**top-side Economic PCBA**. Enable **Confirm Production File** and "
            "manual parts-placement confirmation.\n\n"
            "The board is electrically gated for fabrication: zero DRC errors, "
            "zero unconnected pads, zero exclusions, zero ERC errors, and the "
            "eleven-net routed-interface audit passes. The all-severity DRC "
            "warnings are retained in the report; none are silkscreen-over-copper "
            "or board-edge clipping violations.\n\n"
            "This is a fabrication-ready prototype, not final system approval. "
            "The mating B2.2 carrier and straight-through 40-contact cable are "
            "required. The external backlight circuit must implement the documented "
            "LCD_INS# pull-up and hardware interlock. Verify live JLC inventory, "
            "especially private-library connector C5311655, before checkout. "
            "The 2026-08-20 live check found C5311655 at stock 0 with a "
            "442-piece pre-order minimum. FL1/FL2 now use the approved "
            "DLP2ADN900HL4L / C91592 substitution, with 3874 pieces in stock. "
            "This same filter was fitted on the previous five-board JLCPCB "
            "batch. The PCB is ready to fabricate; PCBA can proceed once J2 "
            "has arrived in the private parts library.\n",
            encoding="utf-8",
        )
        (DESTINATION / "fabrication-approval.json").write_text(
            json.dumps({
                "revision": "R2.9",
                "approved_for_fabrication": True,
                "purchase_authorized": False,
                "electrical_gate": {
                    "drc_errors": 0,
                    "unconnected_pads": 0,
                    "drc_exclusions": 0,
                    "erc_errors": 0,
                    "interface_audit": "PASS",
                },
                "manufacturing": {
                    "layers": 4,
                    "assembly_sides": ["top"],
                    "minimum_via_hole_mm": 0.20,
                    "via_covering": "tented",
                    "confirm_production_file": True,
                    "confirm_parts_placement": True,
                },
                "external_gates": {
                    "mating_carrier": "B2.2",
                    "live_part_inventory_reviewed": True,
                    "pcba_ready_after_sourcing": True,
                    "zero_stock_parts": {
                        "C5311655": {"method": "pre-order", "minimum": 442},
                    },
                    "approved_filter_substitution": {
                        "designators": ["FL1", "FL2"],
                        "part": "DLP2ADN900HL4L",
                        "jlcpcb_part": "C91592",
                        "stock_checked": 3874,
                        "previous_jlcpcb_build": "2026-07-30 five-board v1.1 batch",
                    },
                    "placement_reviewed": True,
                    "backlight_interlock_on_mating_system": False,
                    "measured_chassis_fit_completed": False,
                },
            }, indent=2) + "\n",
            encoding="utf-8",
        )

        SOURCE_RENDERS = SOURCE / "renders"
        if SOURCE_RENDERS.exists():
            shutil.rmtree(SOURCE_RENDERS)
        shutil.copytree(renders, SOURCE_RENDERS)
        source_reports = SOURCE / "reports"
        source_reports.mkdir(exist_ok=True)
        shutil.copy2(errors_drc, source_reports / "drc-errors.rpt")
        shutil.copy2(errors_erc, source_reports / "erc-errors.rpt")
        # Do not carry working-state reports from the immutable parent into a
        # released revision; only the freshly generated release gates belong
        # alongside the R2.9 source.
        for stale_name in ("drc-routed-working.rpt", "erc-fabrication-prep.rpt"):
            stale = source_reports / stale_name
            if stale.exists():
                stale.unlink()
        files = sorted(
            path for path in DESTINATION.rglob("*")
            if path.is_file() and path.name != "SHA256SUMS"
        )
        with (DESTINATION / "SHA256SUMS").open("w", encoding="utf-8") as output:
            for path in files:
                output.write(f"{sha256(path)}  {path.relative_to(DESTINATION)}\n")
            for path in (BOARD, SCHEMATIC, PROJECT):
                output.write(f"{sha256(path)}  ../../{path.relative_to(ROOT)}\n")
    print(f"R2.9 JLCPCB candidate built at {DESTINATION}")


if __name__ == "__main__":
    main()
