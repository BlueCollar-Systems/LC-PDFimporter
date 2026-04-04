# -*- coding: utf-8 -*-
# pdfcadcore — Shared PDF vector import core
# BlueCollar Systems — BUILT. NOT BOUGHT.
"""
Host-neutral PDF vector extraction, recognition, and cleanup.
Used by FreeCAD, Blender, and LibreCAD importers.
"""
__version__ = "1.0.0"

from .primitives import (
    Primitive, NormalizedText, PageData, ParsedDimension,
    Region, PageProfile, RecognitionConfig, next_id, reset_ids,
)
from .import_config import ImportConfig, CLEANUP_PRESETS
from .primitive_extractor import extract_page
from .auto_mode import classify_page_content
from .hatch_detector import tag_hatch_primitives
from .geometry_cleanup import cleanup_primitives
