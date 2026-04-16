# LLM Prime Directive: BlueCollar Systems PDF Importers

## 1. Absolute Objective

The singular goal of this project is **100% visual and geometric perfection** when importing PDF vector data into the target CAD environments (Blender, FreeCAD, LibreCAD, and SketchUp). Acceptable output means zero unhandled discontinuities, zero dropped primitives, and exact visual parity with the source PDF. This standard is limited *only* by the hard technical boundaries of the parent software.

## 2. Operating Methods

- **Verify Against Diverse Geometry:** Solutions must universally apply to the provided test suite (10 PDFs listed in `Test File Paths.txt`). A fix that works on simple geometry must not break complex, high-density files like the Alvord Garden maps, or technical documents like the Welding-Symbol-Chart and structural sheets (1058, 1071).
- **Isolate Target Syntax:** Code must be strictly segmented. Do not allow SketchUp Ruby logic to pollute LibreCAD Python DXF generators, or FreeCAD topological rules to interfere with Blender mesh generation. Cross-platform core logic must remain entirely agnostic.
- **Prioritize Visual Fidelity:** If a mathematical conversion or tolerance adjustment causes a visual artifact (such as a shattered spline, an open contour, or an inverted arc), the logic is invalid. Visual continuity dictates the success of the algorithm.

## 3. Mandatory Regression Prevention

To prevent catastrophic forgetting and the sycophantic acceptance of broken code, the LLM is bound by the following self-policing rules:

- **The Invariant Check:** Before outputting modified code, internally review the established functionality. You are strictly forbidden from altering previously solved core logic (such as bezier subdivision rates or scaling matrix math) to apply a localized band-aid to a new problem.
- **Zero-Tolerance for Degradation:** Never argue that a new visual discontinuity is "acceptable," "a known limitation," or "close enough." If a proposed fix causes a regression in a previously working test file, immediately flag it as a critical failure, reject the approach, and formulate a new path.
- **Forced Context Resets:** If a debugging thread exceeds 5 back-and-forth turns without achieving a perfectly validated fix, pause operations. Explicitly instruct the user to commit the last stable code, regenerate the repository context files, and initialize a fresh chat session to restore maximum attention accuracy.
- **Automated Enforcement:** The regression guard scripts (`regression_guard.py`, `regression_guard_su.rb`, `pdfcadcore_sync_check.py`) are the automated enforcement mechanism. The `LLM_SESSION_RULES.md` constraints block is the behavioral mechanism. Both are required. LLM self-policing alone is insufficient — the golden baselines are the source of truth.

## 4. Project Scope

Four PDF importers:

- **Blender** (1BL-PDFimporter) — Python, pdfcadcore + Blender adapter
- **FreeCAD** (1FC-PDFimporter) — Python, pdfcadcore + FreeCAD adapter
- **LibreCAD** (1LC-PDFimporter) — Python, pdfcadcore + DXF exporter
- **SketchUp** (1SU-PDFimporter) — Ruby, independent implementation

Shared extraction core: `pdfcadcore` (15 Python files, embedded in BL/FC/LC repos). FreeCAD is the canonical copy. Changes must be mirrored to all three.

Regression corpus: 10 PDFs listed in `Test File Paths.txt`.

## 5. What Success Means

A successful fix preserves or improves **all** of the following:

- Geometry completeness
- Continuity and closure
- Page coverage
- Scale and placement
- Text behavior, within host limitations
- Layers, tags, groups, or collections
- Linework, arcs, circles, hatches, and dash behavior where supported
- Raster/vector mode choice
- Overall visual appearance

A run is **not** successful just because it passes a smoke test, returns exit code 0, or produces some output.

## 6. Non-Negotiable Rules

1. A previously fixed issue must remain fixed.
2. Never redefine acceptable output downward.
3. Never call a regression acceptable because the host "still imported something."
4. Never trade away visual correctness to improve a weak numeric metric unless the host software truly cannot do better.
5. Never make broad refactors during bug-fix work unless the task explicitly requires it.
6. Never change unrelated presets, defaults, thresholds, or architecture just to get one test passing.

## 7. Required Working Method

For every task, do this in order:

1. Read the latest project context pack for the relevant importer.
2. State the exact bug or failure mode in one sentence.
3. Reproduce it using the regression corpus.
4. Record baseline evidence before changing code.
5. Identify whether the bug belongs in shared extraction/core logic, or host-specific adapter/export/build logic.
6. Make the **smallest root-cause fix**.
7. Re-run the affected PDF(s), preset(s), mode(s), and page ranges.
8. Re-run `regression_guard.py` (and `regression_guard_su.rb` if SU was involved).
9. Run `pdfcadcore_sync_check.py` if any core file was touched.
10. Compare before vs. after.
11. Only declare success if the target bug is fixed and no unrelated behavior became worse.

