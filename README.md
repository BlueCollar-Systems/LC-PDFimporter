# PDF to DXF Converter for LibreCAD

**BlueCollar Systems -- BUILT. NOT BOUGHT.**

Converts PDF vector drawings to DXF format for use with LibreCAD, AutoCAD,
DraftSight, QCAD, and any DXF-compatible CAD software.

## Features

- Extracts lines, polylines, arcs, circles, rectangles, and closed loops
- Preserves stroke colors, line widths, and dash patterns
- Imports text with font size and rotation
- Supports text modes (`labels`, `geometry`, `none`) and strict-text fidelity
- Supports raster-only and hybrid raster+vector import modes
- Organizes geometry into DXF layers (per-page and per-OCG)
- Multiple import presets: Fast, General, Technical, Shop Drawing, Raster+Vectors, Raster Only, Max Fidelity
- Outputs DXF versions from R12 through R2018
- CLI and GUI interfaces
- Built on pdfcadcore shared extraction engine

## Compatibility

| LibreCAD Version | Python | ezdxf | PyMuPDF | Status |
|-----------------|--------|-------|---------|--------|
| 2.1.x+ | 3.10+ | 1.0+ | >=1.24,<2.0 | ⚠️ Expected |
| 2.0.x | 3.8+ | 1.0+ | >=1.24,<2.0 | ⚠️ Expected |

Evidence levels:
- `✅ Verified`: host-run validation evidence captured.
- `⚠️ Expected`: syntax/runtime compatible but no host-run evidence yet.
- `❌ Not supported`: outside maintained/tested compatibility scope.

## Requirements

- Python 3.10+
- PyMuPDF >=1.24,<2.0
- ezdxf >= 1.0

## Installation

```
pip install -r requirements.txt
```

## CLI Usage

Basic conversion:
```
python pdf2dxf.py drawing.pdf
```

Specify output path:
```
python pdf2dxf.py drawing.pdf output.dxf
```

Convert specific pages with a preset:
```
python pdf2dxf.py drawing.pdf --pages 1,3,5 --preset technical --verbose
```

Skip text and arc detection for speed:
```
python pdf2dxf.py drawing.pdf --no-text --no-arcs --preset fast
```

Target a specific DXF version:
```
python pdf2dxf.py drawing.pdf --dxf-version R2004
```

All options:
```
python pdf2dxf.py input.pdf [output.dxf] [options]

Options:
  --pages 1,2,3          Pages to convert (default: all)
  --preset PRESET        fast | general | technical | shop | full | raster_vector | raster_only | max (default: shop)
  --mode MODE            auto | vectors | raster | hybrid
  --text-mode MODE       labels | geometry | none
  --strict-text-fidelity / --no-strict-text-fidelity
  --hatch-mode MODE      import | group | skip
  --arc-mode MODE        auto | preserve | rebuild | polyline
  --cleanup-level LVL    conservative | balanced | aggressive
  --lineweight-mode MODE ignore | preserve | group | map_to_layers
  --grouping-mode MODE   single | per_page | per_layer | per_color | nested_page_layer | nested_page_lineweight
  --raster-dpi DPI       Raster rendering DPI for raster/hybrid modes
  --no-raster-fallback   Disable automatic raster fallback when vectors are absent
  --scale 1.0            Scale factor
  --no-text              Skip text import
  --no-arcs              Skip arc detection
  --dxf-version VER      R12 | R2000 | R2004 | R2007 | R2010 | R2013 | R2018
  --gui                  Launch GUI instead of CLI
  --verbose              Print progress
  --version              Show version
```

## GUI Usage

Launch the graphical interface:
```
python pdf2dxf.py --gui
```

Or run the GUI directly:
```
python gui.py
```

The GUI provides file pickers, preset selection, page range input, option
checkboxes, a progress bar, and a status log.

## Batch Import

Convert an entire directory tree of PDFs to DXF:

```
python -m librecad_pdf_importer.batch_cli "C:\path\to\pdfs" "C:\path\to\out_dxf" --recursive --preset technical --pages all --json batch_report.json
```

## QA Smoke Harness

Run a quick automated smoke-test pass on one PDF or a folder:

```
python -m librecad_pdf_importer.qa_smoke "C:\path\to\pdfs" --preset technical --pages 1 --min-entities 1 --json qa_smoke.json
```

## Import Presets

| Preset     | Best For                          | Speed   |
|------------|-----------------------------------|---------|
| fast       | Quick preview, large files        | Fastest |
| general    | Most general-purpose PDFs         | Fast    |
| technical  | Engineering / technical drawings  | Medium  |
| shop       | Fabrication / shop drawings       | Medium  |
| raster_vector | Raster background + vector overlay | Medium |
| raster_only | Raster rendering only (no vectors) | Fast |
| full       | Same as shop                      | Medium  |
| max        | Highest accuracy, archival        | Slowest |

## DXF Compatibility

- **R12**: Maximum compatibility. No true-color, limited linetypes.
- **R2000 - R2004**: True-color support, standard linetypes.
- **R2007 - R2018**: Full feature set including lineweights.

The default R2010 output opens in LibreCAD, AutoCAD 2010+, DraftSight, QCAD,
and virtually all modern DXF readers.

## Project Structure

```
pdf2dxf.py            CLI entry point
gui.py                Tkinter GUI
dxf_import_engine.py  Pipeline orchestrator
dxf_builder.py        Primitive -> DXF entity mapping
dxf_text_builder.py   Text -> DXF TEXT/MTEXT mapping
pdfcadcore/           Shared PDF extraction core
```

## Known Limitations

| Limitation | Details |
|-----------|---------|
| Encrypted PDFs | Password-protected PDFs must be unlocked before import |
| Compression filters | Decoding is delegated to PyMuPDF. Malformed or non-standard compressed object streams may fail to parse |
| Raster-only scans | Pure raster PDFs produce no vector geometry |
| Clipped/XObject-heavy PDFs | Complex clip stacks and deeply nested form XObjects can produce partial geometry |
| MTEXT in LibreCAD | LibreCAD has known issues with MTEXT bounding boxes; TEXT fallback is used automatically |
| Embedded subset fonts | Text using embedded subset fonts may not render correctly |
| DXF version | R2010 is the recommended default; R12 mode uses TEXT entities only |
| Legacy hosts | LibreCAD/DXF consumer behavior outside the tested matrix is expected-only until verified |

## License

MIT License. Copyright (c) 2024-2026 BlueCollar Systems.
