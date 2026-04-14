# How to Use the LibreCAD PDF Importer

This tool converts PDF drawings to DXF files that you can open in LibreCAD, AutoCAD, DraftSight, QCAD, or any DXF-compatible CAD program.

## Quick Start

### Option 1: LibreCAD Plugins menu (recommended)
1. Build/install plugin:
```powershell
powershell -ExecutionPolicy Bypass -File .\plugin\build_install_lcpdf_menu.ps1
```
2. Restart LibreCAD
3. Use `Plugins > PDF Importer (BlueCollar)...`

### Option 2: Command Line (fastest)
```bash
python pdf2dxf.py "C:\path\to\drawing.pdf" "C:\output\drawing.dxf"
```

### Option 3: GUI Window (no terminal required)
```bash
python gui.py
```
A window opens where you can browse for a PDF, choose presets, export, and
auto-open the DXF in LibreCAD.

### Option 3b: Double-click launcher (Windows, no terminal)
- Double-click `launch_lcpdf_gui.pyw`
- Or install entrypoint and run `lcpdf-guiw`

### Option 4: Batch Convert (multiple files)
```bash
python -m librecad_pdf_importer.batch_cli "C:\folder\with\pdfs"
```

## After Converting

1. In the GUI, keep `Open in LibreCAD after convert` enabled
2. Click `Convert`
3. LibreCAD opens automatically with the generated DXF

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
