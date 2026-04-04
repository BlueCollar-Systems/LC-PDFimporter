# -*- coding: utf-8 -*-
# primitive_extractor.py — PyMuPDF -> normalized Primitives
# BlueCollar Systems — BUILT. NOT BOUGHT.
"""
THE SEAM: converts PyMuPDF page data into host-neutral Primitives.
Rule 1: Parser modules must not know about domain-specific logic.
"""
from __future__ import annotations
import math
import re
from typing import List, Tuple

from .primitives import (
    Primitive, NormalizedText, PageData, next_id
)

MM_PER_PT = 25.4 / 72.0


def _xy(obj) -> Tuple[float, float]:
    if hasattr(obj, "x") and hasattr(obj, "y"):
        return float(obj.x), float(obj.y)
    if isinstance(obj, (tuple, list)) and len(obj) >= 2:
        return float(obj[0]), float(obj[1])
    return 0.0, 0.0


def _norm_color(col) -> Tuple[float, float, float]:
    if col is None:
        return (0.0, 0.0, 0.0)
    try:
        if isinstance(col, (int, float)):
            g = max(0.0, min(1.0, float(col)))
            return (g, g, g)
        vals = [max(0.0, min(1.0, float(c))) for c in col]
        if len(vals) >= 4:
            c, m, y, k = vals[0], vals[1], vals[2], vals[3]
            r = (1.0 - c) * (1.0 - k)
            g = (1.0 - m) * (1.0 - k)
            b = (1.0 - y) * (1.0 - k)
            return (
                max(0.0, min(1.0, r)),
                max(0.0, min(1.0, g)),
                max(0.0, min(1.0, b)),
            )
        while len(vals) < 3:
            vals.append(vals[-1] if vals else 0.0)
        return (vals[0], vals[1], vals[2])
    except (TypeError, ValueError, AttributeError):
        return (0.0, 0.0, 0.0)


def _parse_dashes(raw) -> list | None:
    """Parse PyMuPDF dash patterns into a numeric list.

    PyMuPDF returns dashes as strings like ``'[ 6 6 ] 0'`` (array + phase)
    or as actual lists/tuples.  Returns ``None`` for solid lines.
    """
    if raw is None:
        return None
    if isinstance(raw, str):
        s = raw.strip()
        if not s or s.startswith("[]") or s == "() 0":
            return None
        # Extract numbers between brackets: "[ 6 6 ] 0" -> [6.0, 6.0]
        bracket = s.find("[")
        bracket_end = s.find("]")
        if bracket >= 0 and bracket_end > bracket:
            inner = s[bracket + 1:bracket_end].strip()
            if not inner:
                return None
            try:
                nums = [float(x) for x in inner.split()]
                return nums if nums else None
            except ValueError:
                return None
        return None
    if isinstance(raw, (list, tuple)):
        if not raw:
            return None
        # Could be ([6,6], 0) tuple or flat [6,6]
        if len(raw) == 2 and isinstance(raw[0], (list, tuple)):
            return list(raw[0]) if raw[0] else None
        try:
            nums = [float(x) for x in raw]
            return nums if nums else None
        except (TypeError, ValueError):
            return None
    return None


