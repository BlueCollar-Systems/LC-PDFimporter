from __future__ import annotations

import math
import tempfile
import unittest
from pathlib import Path

import ezdxf
import fitz

from librecad_pdf_importer.exporters.dxf_exporter import export_to_dxf
from librecad_pdf_importer.importer import run_import


class TestDxfPipeline(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="lc_pdf_importer_test_")
        self.tmp_path = Path(self._tmp.name)
        self.pdf_path = self.tmp_path / "sample.pdf"
        self.dxf_path = self.tmp_path / "sample.dxf"
        self._build_sample_pdf(self.pdf_path)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _build_sample_pdf(self, out_path: Path) -> None:
        doc = fitz.open()
        page = doc.new_page(width=600, height=400)
        page.draw_line((50, 50), (300, 50), color=(0, 0, 0), width=1.0)

        center = (210, 200)
        radius = 40
        pts = []
        for i in range(12):
            angle = 2 * math.pi * i / 12
            pts.append((center[0] + radius * math.cos(angle), center[1] + radius * math.sin(angle)))
        pts.append(pts[0])
        page.draw_polyline(pts, color=(0, 0, 1), width=1.0)

        page.insert_text((70, 130), "BOLT 3/4\" DIA", fontsize=12)

        pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 12, 12), 0)
        pix.clear_with(0x3366CC)
        page.insert_image(fitz.Rect(360, 60, 420, 120), stream=pix.tobytes("png"))

        doc.save(str(out_path))

    def test_pdf_to_dxf_export(self) -> None:
        run = run_import(str(self.pdf_path), preset="technical", overrides={"pages": "1"})
        export = export_to_dxf(run.extraction, str(self.dxf_path))

        self.assertTrue(Path(export.output_path).is_file())
        self.assertGreater(export.entity_count, 0)
        self.assertGreaterEqual(export.layer_count, 1)

        dxf = ezdxf.readfile(export.output_path)
        entities = list(dxf.modelspace())
        self.assertGreater(len(entities), 0)

        types = {entity.dxftype() for entity in entities}
        self.assertTrue({"LINE", "LWPOLYLINE", "ARC", "CIRCLE"}.intersection(types))


if __name__ == "__main__":
    unittest.main(verbosity=2)
