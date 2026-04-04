"""DXF export adapter for LibreCAD workflows."""
from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
from typing import Dict, Optional, Tuple

import ezdxf
from ezdxf.colors import rgb2int
from ezdxf.units import MM
import fitz

from ..core.document import DocumentExtraction


@dataclass
class DxfExportOptions:
    include_text: bool = True
    include_images: bool = True
    group_by_page: bool = True
    prefer_source_layers: bool = True
    attach_metadata: bool = True


@dataclass
class DxfExportResult:
    output_path: str
    entity_count: int
    layer_count: int
    image_count: int


def export_to_dxf(extraction: DocumentExtraction, output_path: str,
                  options: Optional[DxfExportOptions] = None) -> DxfExportResult:
    opts = options or DxfExportOptions()
    doc = ezdxf.new("R2018")
    doc.units = MM
    msp = doc.modelspace()

    entity_count = 0
    image_count = 0
    dash_cache: Dict[str, str] = {}
    image_def_cache: Dict[str, object] = {}

    for page in extraction.pages:
        for primitive in page.page_data.primitives:
            layer = _layer_name(page.page_data.page_number, primitive.layer_name, primitive.stroke_color, opts)
            _ensure_layer(doc, layer, primitive.stroke_color)
            attribs = {"layer": layer}
            _apply_color(attribs, primitive.stroke_color)
            _apply_lineweight(attribs, primitive.line_width)

            ltype = _linetype_from_dash(doc, primitive.dash_pattern, dash_cache)
            if ltype:
                attribs["linetype"] = ltype

            if primitive.type == "line" and primitive.points and len(primitive.points) == 2:
                msp.add_line(primitive.points[0], primitive.points[1], dxfattribs=attribs)
                entity_count += 1
            elif primitive.type == "circle" and primitive.center and primitive.radius:
                msp.add_circle(primitive.center, primitive.radius, dxfattribs=attribs)
                entity_count += 1
            elif primitive.type == "arc" and primitive.center and primitive.radius:
                start = float(primitive.start_angle or 0.0)
                end = float(primitive.end_angle or 0.0)
                if math.isclose(start, end, abs_tol=1e-6):
                    end = (end + 359.999) % 360.0
                msp.add_arc(primitive.center, primitive.radius, start, end, dxfattribs=attribs)
                entity_count += 1
            elif primitive.points and len(primitive.points) >= 2:
                msp.add_lwpolyline(primitive.points, format="xy", close=bool(primitive.closed), dxfattribs=attribs)
                entity_count += 1

        if opts.include_text:
            for text in page.page_data.text_items:
                layer = _layer_name(page.page_data.page_number, "TEXT", None, opts)
                _ensure_layer(doc, layer, None)
                txt = msp.add_text(
                    text.text,
                    dxfattribs={
                        "layer": layer,
                        "height": max(float(text.font_size), 0.1),
                        "rotation": float(text.rotation or 0.0),
                        "insert": (float(text.insertion[0]), float(text.insertion[1])),
                    },
                )
                if opts.attach_metadata:
                    txt.set_xdata("BC_PDF", [
                        (1000, f"text_id={text.id}"),
                        (1000, f"page={text.page_number}"),
                    ])
                entity_count += 1

        if opts.include_images:
            for placement in page.images:
                img_path = Path(placement.path)
                if not img_path.is_file():
                    continue

                image_def = image_def_cache.get(str(img_path))
                if image_def is None:
                    size_px = _image_size_pixels(str(img_path))
                    image_def = doc.add_image_def(
                        filename=str(img_path),
                        size_in_pixel=size_px,
                        name=f"IMG_{len(image_def_cache) + 1}",
                    )
                    image_def_cache[str(img_path)] = image_def

                layer = _layer_name(page.page_data.page_number, "IMAGES", None, opts)
                _ensure_layer(doc, layer, None)
                msp.add_image(
                    image_def,
                    insert=(placement.x_mm, placement.y_mm),
                    size_in_units=(placement.width_mm, placement.height_mm),
                    dxfattribs={"layer": layer},
                )
                entity_count += 1
                image_count += 1

    output = Path(output_path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(str(output))

    return DxfExportResult(
        output_path=str(output),
        entity_count=entity_count,
        layer_count=len(doc.layers),
        image_count=image_count,
    )


def _layer_name(page_number: int, source_layer: Optional[str], stroke_color,
                opts: DxfExportOptions) -> str:
    parts = []
    if opts.group_by_page:
        parts.append(f"P{page_number:03d}")
    if opts.prefer_source_layers and source_layer:
        parts.append(_sanitize_layer(str(source_layer)))
    elif stroke_color is not None:
        parts.append(_color_key(stroke_color))
    return "_".join(parts) if parts else "PDF_IMPORT"


def _sanitize_layer(name: str) -> str:
    out = [ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in name.strip()]
    value = "".join(out).strip("_")
    return value[:120] if value else "Layer"


def _color_key(rgb) -> str:
    r, g, b = (int(max(0, min(255, round(float(c) * 255)))) for c in rgb)
    return f"RGB_{r:03d}_{g:03d}_{b:03d}"


def _ensure_layer(doc: ezdxf.EzDxf, name: str, rgb) -> None:
    if doc.layers.has_entry(name):
        return
    kwargs = {}
    if rgb is not None:
        kwargs["true_color"] = rgb2int(tuple(int(max(0, min(255, round(float(c) * 255)))) for c in rgb))
    doc.layers.new(name=name, dxfattribs=kwargs)


def _apply_color(attribs: dict, rgb) -> None:
    if rgb is None:
        return
    attribs["true_color"] = rgb2int(tuple(int(max(0, min(255, round(float(c) * 255)))) for c in rgb))


def _apply_lineweight(attribs: dict, width_pt) -> None:
    if width_pt is None:
        return
    width_mm = float(width_pt) * (25.4 / 72.0)
    lw = int(max(5, min(211, round(width_mm * 100))))  # hundredths of mm
    attribs["lineweight"] = lw


def _linetype_from_dash(doc: ezdxf.EzDxf, dash_pattern, cache: Dict[str, str]) -> Optional[str]:
    if not dash_pattern:
        return None

    values = _normalize_dash(dash_pattern)
    if len(values) < 2:
        return None

    key = ",".join(f"{v:.2f}" for v in values)
    cached = cache.get(key)
    if cached:
        return cached

    if len(values) % 2 == 1:
        values.append(values[-1])

    mm_vals = [max(0.1, v * (25.4 / 72.0)) for v in values]
    pattern = [sum(mm_vals)]
    for idx, val in enumerate(mm_vals):
        pattern.append(val if idx % 2 == 0 else -val)

    name = f"PDF_DASH_{len(cache) + 1}"
    try:
        doc.linetypes.add(name=name, pattern=pattern, description=f"PDF dash {key}")
    except Exception:
        return None

    cache[key] = name
    return name


def _normalize_dash(dash_pattern) -> list[float]:
    if isinstance(dash_pattern, str):
        vals = []
        token = ""
        for ch in dash_pattern:
            if ch.isdigit() or ch in {".", "-"}:
                token += ch
                continue
            if token:
                try:
                    vals.append(abs(float(token)))
                except ValueError:
                    pass
                token = ""
        if token:
            try:
                vals.append(abs(float(token)))
            except ValueError:
                pass
        return [v for v in vals if v > 0.0]

    if isinstance(dash_pattern, (list, tuple)):
        vals = []
        for item in dash_pattern:
            if isinstance(item, (int, float)):
                vals.append(abs(float(item)))
            elif isinstance(item, (list, tuple)):
                for nested in item:
                    if isinstance(nested, (int, float)):
                        vals.append(abs(float(nested)))
        return [v for v in vals if v > 0.0]

    return []


def _image_size_pixels(path: str) -> Tuple[int, int]:
    try:
        pix = fitz.Pixmap(path)
        return int(max(1, pix.width)), int(max(1, pix.height))
    except Exception:
        return (100, 100)
