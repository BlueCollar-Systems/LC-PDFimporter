"""Preset-driven import orchestration for LibreCAD PDF importer."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .core.PDFImportConfig import ImportConfig
from .core.document import DocumentExtraction, ExtractionOptions, extract_document


@dataclass
class ImportRun:
    extraction: DocumentExtraction
    config: ImportConfig


def _preset_config(name: str) -> ImportConfig:
    key = (name or "general").strip().lower()
    if key in {"fast", "preview"}:
        return ImportConfig.fast()
    if key in {"max", "max_fidelity", "fidelity"}:
        return ImportConfig.max_fidelity()
    if key in {"shop", "shop_drawing", "full"}:
        return ImportConfig.full()
    if key in {"technical", "tech"}:
        cfg = ImportConfig.full()
        cfg.cleanup_level = "aggressive"
        cfg.arc_mode = "rebuild"
        cfg.text_mode = "labels"
        return cfg
    if key in {"general", "default"}:
        cfg = ImportConfig()
        cfg.text_mode = "labels"
        return cfg
    return ImportConfig()


def _preset_runtime_tuning(name: str) -> Dict[str, Any]:
    key = (name or "general").strip().lower()
    if key in {"fast", "preview"}:
        return {"min_segment_mm": 0.40, "max_text_items_per_page": 0}
    if key in {"technical", "tech"}:
        return {"min_segment_mm": 0.02, "max_text_items_per_page": 1500}
    if key in {"shop", "shop_drawing", "full"}:
        return {"min_segment_mm": 0.02, "max_text_items_per_page": 2500}
    if key in {"max", "max_fidelity", "fidelity"}:
        return {"min_segment_mm": 0.0, "max_text_items_per_page": None}
    return {"min_segment_mm": 0.05, "max_text_items_per_page": 4000}


def run_import(pdf_path: str, preset: str = "general",
               overrides: Optional[Dict[str, Any]] = None) -> ImportRun:
    cfg = _preset_config(preset)
    tuning = _preset_runtime_tuning(preset)
    for key, value in (overrides or {}).items():
        if hasattr(cfg, key):
            setattr(cfg, key, value)
        elif key in {"min_segment_mm", "max_text_items_per_page"}:
            tuning[key] = value

    opts = ExtractionOptions(
        pages=cfg.pages,
        scale=cfg.user_scale,
        flip_y=cfg.flip_y,
        import_text=cfg.import_text and cfg.text_mode != "none",
        import_images=not cfg.ignore_images,
        detect_arcs=cfg.detect_arcs,
        arc_fit_tol_mm=cfg.arc_fit_tol_mm,
        min_segment_mm=float(tuning.get("min_segment_mm", 0.0) or 0.0),
        max_text_items_per_page=tuning.get("max_text_items_per_page"),
    )

    extraction = extract_document(pdf_path, opts)
    return ImportRun(extraction=extraction, config=cfg)


def apply_uniform_scale(extraction: DocumentExtraction, factor: float) -> None:
    if factor <= 0:
        raise ValueError("Scale factor must be positive.")

    for page in extraction.pages:
        data = page.page_data
        data.width *= factor
        data.height *= factor

        for primitive in data.primitives:
            primitive.points = [(x * factor, y * factor) for x, y in (primitive.points or [])]
            if primitive.center:
                primitive.center = (primitive.center[0] * factor, primitive.center[1] * factor)
            if primitive.radius is not None:
                primitive.radius *= factor
            if primitive.bbox:
                x0, y0, x1, y1 = primitive.bbox
                primitive.bbox = (x0 * factor, y0 * factor, x1 * factor, y1 * factor)
            if primitive.line_width is not None:
                primitive.line_width *= factor
            if primitive.area is not None:
                primitive.area *= factor * factor

        for txt in data.text_items:
            tx, ty = txt.insertion
            txt.insertion = (tx * factor, ty * factor)
            if txt.bbox:
                x0, y0, x1, y1 = txt.bbox
                txt.bbox = (x0 * factor, y0 * factor, x1 * factor, y1 * factor)
            txt.font_size *= factor

        for image in page.images:
            image.x_mm *= factor
            image.y_mm *= factor
            image.width_mm *= factor
            image.height_mm *= factor