def extract_page(page, page_num: int, scale: float = 1.0,
                 flip_y: bool = True) -> PageData:
    """Extract normalized primitives from a PyMuPDF page."""
    page_h = page.rect.height
    page_w_mm = page.rect.width * MM_PER_PT * scale
    page_h_mm = page.rect.height * MM_PER_PT * scale

    primitives = []
    drawings = page.get_drawings()

    for path_group in drawings:
        items = path_group.get("items", [])
        if not items:
            continue

        stroke = _norm_color(path_group.get("color") or path_group.get("stroke"))
        fill = _norm_color(path_group.get("fill"))
        width = path_group.get("width")
        dashes = _parse_dashes(path_group.get("dashes"))
        close_path = path_group.get("closePath", False)
        layer_name = path_group.get("oc") or path_group.get("layer")

        current_pts: List[Tuple[float, float]] = []
        sub_paths: List[Tuple[List[Tuple[float, float]], bool]] = []

        def flush(closed: bool, _sub_paths=sub_paths):
            nonlocal current_pts
            if len(current_pts) >= 2:
                _sub_paths.append((current_pts[:], closed))
            current_pts = []

        for item in items:
            kind = item[0]
            data = item[1:]

            if kind == "m":
                flush(False)
                x, y = _parse_point(data)
                px, py = _to_mm(x, y, page_h, flip_y, scale)
                current_pts = [(px, py)]

            elif kind == "l":
                if len(data) >= 2 and hasattr(data[0], "x") and hasattr(data[1], "x"):
                    x0, y0 = _xy(data[0])
                    x1, y1 = _xy(data[1])
                    p0 = _to_mm(x0, y0, page_h, flip_y, scale)
                    p1 = _to_mm(x1, y1, page_h, flip_y, scale)
                    if not current_pts:
                        current_pts.append(p0)
                    current_pts.append(p1)
                else:
                    x, y = _parse_point(data)
                    current_pts.append(_to_mm(x, y, page_h, flip_y, scale))

            elif kind == "c":
                if len(data) == 4 and all(hasattr(d, "x") for d in data):
                    pts = [_xy(d) for d in data]
                else:
                    pts = _parse_cubic(data)
                p0 = _to_mm(pts[0][0], pts[0][1], page_h, flip_y, scale)
                p1 = _to_mm(pts[1][0], pts[1][1], page_h, flip_y, scale)
                p2 = _to_mm(pts[2][0], pts[2][1], page_h, flip_y, scale)
                p3 = _to_mm(pts[3][0] if len(pts) > 3 else pts[2][0],
                            pts[3][1] if len(pts) > 3 else pts[2][1],
                            page_h, flip_y, scale)
                if not current_pts:
                    current_pts.append(p0)
                N = max(4, min(32, int(math.ceil(_dist(p0, p3) / 0.5))))
                for i in range(1, N + 1):
                    t = i / float(N)
                    q = _bezier_pt(p0, p1, p2, p3, t)
                    current_pts.append(q)

            elif kind == "re":
                flush(False)
                x, y, w, h = _parse_rect(data)
                c1 = _to_mm(x, y, page_h, flip_y, scale)
                c2 = _to_mm(x + w, y, page_h, flip_y, scale)
                c3 = _to_mm(x + w, y + h, page_h, flip_y, scale)
                c4 = _to_mm(x, y + h, page_h, flip_y, scale)
                sub_paths.append(([c1, c2, c3, c4, c1], True))

            elif kind == "h":
                flush(True)

            elif kind == "v":
                if len(data) >= 2:
                    cx, cy = _xy(data[0])
                    ex, ey = _xy(data[1])
                    ctrl = _to_mm(cx, cy, page_h, flip_y, scale)
                    end = _to_mm(ex, ey, page_h, flip_y, scale)
                    if current_pts:
                        p0 = current_pts[-1]
                        cp1 = (p0[0] + 2/3*(ctrl[0]-p0[0]), p0[1] + 2/3*(ctrl[1]-p0[1]))
                        cp2 = (end[0] + 2/3*(ctrl[0]-end[0]), end[1] + 2/3*(ctrl[1]-end[1]))
                        N = 8
                        for i in range(1, N + 1):
                            t = i / float(N)
                            current_pts.append(_bezier_pt(p0, cp1, cp2, end, t))

        flush(close_path)

        for pts, is_closed in sub_paths:
            if len(pts) < 2:
                continue
            cleaned = [pts[0]]
            for p in pts[1:]:
                if _dist(p, cleaned[-1]) > 0.01:
                    cleaned.append(p)
            if len(cleaned) < 2:
                continue

            xs = [p[0] for p in cleaned]
            ys = [p[1] for p in cleaned]
            bbox = (min(xs), min(ys), max(xs), max(ys))

            area = None
            if is_closed and len(cleaned) >= 3:
                area = _polygon_area(cleaned)

            ptype = "line" if len(cleaned) == 2 else ("closed_loop" if is_closed else "polyline")

            primitives.append(Primitive(
                id=next_id(), type=ptype, points=cleaned,
                bbox=bbox, stroke_color=stroke, fill_color=fill,
                dash_pattern=dashes, line_width=width,
                layer_name=layer_name, closed=is_closed,
                area=area, page_number=page_num
            ))

    text_items = _extract_text(page, page_h, page_num, flip_y, scale)

    return PageData(
        page_number=page_num,
        width=page_w_mm, height=page_h_mm,
        primitives=primitives, text_items=text_items,
        layers=[], xobject_names=[]
    )


