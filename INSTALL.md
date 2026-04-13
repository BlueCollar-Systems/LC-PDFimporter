# How to Use the LibreCAD PDF Importer

This tool converts PDF drawings to DXF files that you can open in LibreCAD, AutoCAD, DraftSight, QCAD, or any DXF-compatible CAD program.

## Quick Start

### Option 1: Command Line (fastest)
```bash
python pdf2dxf.py "C:\path\to\drawing.pdf" "C:\output\drawing.dxf"
```

### Option 2: GUI Window
```bash
python gui.py
```
A window opens where you can browse for a PDF, choose presets, and export.

### Option 3: Batch Convert (multiple files)
```bash
python -m librecad_pdf_importer.batch_cli "C:\folder\with\pdfs"
```

## After Converting

1. Open LibreCAD
2. File > Open > select your .dxf file
3. The drawing should auto-zoom to fit

## Presets

| Preset | Best For | Speed |
|--------|----------|-------|
| fast | Quick preview | Fastest |
| general | Most PDFs | Fast |
| technical | Engineering drawings | Medium |
| shop | Fabrication shop drawings | Medium |
| max | Maximum accuracy | Slower |

## Requirements

- Python 3.10+
- PyMuPDF: `pip install "PyMuPDF>=1.24,<2.0"`
- ezdxf: `pip install ezdxf`

## Troubleshooting

**Black screen when opening DXF?** The importer auto-inverts white lines to black for visibility. If you still see a blank screen, try View > Auto Zoom in LibreCAD.

**Missing text?** Try the `technical` or `max` preset which extracts more text detail.

**Geometry looks wrong?** Try a different preset — `shop` is best for steel fabrication drawings.
