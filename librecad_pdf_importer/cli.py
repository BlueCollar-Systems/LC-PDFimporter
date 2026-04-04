"""CLI for PDF -> DXF conversion tailored to LibreCAD."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .exporters.dxf_exporter import DxfExportOptions, export_to_dxf
from .importer import apply_uniform_scale, run_import
from .launchers.librecad_launcher import launch_librecad


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert PDF vectors into LibreCAD-ready DXF.")
    parser.add_argument("pdf", help="Input PDF path")
    parser.add_argument("--out", help="Output DXF path (default: <pdf>.dxf)")
    parser.add_argument("--preset", default="general",
                        choices=["fast", "general", "technical", "shop", "max"],
                        help="Import preset")
    parser.add_argument("--pages", default=None, help="Page spec: 1,3-5,all")
    parser.add_argument("--scale", type=float, default=None,
                        help="Manual scale multiplier")
    parser.add_argument("--reference-detected-mm", type=float, default=None,
                        help="Measured length in imported geometry (mm)")
    parser.add_argument("--reference-real-mm", type=float, default=None,
                        help="Real-world reference length (mm)")
    parser.add_argument("--no-text", action="store_true", help="Skip text export")
    parser.add_argument("--no-images", action="store_true", help="Skip image export")
    parser.add_argument("--no-arcs", action="store_true", help="Skip arc reconstruction")
    parser.add_argument("--json", help="Write JSON report")
    parser.add_argument("--launch", action="store_true", help="Launch LibreCAD after export")
    parser.add_argument("--librecad-exe", help="Explicit LibreCAD executable path")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    pdf_path = Path(args.pdf).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve() if args.out else pdf_path.with_suffix(".dxf")

    overrides = {}
    if args.pages is not None:
        overrides["pages"] = args.pages
    if args.scale is not None:
        overrides["user_scale"] = args.scale
    if args.no_text:
        overrides["import_text"] = False
        overrides["text_mode"] = "none"
    if args.no_images:
        overrides["ignore_images"] = True
    if args.no_arcs:
        overrides["detect_arcs"] = False

    run = run_import(str(pdf_path), preset=args.preset, overrides=overrides)

    if args.reference_detected_mm and args.reference_real_mm:
        if args.reference_detected_mm <= 0:
            raise SystemExit("--reference-detected-mm must be > 0")
        scale_factor = args.reference_real_mm / args.reference_detected_mm
        apply_uniform_scale(run.extraction, scale_factor)

    export = export_to_dxf(
        run.extraction,
        str(out_path),
        DxfExportOptions(
            include_text=not args.no_text,
            include_images=not args.no_images,
            group_by_page=True,
            prefer_source_layers=True,
            attach_metadata=True,
        ),
    )

    summary = {
        "import": run.extraction.summary(),
        "export": {
            "output_path": export.output_path,
            "entity_count": export.entity_count,
            "layer_count": export.layer_count,
            "image_count": export.image_count,
        },
    }

    print(json.dumps(summary, indent=2))

    if args.json:
        report = Path(args.json).expanduser().resolve()
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"Wrote report: {report}")

    if args.launch:
        ok, message = launch_librecad(export.output_path, executable=args.librecad_exe)
        print(message)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
