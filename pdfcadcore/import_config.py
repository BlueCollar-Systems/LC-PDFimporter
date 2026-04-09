# -*- coding: utf-8 -*-
# import_config.py — Versioned import configuration
# BlueCollar Systems — BUILT. NOT BOUGHT.
"""
Centralised, versioned import configuration for PDF Vector Importers.
Shared across FreeCAD, Blender, and LibreCAD hosts.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, fields
from typing import Any, Dict, List, Optional


# ──────────────────────────────────────────────────────────────────────
# Cleanup presets  (tolerance values in mm)
# ──────────────────────────────────────────────────────────────────────
CLEANUP_PRESETS: Dict[str, Dict[str, float]] = {
    "conservative": {
        "merge_tol": 0.5,
        "collinear_tol": 0.25,
        "min_seg": 0.25,
    },
    "balanced": {
        "merge_tol": 0.1,
        "collinear_tol": 0.05,
        "min_seg": 0.05,
    },
    "aggressive": {
        "merge_tol": 0.01,
        "collinear_tol": 0.005,
        "min_seg": 0.01,
    },
}


@dataclass
class ImportConfig:
    """Versioned import configuration for PDF Vector Importers."""

    VERSION: str = "2.0"

    # ── Core geometry options ────────────────────────────────────────
    pages: Optional[List[int]] = None
    scale_to_mm: bool = True
    user_scale: float = 1.0
    flip_y: bool = True
    join_tol: float = 0.1
    min_seg_len: float = 0.0
    curve_step_mm: float = 0.5
    make_faces: bool = True
    import_text: bool = True
    text_mode: str = "labels"               # "labels" | "geometry" | "none"
    strict_text_fidelity: bool = True
    group_by_color: bool = True
    assign_lineweight: bool = True
    map_dashes: bool = True
    verbose: bool = True
    create_top_group: bool = True
    hatch_to_faces: bool = True
    hatch_mode: str = "import"              # "import" | "skip" | "group"
    ignore_images: bool = False
    raster_fallback: bool = True
    raster_dpi: int = 200
    import_mode: str = "auto"               # "auto" | "vectors" | "raster" | "hybrid"
    max_bezier_segments: int = 128

    # ── Arc reconstruction ───────────────────────────────────────────
    detect_arcs: bool = True
    arc_fit_tol_mm: float = 0.08
    min_arc_angle_deg: float = 5.0
    arc_sampling_pts: int = 7

    # ── Layering ─────────────────────────────────────────────────────
    layer_mode: str = "auto"                # "auto" | "ocg" | "color" | "none"

    # ── Object-count management ──────────────────────────────────────
    compound_batch_size: int = 200
    heavy_page_threshold: int = 3000

    # ── Phase 2 options ──────────────────────────────────────────────
    arc_mode: str = "auto"
    cleanup_level: str = "balanced"
    lineweight_mode: str = "ignore"
    grouping_mode: str = "per_page"

    # ─────────────────────────────────────────────────────────────────
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d.pop("VERSION", None)
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ImportConfig":
        valid_keys = {f.name for f in fields(cls)}
        filtered = {k: v for k, v in d.items() if k in valid_keys}
        return cls(**filtered)

    def get_cleanup_tolerances(self) -> Dict[str, float]:
        return dict(CLEANUP_PRESETS.get(self.cleanup_level,
                                        CLEANUP_PRESETS["balanced"]))

    # ── Named constructors (presets) ─────────────────────────────────
    @classmethod
    def fast(cls) -> "ImportConfig":
        """Fast Preview — speed over fidelity."""
        return cls(
            curve_step_mm=2.0, join_tol=0.5, detect_arcs=False,
            map_dashes=False, make_faces=False, import_text=False,
            text_mode="none", strict_text_fidelity=False,
            hatch_mode="skip", import_mode="auto",
            cleanup_level="conservative", arc_mode="polyline",
            lineweight_mode="ignore", grouping_mode="single",
        )

    @classmethod
    def general_vector(cls) -> "ImportConfig":
        """General Vector — good for most PDFs."""
        return cls(
            curve_step_mm=1.0, join_tol=0.2, detect_arcs=True,
            map_dashes=False, make_faces=False, import_text=True,
            text_mode="labels", strict_text_fidelity=False,
            hatch_mode="skip", import_mode="auto",
            cleanup_level="conservative", arc_mode="auto",
            lineweight_mode="ignore", grouping_mode="per_page",
        )

    @classmethod
    def technical_drawing(cls) -> "ImportConfig":
        """Technical Drawing — engineering drawings."""
        return cls(
            curve_step_mm=0.5, join_tol=0.1, detect_arcs=True,
            map_dashes=True, make_faces=True, import_text=True,
            text_mode="geometry", strict_text_fidelity=True,
            hatch_mode="group", import_mode="auto",
            cleanup_level="balanced", arc_mode="auto",
            lineweight_mode="preserve", grouping_mode="per_page",
        )

    @classmethod
    def shop_drawing(cls) -> "ImportConfig":
        """Shop Drawing — fabrication drawings (default)."""
        return cls(
            curve_step_mm=0.3, join_tol=0.1, detect_arcs=True,
            map_dashes=True, make_faces=True, import_text=True,
            text_mode="geometry", strict_text_fidelity=True,
            hatch_mode="group", import_mode="auto",
            cleanup_level="balanced", arc_mode="auto",
            lineweight_mode="preserve", grouping_mode="per_page",
            arc_fit_tol_mm=0.05,
        )

    @classmethod
    def full(cls) -> "ImportConfig":
        """Full / Shop Drawing preset — balanced quality."""
        return cls.shop_drawing()

    @classmethod
    def max_fidelity(cls) -> "ImportConfig":
        """Max Fidelity — highest accuracy, slower."""
        return cls(
            curve_step_mm=0.2, join_tol=0.05, detect_arcs=True,
            map_dashes=True, make_faces=True, import_text=True,
            text_mode="geometry", strict_text_fidelity=True,
            hatch_mode="import", import_mode="auto",
            cleanup_level="aggressive", arc_mode="rebuild",
            lineweight_mode="preserve", grouping_mode="nested_page_layer",
        )