def _extract_text(page, page_h, page_num, flip_y, scale) -> List[NormalizedText]:
    items = []
    try:
        tdict = page.get_text("dict")
    except (RuntimeError, TypeError, ValueError):
        return items

    for block in tdict.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            spans = line.get("spans", [])
            if not spans:
                continue
            text_dir = line.get("dir", (1.0, 0.0))
            dx = float(text_dir[0]) if text_dir else 1.0
            dy = float(text_dir[1]) if text_dir else 0.0
            angle = -math.degrees(math.atan2(dy, dx))

            # Important: keep each PDF span as its own text item.
            # Some CAD PDFs store a visual "line" as multiple positioned spans;
            # collapsing them into one string at the first-span origin causes
            # alignment drift and label overlap in DXF viewers.
            for span in spans:
                text = str(span.get("text", "")).strip()
                if not text:
                    continue

                origin = span.get("origin")
                if origin and len(origin) >= 2:
                    x, y = float(origin[0]), float(origin[1])
                else:
                    bb = span.get("bbox") or line.get("bbox", (0, 0, 0, 0))
                    # Fallback: use lower-left-ish point from bbox.
                    x, y = float(bb[0]), float(bb[3] if len(bb) >= 4 else bb[1])

                px, py = _to_mm(x, y, page_h, flip_y, scale)
                size = max(float(span.get("size", 3)), 1.0) * MM_PER_PT * scale
                font = str(span.get("font", ""))

                bbox_mm = None
                sb = span.get("bbox")
                if sb and len(sb) >= 4:
                    x0, y0, x1, y1 = map(float, sb[:4])
                    if flip_y:
                        by0 = (page_h - max(y0, y1)) * MM_PER_PT * scale
                        by1 = (page_h - min(y0, y1)) * MM_PER_PT * scale
                    else:
                        by0 = min(y0, y1) * MM_PER_PT * scale
                        by1 = max(y0, y1) * MM_PER_PT * scale
                    bx0 = min(x0, x1) * MM_PER_PT * scale
                    bx1 = max(x0, x1) * MM_PER_PT * scale
                    bbox_mm = (bx0, by0, bx1, by1)

                normalized = text.upper().replace("  ", " ").strip()
                generic_tags = _classify_generic(text)

                items.append(NormalizedText(
                    id=next_id(),
                    text=text,
                    normalized=normalized,
                    insertion=(px, py),
                    bbox=bbox_mm,
                    font_size=size,
                    rotation=angle,
                    font_name=font,
                    page_number=page_num,
                    generic_tags=generic_tags,
                ))
    return items


def _classify_generic(text: str) -> list:
    tags = []
    t = text.strip()
    tu = t.upper()
    if re.search(r"\d+['']\s*[-\u2013]?\s*\d", t) or re.search(r"\d+\s*/\s*\d+", t):
        tags.append("dimension_like")
    if re.search(r'\d+\.?\d*\s*(?:"|mm|cm|in|ft)', t, re.I):
        tags.append("dimension_like")
    if re.search(r"SCALE[:\s]*\d", tu) or re.search(r"\d+\s*:\s*\d+", t):
        tags.append("scale_like")
    if re.search(r"\b(DRAWN|CHECKED|DATE|SCALE|REV|SHEET|PROJECT|DWG|TITLE)\b", tu):
        tags.append("titleblock_like")
    if re.search(r"\u00D8|\bDIA\b|\bRAD\b|\bR\d", t, re.I):
        tags.append("callout_like")
    if re.search(r"\b(DETAIL|SECTION|SEC|VIEW|ELEVATION)\s+[A-Z]", tu):
        tags.append("detail_reference")
    if len(t) > 1 and len(t) < 60 and re.search(r"[A-Z]{2,}", tu):
        tags.append("label_like")
    return tags


# ── Coordinate helpers ──

def _to_mm(x, y, page_h, flip_y, scale):
    if flip_y:
        y = page_h - y
    return x * MM_PER_PT * scale, y * MM_PER_PT * scale


def _parse_point(data):
    if len(data) >= 1 and hasattr(data[0], "x"):
        return _xy(data[0])
    if len(data) >= 2:
        return float(data[0]), float(data[1])
    return 0.0, 0.0


def _parse_cubic(data):
    if len(data) == 3 and all(hasattr(d, "x") for d in data):
        return [_xy(d) for d in data]
    if len(data) >= 6:
        return [(float(data[0]), float(data[1])),
                (float(data[2]), float(data[3])),
                (float(data[4]), float(data[5]))]
    if len(data) == 4:
        return [_xy(d) for d in data]
    return [(0, 0), (0, 0), (0, 0)]


def _parse_rect(data):
    if len(data) >= 1 and hasattr(data[0], "x0"):
        r = data[0]
        return float(r.x0), float(r.y0), float(r.x1) - float(r.x0), float(r.y1) - float(r.y0)
    if len(data) >= 4:
        return float(data[0]), float(data[1]), float(data[2]), float(data[3])
    return 0.0, 0.0, 0.0, 0.0


def _bezier_pt(p0, p1, p2, p3, t):
    u = 1.0 - t
    return (u**3*p0[0] + 3*u**2*t*p1[0] + 3*u*t**2*p2[0] + t**3*p3[0],
            u**3*p0[1] + 3*u**2*t*p1[1] + 3*u*t**2*p2[1] + t**3*p3[1])


def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _polygon_area(pts):
    n = len(pts)
    a = 0.0
    for i in range(n):
        j = (i + 1) % n
        a += pts[i][0] * pts[j][1] - pts[j][0] * pts[i][1]
    return abs(a) / 2.0