## 8. How to Decide Where to Fix

**Fix in pdfcadcore (shared core) when the issue involves:**

- PDF parsing
- Primitive extraction
- Page selection
- Classification or profiling
- Auto-mode logic
- Geometry cleanup
- Arc or circle reconstruction
- Text/image extraction decisions
- Raster fallback decisions

**Fix in the host adapter/export layer when the issue involves:**

- FreeCAD object creation
- SketchUp edges, faces, tags, or groups
- Blender curves, text objects, collections, or materials
- LibreCAD/DXF entity creation, layer mapping, or export arrangement
- Host-only coordinate, scaling, or display behavior

Do not duplicate the same behavioral fix in multiple places unless duplication is proven necessary.

## 9. Hard Fail Conditions

Treat each of these as failure unless the parent software truly cannot support the feature:

- Missing output payload or result JSON
- Wrong page count
- Missing geometry that should exist
- Broken continuity where continuity should exist
- Scale drift beyond tolerance
- Wrong raster/vector/hybrid decision
- Missing text where text should be imported
- Missing layers/tags/groups/collections when supported
- Visual degradation even if counts improved
- Pass criteria based only on page 1 when the real job is multi-page
- Weak threshold passes such as "1 primitive is enough" or "1 entity is enough" for real regression validation

## 10. Mandatory Regression Guardrails

Every bug fix must leave behind its own protection. For every completed fix, add at least one of these:

- Automated test
- Expected-output check
- Stricter QA fail condition
- Per-file regression assertion
- Host verification check
- Corpus-specific guardrail tied to the exact PDF, mode, and preset

## 11. Required Self-Check Before Finishing

Before ending any work session, answer these:

1. Did I fix the root cause instead of masking the symptom?
2. Could this change break a different preset or import mode?
3. Could this change break another importer that shares the same logic?
4. Did I add a permanent guardrail for this exact regression?
5. Does the result look better, or at least no worse, in the actual host application?
6. Did `regression_guard.py` report ALL PASS?
7. Did `pdfcadcore_sync_check.py` report ALL IN SYNC? (if core was touched)

If any answer is unknown, the task is not complete.

## 12. Required Session Output

After every completed fix, report:

1. Bug addressed
2. Root cause
3. Files changed and reason for each change
4. Before/after evidence
5. Regression checks run and results
6. Remaining risk
7. Regression guardrail added

If item 7 is missing, the work is incomplete.

## 13. High-Level Roadmap

| Phase | Goal | Who Drives It |
|-------|------|---------------|
| 1 | Lock regression workflow (golden baselines captured, guard scripts running) | You |
| 2 | Stabilize shared core (pdfcadcore) against all 10 test PDFs | LLM |
| 3 | Finish Blender importer | LLM |
| 4 | Finish FreeCAD, LibreCAD, and SketchUp importers | LLM |
| 5 | Final hardening and cross-importer verification | You + LLM |

### Phase 1 — Lock Regression Workflow

This is done BEFORE any code stabilization begins.

1. Get all 4 importers to their best current state.
2. Run `0run_full_suite.cmd` to capture golden baselines.
3. Confirm `golden_baselines.json` and `golden_baselines_su.json` exist.
4. From this point forward, every code change is followed by a regression guard run.

### Phase 2 — Stabilize the Shared Core

Task description for the LLM (inside the session constraints block):

> We are stabilizing the shared core PDF extraction/normalization library used by all four importers. Your job is to ensure primitives, text, layers, colors, and images are extracted with maximum fidelity; ensure arc/circle detection is correct; ensure page selection, modes, and presets behave correctly; ensure the 10 test PDFs all extract correctly. Do not change host-specific adapters yet.

Run `regression_guard.py` after every change. The golden baselines ARE the automated tests.

### Phase 3 — Finish the Blender Importer

Task description for the LLM:

> We are now finishing the Blender importer. Use the stabilized core pipeline as given. Ensure Blender geometry, text, images, layers, and colors match the PDF visually. Ensure all presets and modes behave correctly. Ensure the 10 test PDFs import cleanly. Do not change the core library unless absolutely necessary.

### Phase 4 — Finish the Other Three Importers

Repeat the Phase 3 pattern for FreeCAD, LibreCAD, and SketchUp. For each:

- Use the session constraints block
- Focus on host-adapter changes
- Always remind the LLM: "Do not change the shared core unless absolutely necessary. Prefer host-adapter changes."
- Run the regression guard after every change

### Phase 5 — Final Hardening

Once all four importers are complete:

- Re-run the full suite one final time
- Recapture golden baselines
- Verify pdfcadcore sync across all three Python repos
- Archive the golden baselines in version control

## 14. Final Rule

Do not chase green checkmarks. Do not chase broad refactors. Do not chase "good enough."

Chase repeatable correctness until all four importers are as visually faithful and regression-resistant as the host software allows.
