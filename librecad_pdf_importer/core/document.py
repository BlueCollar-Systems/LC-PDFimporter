"""Host-neutral document extraction for PDF importer adapters."""
from __future__ import annotations

from dataclasses import dataclass, field
import math
from pathlib import Path
import tempfile
from typing import Iterable, List, Optional

try:
    import pymupdf as fitz  # PyMuPDF >= 1.24 preferred name
except ImportError:
    import fitz  # Legacy fallback

from .PDFDocumentProfiler import profile as profile_page
from .PDFGeometryCleanup import circle_fit
from .PDFPrimitiveExtractor import extract_page
from .PDFPrimitives import PageData

MM_PER_PT = 25.4 / 72.0


@dataclass
class ImagePlacement:
    page_number: int
    x_mm: float
    y_mm: float
    width_mm: float
    height_mm: float
    path: str
    xref: int


@dataclass
class ExtractedPage:
    page_data: PageData
    profile: object
    images: List[ImagePlacement] = field(default_factory=list)


@dataclass
class DocumentExtraction:
    pdf_path: str
    pages: List[ExtractedPage] = field(default_factory=list)

    @property
    def primitive_count(self) -> int:
        return sum(len(p.page_data.primitives) for p in self.pages)

    @property
    def text_count(self) -> int:
        return sum(len(p.page_data.text_items) for p in self.pages)

    @property
    def image_count(self) -> int:
        return sum(len(p.images) for p in self.pages)

    def summary(self) -> dict:
        return {
            "pdf_path": self.pdf_path,
            "pages": len(self.pages),
            "primitives": self.primitive_count,
            "text_items": self.text_count,
            "images": self.image_count,
            "profiles": [
                {
                    "page": p.page_data.page_number,
                    "primary_type": getattr(p.profile, "primary_type", "unknown"),
                    "scores": getattr(p.profile, "scores", {}),
                }
                for p in self.pages
            ],
        }


@dataclass
class ExtractionOptions:
    pages: Optional[Iterable[int] | str] = None
    scale: float = 1.0
    flip_y: bool = True
    import_text: bool = True
    import_images: bool = True
    import_mode: str = "auto"
    raster_fallback: bool = True
    raster_dpi: int = 200
    detect_arcs: bool = True
    arc_fit_tol_mm: float = 0.20
    min_arc_span_deg: float = 8.0
    min_segment_mm: float = 0.0
    max_text_items_per_page: Optional[int] = None
    image_dir: Optional[str] = None


def parse_pages_spec(spec: Optional[Iterable[int] | str], page_count: int) -> List[int]:
    if spec is None:
        return list(range(1, page_count + 1))
    if isinstance(spec, str):
        s = spec.strip().lower()
        if not s or s in {"1", "first"}:
            return [1]
        if s in {"all", "*", "a"}:
            return list(range(1, page_count + 1))
        pages: list[int] = []
        for token in s.split(","):
            token = token.strip()
            if not token:
                continue
            if "-" in token:
                left, right = token.split("-", 1)
                try:
                    a = int(left)
                    b = int(right)
                except ValueError:
                    continue
                if a > b:
                    a, b = b, a
                pages.extend(range(a, b + 1))
                continue
            try:
                pages.append(int(token))
            except ValueError:
                continue
        uniq = sorted({p for p in pages if 1 <= p <= page_count})
        return uniq or [1]
    out = sorted({int(p) for p in spec if 1 <= int(p) <= page_count})
    return out or [1]


def extract_document(pdf_path: str, options: Optional[ExtractionOptions] = None) -> DocumentExtraction:
    opts = options or ExtractionOptions()
    pdf_path = str(Path(pdf_path).expanduser().resolve())

    image_dir = Path(opts.image_dir).expanduser().resolve() if opts.image_dir else None
    if opts.import_images and image_dir is None:
        image_dir = Path(tempfile.mkdtemp(prefix="bc_lc_pdf_images_"))
    if image_dir is not None:
        image_dir.mkdir(parents=True, exist_ok=True)

    mode = _normalize_import_mode(opts.import_mode)
    extracted: list[ExtractedPage] = []

    with fitz.open(pdf_path) as doc:
        pages = parse_pages_spec(opts.pages, len(doc))
        for page_number in pages:
            page = doc.load_page(page_number - 1)
            page_data = extract_page(page, page_number, scale=opts.scale, flip_y=opts.flip_y)

            include_vectors = mode in {"auto", "vectors", "hybrid"}
            if include_vectors:
                if opts.min_segment_mm > 0:
                    _prune_micro_segments(page_data, opts.min_segment_mm)
                if not opts.import_text:
                    page_data.text_items = []
                elif opts.max_text_items_per_page is not None:
                    cap = int(max(0, opts.max_text_items_per_page))
                    if len(page_data.text_items) > cap:
                        page_data.text_items = page_data.text_items[:cap]
                if opts.detect_arcs:
                    _promote_arcs(page_data, opts.arc_fit_tol_mm, opts.min_arc_span_deg)
            else:
                page_data.primitives = []
                page_data.text_items = []

            profile = profile_page(page_data)
            images = []
            if opts.import_images:
                if mode in {"raster", "hybrid"}:
                    rendered = _render_page_raster(page, page_number, opts, image_dir)
                    if rendered is not None:
                        images.append(rendered)
                elif mode == "auto":
                    images = _extract_images(doc, page, page_number, opts, image_dir)
                    if opts.raster_fallback and not page_data.primitives and not images:
                        rendered = _render_page_raster(page, page_number, opts, image_dir)
                        if rendered is not None:
                            images.append(rendered)

            extracted.append(ExtractedPage(page_data=page_data, profile=profile, images=images))

    return DocumentExtraction(pdf_path=pdf_path, pages=extracted)


