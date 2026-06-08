# -*- coding: utf-8 -*-
"""Shared import bounding boxes for autofit and golden bbox gates."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence, Tuple, Union

from .primitives import NormalizedText, PageData, Primitive

DEFAULT_PADDING_FRACTION = 0.02
DEFAULT_MIN_PADDING_MM = 1.0


@dataclass(frozen=True)
class ImportBounds:
    """Axis-aligned bounds in PageData model units (mm)."""

    min_x: float
    min_y: float
    max_x: float
    max_y: float
    unit: str = "mm"

    @property
    def width(self) -> float:
        return max(0.0, self.max_x - self.min_x)

    @property
    def height(self) -> float:
        return max(0.0, self.max_y - self.min_y)

    @property
    def center(self) -> Tuple[float, float]:
        return ((self.min_x + self.max_x) * 0.5, (self.min_y + self.max_y) * 0.5)

    def as_tuple(self) -> Tuple[float, float, float, float]:
        return (self.min_x, self.min_y, self.max_x, self.max_y)

    def with_padding(
        self,
        fraction: float = DEFAULT_PADDING_FRACTION,
        min_padding_mm: float = DEFAULT_MIN_PADDING_MM,
    ) -> "ImportBounds":
        span = max(self.width, self.height, min_padding_mm)
        pad = max(span * fraction, min_padding_mm)
        return ImportBounds(
            self.min_x - pad,
            self.min_y - pad,
            self.max_x + pad,
            self.max_y + pad,
            unit=self.unit,
        )


def _bbox_from_primitive(primitive: Primitive) -> Optional[Tuple[float, float, float, float]]:
    if primitive.bbox:
        return primitive.bbox
    if primitive.points:
        xs = [pt[0] for pt in primitive.points]
        ys = [pt[1] for pt in primitive.points]
        return (min(xs), min(ys), max(xs), max(ys))
    if primitive.center and primitive.radius is not None:
        cx, cy = primitive.center
        radius = primitive.radius
        return (cx - radius, cy - radius, cx + radius, cy + radius)
    return None


def _bbox_from_text(text: NormalizedText) -> Optional[Tuple[float, float, float, float]]:
    if text.bbox:
        return text.bbox
    if text.insertion:
        x, y = text.insertion
        return (x, y, x, y)
    return None


def _merge_bbox(
    acc: Optional[Tuple[float, float, float, float]],
    box: Tuple[float, float, float, float],
) -> Tuple[float, float, float, float]:
    if acc is None:
        return box
    return (min(acc[0], box[0]), min(acc[1], box[1]), max(acc[2], box[2]), max(acc[3], box[3]))


def _bounds_for_page(
    page: PageData,
    *,
    include_page_frame: bool,
) -> Optional[Tuple[float, float, float, float]]:
    merged: Optional[Tuple[float, float, float, float]] = None

    for primitive in page.primitives:
        box = _bbox_from_primitive(primitive)
        if box is not None:
            merged = _merge_bbox(merged, box)

    for text in page.text_items:
        box = _bbox_from_text(text)
        if box is not None:
            merged = _merge_bbox(merged, box)

    if merged is None and include_page_frame:
        return (0.0, 0.0, page.width, page.height)

    return merged


def compute_import_bounds(
    pages: Union[PageData, Sequence[PageData]],
    *,
    include_page_frame: bool = True,
    padding_fraction: float = DEFAULT_PADDING_FRACTION,
    min_padding_mm: float = DEFAULT_MIN_PADDING_MM,
    apply_padding: bool = True,
) -> Optional[ImportBounds]:
    """
    Compute union bounds for one or more imported pages.

    Returns padded bounds suitable for host autofit when ``apply_padding`` is True.
    """
    if isinstance(pages, PageData):
        page_list = [pages]
    else:
        page_list = list(pages)

    if not page_list:
        return None

    merged: Optional[Tuple[float, float, float, float]] = None
    for page in page_list:
        page_bounds = _bounds_for_page(page, include_page_frame=include_page_frame)
        if page_bounds is not None:
            merged = _merge_bbox(merged, page_bounds)

    if merged is None:
        return None

    bounds = ImportBounds(merged[0], merged[1], merged[2], merged[3])
    if apply_padding:
        return bounds.with_padding(
            fraction=padding_fraction,
            min_padding_mm=min_padding_mm,
        )
    return bounds


__all__ = [
    "DEFAULT_MIN_PADDING_MM",
    "DEFAULT_PADDING_FRACTION",
    "ImportBounds",
    "compute_import_bounds",
]
