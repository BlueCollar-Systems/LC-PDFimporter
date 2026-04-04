# -*- coding: utf-8 -*-
# hatch_detector.py — Detect hatching patterns in PyMuPDF drawing groups
# BlueCollar Systems — BUILT. NOT BOUGHT.
"""
Hatching = dense clusters of parallel lines at regular spacing.
Modes: "import" (default), "skip" (remove), "group" (separate hidden group)
"""
from __future__ import annotations

import math
from typing import List, Optional, Set, Tuple

MIN_HATCH_LINES = 6
ANGLE_TOL_DEG = 3.0
SPACING_REGULARITY = 0.35
LENGTH_CV_MAX = 0.50


def _parse_line_segment(item_data) -> Optional[Tuple[float, float, float, float]]:
    if len(item_data) >= 2:
        p0, p1 = item_data[0], item_data[1]
        if hasattr(p0, 'x') and hasattr(p1, 'x'):
            return (p0.x, p0.y, p1.x, p1.y)
    return None


def _angle_diff(a: float, b: float) -> float:
    d = abs(a - b)
    if d > 90.0:
        d = 180.0 - d
    return d


def detect(drawings: List[dict]) -> Set[int]:
    """Detect hatch patterns. Returns set of drawing-group indices."""
    if not drawings or len(drawings) < MIN_HATCH_LINES:
        return set()

    lines: List[dict] = []
    for idx, pg in enumerate(drawings):
        items = pg.get("items", [])
        if len(items) < 1:
            continue
        segs = []
        cur = None
        for item in items:
            kind = item[0]
            data = item[1:]
            if kind == "m":
                pt = data[0] if data else None
                if pt and hasattr(pt, 'x'):
                    cur = (pt.x, pt.y)
            elif kind == "l" and cur is not None:
                parsed = _parse_line_segment(data)
                if parsed:
                    segs.append(parsed)
                else:
                    pt = data[0] if data else None
                    if pt and hasattr(pt, 'x'):
                        segs.append((cur[0], cur[1], pt.x, pt.y))
                        cur = (pt.x, pt.y)
            elif kind == "c":
                break
        if len(segs) == 1:
            x0, y0, x1, y1 = segs[0]
            dx, dy = x1 - x0, y1 - y0
            length = math.hypot(dx, dy)
            if length < 0.5:
                continue
            angle = math.degrees(math.atan2(dy, dx))
            if angle < 0:
                angle += 180.0
            mx, my = (x0 + x1) / 2.0, (y0 + y1) / 2.0
            lines.append({"idx": idx, "angle": angle, "len": length, "mx": mx, "my": my})

    if len(lines) < MIN_HATCH_LINES:
        return set()

    hatch_indices: Set[int] = set()
    used = [False] * len(lines)

    for i, line in enumerate(lines):
        if used[i]:
            continue
        group = [line]
        used[i] = True
        for j, other in enumerate(lines):
            if j <= i or used[j]:
                continue
            if _angle_diff(line["angle"], other["angle"]) < ANGLE_TOL_DEG:
                group.append(other)
                used[j] = True
        if len(group) < MIN_HATCH_LINES:
            continue

        ref_rad = math.radians(group[0]["angle"])
        perp_x = -math.sin(ref_rad)
        perp_y = math.cos(ref_rad)
        projections = sorted(
            [{"proj": l["mx"] * perp_x + l["my"] * perp_y, "line": l} for l in group],
            key=lambda p: p["proj"]
        )
        spacings = []
        for k in range(1, len(projections)):
            spacings.append(abs(projections[k]["proj"] - projections[k-1]["proj"]))
        if not spacings:
            continue
        mean_sp = sum(spacings) / len(spacings)
        if mean_sp < 0.3:
            continue
        variance = sum((s - mean_sp) ** 2 for s in spacings) / len(spacings)
        std_dev = math.sqrt(variance)
        if mean_sp > 0 and (std_dev / mean_sp) < SPACING_REGULARITY:
            lengths = [l["len"] for l in group]
            mean_len = sum(lengths) / len(lengths)
            len_var = sum((v - mean_len) ** 2 for v in lengths) / len(lengths)
            len_cv = math.sqrt(len_var) / mean_len if mean_len > 0 else 1.0
            if len_cv < LENGTH_CV_MAX:
                for l in group:
                    hatch_indices.add(l["idx"])

    return hatch_indices