def _normalize_import_mode(raw: str | None) -> str:
    mode = (raw or "auto").strip().lower()
    if mode in {"vectors", "vector", "vector_only", "vectors_only"}:
        return "vectors"
    if mode in {"raster", "raster_only", "image", "images"}:
        return "raster"
    if mode in {"hybrid", "raster_vector", "raster+vectors", "raster_vectors"}:
        return "hybrid"
    return "auto"


def _promote_arcs(page_data: PageData, arc_fit_tol_mm: float, min_arc_span_deg: float) -> None:
    for primitive in page_data.primitives:
        if primitive.type not in {"polyline", "closed_loop"}:
            continue
        pts = primitive.points or []
        if len(pts) < 6:
            continue
        fit = circle_fit(pts)
        if not fit:
            continue
        cx, cy, radius, rms = fit
        if rms > arc_fit_tol_mm or radius <= 0:
            continue

        angles = [math.degrees(math.atan2(y - cy, x - cx)) for x, y in pts]
        unwrapped = _unwrap_angles(angles)
        span = max(unwrapped) - min(unwrapped)

        if primitive.closed and span >= 330.0:
            primitive.type = "circle"
            primitive.center = (cx, cy)
            primitive.radius = radius
            primitive.start_angle = 0.0
            primitive.end_angle = 360.0
            continue

        if span < min_arc_span_deg:
            continue

        primitive.type = "arc"
        primitive.center = (cx, cy)
        primitive.radius = radius
        primitive.start_angle = _wrap_angle(unwrapped[0])
        primitive.end_angle = _wrap_angle(unwrapped[-1])
        primitive.closed = False


def _prune_micro_segments(page_data: PageData, min_segment_mm: float) -> None:
    if min_segment_mm <= 0:
        return
    kept = []
    for primitive in page_data.primitives:
        if primitive.type == "line" and len(primitive.points or []) == 2:
            (x0, y0), (x1, y1) = primitive.points
            if math.hypot(x1 - x0, y1 - y0) < min_segment_mm:
                continue
        kept.append(primitive)
    page_data.primitives = kept


def _wrap_angle(value: float) -> float:
    while value < 0.0:
        value += 360.0
    while value >= 360.0:
        value -= 360.0
    return value


def _unwrap_angles(values: list[float]) -> list[float]:
    if not values:
        return []
    unwrapped = [values[0]]
    for angle in values[1:]:
        prev = unwrapped[-1]
        candidate = angle
        while candidate - prev > 180.0:
            candidate -= 360.0
        while candidate - prev < -180.0:
            candidate += 360.0
        unwrapped.append(candidate)
    return unwrapped


def _extract_images(doc: fitz.Document, page: fitz.Page, page_number: int,
                    options: ExtractionOptions, image_dir: Optional[Path]) -> List[ImagePlacement]:
    placements: list[ImagePlacement] = []
    if image_dir is None:
        return placements

    page_height = float(page.rect.height)
    seen: set[int] = set()
    for img_info in page.get_images(full=True):
        xref = int(img_info[0])
        if xref in seen:
            continue
        seen.add(xref)

        try:
            pix = fitz.Pixmap(doc, xref)
            color_space_n = None
            try:
                color_space_n = int(getattr(getattr(pix, "colorspace", None), "n", 0))
            except (TypeError, ValueError):
                color_space_n = None

            needs_rgb = pix.alpha or pix.n != 3 or (color_space_n is not None and color_space_n != 3)
            if needs_rgb:
                pix = fitz.Pixmap(fitz.csRGB, pix)

            img_path = image_dir / f"page_{page_number:03d}_xref_{xref}.png"
            pix.save(str(img_path))
        except (RuntimeError, OSError, ValueError, TypeError):
            continue

        rects = page.get_image_rects(xref)
        for rect in rects:
            x0, y0, x1, y1 = float(rect.x0), float(rect.y0), float(rect.x1), float(rect.y1)
            left = min(x0, x1)
            right = max(x0, x1)

            if options.flip_y:
                bottom_pt = page_height - max(y0, y1)
                top_pt = page_height - min(y0, y1)
            else:
                bottom_pt = min(y0, y1)
                top_pt = max(y0, y1)

            placements.append(
                ImagePlacement(
                    page_number=page_number,
                    x_mm=left * MM_PER_PT * options.scale,
                    y_mm=bottom_pt * MM_PER_PT * options.scale,
                    width_mm=(right - left) * MM_PER_PT * options.scale,
                    height_mm=(top_pt - bottom_pt) * MM_PER_PT * options.scale,
                    path=str(img_path),
                    xref=xref,
                )
            )

    return placements


def _render_page_raster(page: fitz.Page, page_number: int, options: ExtractionOptions,
                        image_dir: Optional[Path]) -> Optional[ImagePlacement]:
    if image_dir is None:
        return None

    dpi = int(max(36, options.raster_dpi or 200))
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)

    try:
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        img_path = image_dir / f"page_{page_number:03d}_raster_{dpi}dpi.png"
        pix.save(str(img_path))
    except (RuntimeError, OSError, ValueError, TypeError):
        return None

    width_mm = float(page.rect.width) * MM_PER_PT * options.scale
    height_mm = float(page.rect.height) * MM_PER_PT * options.scale
    return ImagePlacement(
        page_number=page_number,
        x_mm=0.0,
        y_mm=0.0,
        width_mm=width_mm,
        height_mm=height_mm,
        path=str(img_path),
        xref=-1,
    )
