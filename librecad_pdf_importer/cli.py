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
                        choices=["fast", "general", "technical", "shop", "raster_vector", "raster_only", "max"],
                        help="Import preset")
    parser.add_argument("--pages", default=None, help="Page spec: 1,3-5,all")
    parser.add_argument("--scale", type=float, default=None,
                        help="Manual scale multiplier")
    parser.add_argument("--mode", default=None,
                        choices=["auto", "vectors", "raster", "hybrid"],
                        help="Force import mode override")
    parser.add_argument("--text-mode", default=None,
                        choices=["labels", "geometry", "none"],
                        help="Text handling override")
    parser.add_argument("--strict-text-fidelity",
                        action=argparse.BooleanOptionalAction,
                        default=None,
                        help="Preserve exact text spans (default from preset)")
    parser.add_argument("--hatch-mode", default=None,
                        choices=["import", "group", "skip"],
                        help="Hatch handling override")
    parser.add_argument("--arc-mode", default=None,
                        choices=["auto", "preserve", "rebuild", "polyline"],
                        help="Arc reconstruction mode")
    parser.add_argument("--cleanup-level", default=None,
                        choices=["conservative", "balanced", "aggressive"],
                        help="Geometry cleanup aggressiveness")
    parser.add_argument("--lineweight-mode", default=None,
                        choices=["ignore", "preserve", "group", "map_to_layers"],
                        help="Lineweight handling mode")
    parser.add_argument("--grouping-mode", default=None,
                        choices=[
                            "single", "per_page", "per_layer", "per_color",
                            "nested_page_layer", "nested_page_lineweight",
                        ],
                        help="Grouping strategy")
    parser.add_argument("--raster-dpi", type=int, default=None,
                        help="Raster rendering DPI for raster/hybrid modes")
    parser.add_argument("--no-raster-fallback", action="store_true",
                        help="Disable automatic raster fallback when vectors are absent")
    parser.add_argument("--dxf-version", default="R2018",
                        choices=["R12", "R2000", "R2004", "R2007", "R2010", "R2013", "R2018"],
                        help="Target DXF version")
    parser.add_argument("--page-arrangement", default="spread",
                        choices=["spread", "compact", "touch", "overlay"],
                        help="Multi-page placement mode (default: spread = 20%% gap)")
    parser.add_argument("--page-gap-ratio", type=float, default=0.02,
                        help="Gap ratio used when --page-arrangement=compact")
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
    if args.mode is not None:
        overrides["import_mode"] = args.mode
    if args.text_mode is not None:
        overrides["text_mode"] = args.text_mode
        overrides["import_text"] = args.text_mode != "none"
    if args.strict_text_fidelity is not None:
        overrides["strict_text_fidelity"] = bool(args.strict_text_fidelity)
    if args.hatch_mode is not None:
        overrides["hatch_mode"] = args.hatch_mode
    if args.arc_mode is not None:
        overrides["arc_mode"] = args.arc_mode
    if args.cleanup_level is not None:
        overrides["cleanup_level"] = args.cleanup_level
    if args.lineweight_mode is not None:
        overrides["lineweight_mode"] = args.lineweight_mode
    if args.grouping_mode is not None:
        overrides["grouping_mode"] = args.grouping_mode
    if args.raster_dpi is not None:
        overrides["raster_dpi"] = args.raster_dpi
    if args.no_raster_fallback:
        overrides["raster_fallback"] = False
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
            include_text=(not args.no_text) and (run.config.text_mode != "geometry"),
            include_images=not args.no_images,
            group_by_page=True,
            prefer_source_layers=True,
            attach_metadata=True,
            dxf_version=args.dxf_version,
            map_dashes=bool(run.config.map_dashes),
            page_arrangement=args.page_arrangement,
            page_gap_ratio=max(0.0, float(args.page_gap_ratio or 0.0)),
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
