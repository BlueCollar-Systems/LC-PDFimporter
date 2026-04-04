# PDF to DXF Converter for LibreCAD

**BlueCollar Systems -- BUILT. NOT BOUGHT.**

Converts PDF vector drawings to DXF format for use with LibreCAD, AutoCAD,
DraftSight, QCAD, and any DXF-compatible CAD software.

## Features

- Extracts lines, polylines, arcs, circles, rectangles, and closed loops
- Preserves stroke colors, line widths, and dash patterns
- Imports text with font size and rotation
- Organizes geometry into DXF layers (per-page and per-OCG)
- Multiple import presets: Fast, General, Technical, Shop Drawing, Max Fidelity
- Outputs DXF versions from R12 through R2018
- CLI and GUI interfaces
- Built on pdfcadcore shared extraction engine

## Requirements

- Python 3.10+
- PyMuPDF >= 1.24
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
  --preset PRESET        fast | general | technical | shop | full | max (default: shop)
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

## Import Presets

| Preset     | Best For                          | Speed   |
|------------|-----------------------------------|---------|
| fast       | Quick preview, large files        | Fastest |
| general    | Most general-purpose PDFs         | Fast    |
| technical  | Engineering / technical drawings  | Medium  |
| shop       | Fabrication / shop drawings       | Medium  |
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

## License

MIT License. Copyright (c) 2024-2026 BlueCollar Systems.
