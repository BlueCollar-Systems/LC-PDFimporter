# LibreCAD Production Benchmark (2026-04-03)

## Inputs
- `C:\Users\Rowdy Payton\Desktop\New folder (2)\TX_Alvord_20220525_TM_geo.pdf`
- `C:\Users\Rowdy Payton\Desktop\New folder (2)\Alvord TX — Garden Plan · Final.pdf`
- `C:\Users\Rowdy Payton\Desktop\New folder (2)\New folder\1019 - Rev 0.pdf`
- `C:\Users\Rowdy Payton\Desktop\New folder (2)\Welding-Symbol-Chart.pdf`

## Summary by Preset

| Preset | Runs | Avg Runtime (s) | Avg Primitives | Avg Text Items | Avg Entities |
|---|---:|---:|---:|---:|---:|
| fast | 4 | 3.949 | 2616 | 0 | 2616 |
| general | 4 | 4.123 | 3212 | 1132 | 4344 |
| technical | 4 | 4.085 | 3212 | 507 | 3719 |
| shop | 4 | 4.149 | 3212 | 757 | 3969 |
| max | 4 | 4.199 | 3212 | 2274.5 | 5486.5 |

## Notes
- Technical and Shop presets now cap exported text entities on heavy sheets.
- Fast preset prunes micro line segments for faster DXF generation.
