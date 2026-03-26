# Developer Tools

This document covers two developer utilities in the repo root and the test fixtures directory that are not part of the production codebase but are essential for day-to-day development workflow.

---

## `resume.sh` — Agent Session Resume Script

**Location:** `resume.sh` (repo root)

### Purpose

`resume.sh` allows you to resume a coding agent session after being away from the project. It reads the last active session for a given agent and relaunches it with the correct flags to continue where it left off, with full workspace-write and terminal-execution permissions already granted.

### Usage

```bash
# Interactive — prompts you to select an agent
./resume.sh

# Direct — specify agent by name
./resume.sh opencode
./resume.sh codex
./resume.sh claude
./resume.sh gemini
./resume.sh qwen
```

### Workflow

1. Open `specs/007-agent-pipeline/feature_journal.md` (or relevant feature journal).
2. Read the most recent entry's `Recorded by:` line to identify which agent was last working.
3. Run `./resume.sh <agent-name>` to relaunch that agent in resume mode.
4. The agent will reload its last session context and you can continue without re-reading the full journal.

### Agent Resume Flags

| Agent | Resume Command |
|-------|---------------|
| `codex` | `codex -a never -s workspace-write resume --last` |
| `opencode` | `opencode --continue` |
| `claude` | `claude --resume --permission-mode bypassPermissions` |
| `gemini` | `gemini --resume latest --yolo` |
| `qwen` | `qwen --continue --approval-mode=yolo` |

### Notes

- The script must be run from the repo root (it `cd`s there automatically).
- It will exit with an error if the selected agent CLI is not on `PATH`.
- Permission flags (`bypassPermissions`, `workspace-write`, `--yolo`) are intentional — they grant the agent broad access needed for autonomous multi-step development tasks. Only use in a trusted local environment.

---

## `tests/fixtures/pdf_convert/The Homebrewery - NaturalCrit.md` — PDF Source Markdown

**Location:** `tests/fixtures/pdf_convert/The Homebrewery - NaturalCrit.md`

### Purpose

This is the Homebrewery V3 markdown source file used to regenerate the two PDF test fixtures:

- `tests/fixtures/pdf_convert/The Homebrewery - NaturalCrit.pdf` (with embedded TOC)
- `tests/fixtures/pdf_convert/The Homebrewery - NaturalCrit - Without TOC.pdf` (no TOC)

These PDFs are the primary test corpus for the `gmkit pdf-convert` pipeline. When the test content needs to change (e.g. updating the table section to test table detection), this markdown file is edited, a new PDF is generated, and the fixtures are replaced.

### How to regenerate the PDFs

1. Open [https://homebrewery.naturalcrit.com/](https://homebrewery.naturalcrit.com/) in Google Chrome.
2. Paste the full contents of `The Homebrewery - NaturalCrit.md` into the left editor pane.
3. The right pane will render the PDF preview in real time.
4. To generate **With TOC** version:
   - Use Chrome's Print dialog (`Ctrl+P` or the navbar Print item).
   - Set Destination to "Save as PDF", Paper Size to "Letter", enable Background Images.
   - Save as `The Homebrewery - NaturalCrit.pdf`.
   - The Homebrewery web app embeds a PDF outline (TOC) automatically based on headings.
5. To generate **Without TOC** version:
   - Save the same PDF (the content is identical).
   - Use PyMuPDF to strip the outline — or simply save as above and then run the fixture replacement script described below.

### How to update the fixtures after regenerating

After saving a new PDF, run the following Python snippet from the repo root to inject the original TOC outline into the with-TOC fixture:

```python
import fitz, shutil
from pathlib import Path

base = Path("tests/fixtures/pdf_convert")
new_pdf = base / "The Homebrewery - NaturalCrit - new.pdf"        # your newly generated PDF
with_toc = base / "The Homebrewery - NaturalCrit.pdf"             # target: with TOC
without_toc = base / "The Homebrewery - NaturalCrit - Without TOC.pdf"  # target: no TOC

# Save without-TOC version (new content, no outline)
shutil.copy2(new_pdf, without_toc)

# Inject the original TOC outline into the with-TOC version
doc_orig = fitz.open(str(with_toc))
toc = doc_orig.get_toc(simple=False)
doc_orig.close()

doc_new = fitz.open(str(new_pdf))
doc_new.set_toc(toc)
doc_new.save(str(with_toc), garbage=4, deflate=True)
doc_new.close()

new_pdf.unlink()  # remove the temporary generated PDF
print("Fixtures updated.")
```

### Notes

- The markdown uses Homebrewery V3 syntax (`{{note`, `\column`, `\page`, `{{pageNumber`, etc.) which is not standard Markdown. Do not run it through a standard Markdown renderer.
- The `Note: For gmkit ...` comment on the Tables page is intentional — it documents the gmkit limitation inline so it appears in the rendered PDF and feeds correctly into test expectations.
- The Weapons table (`Name / Damage / Range`) was added specifically to provide strong table detection signals for step 7.7 of the agent pipeline. If you change the table content, re-run the harness to verify step 7.7 detection still works.
- Both PDF fixtures must always contain identical page content — the only difference between them is the presence or absence of the embedded PDF outline (TOC).
