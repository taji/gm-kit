# PDF Fixtures

This folder contains fixture files used by integration tests for `gmkit pdf-convert`.

## Policy

- Do **not** commit copyrighted third-party PDFs without explicit redistribution rights.
- Homebrewery-generated fixtures in this folder are project-authored test assets.
- Third-party PDFs should be downloaded locally via scripts into this folder and kept untracked.

## Required Fixtures

- `The Homebrewery - NaturalCrit.pdf` (committed)
- `The Homebrewery - NaturalCrit - Without TOC.pdf` (committed)
- `Dungeon Module B2, The Keep on the Borderlands.pdf` (download locally)

## Optional Private Fixtures (Not Committed)

- `CHA23131 Call of Cthulhu 7th Edition Quick-Start Rules.pdf`
- `The Wild Sheep Chase.pdf`

Use these only in local/private workflows where you have rights to store and use them.

## Download Script

To fetch the B2 fixture into this directory:

```bash
bash tests/fixtures/pdf_convert/download_b2_fixture.sh
```

Default source URL:

- `https://archive.org/download/dungeon-module-b-2-the-keep-on-the-borderlands/Dungeon%20Module%20B2%2C%20The%20Keep%20on%20the%20Borderlands.pdf`

The script writes:

- `tests/fixtures/pdf_convert/Dungeon Module B2, The Keep on the Borderlands.pdf`

If the default URL stops working, set `B2_PDF_URL` when running the script:

```bash
B2_PDF_URL='https://example.com/path/to/B2.pdf' \
  bash tests/fixtures/pdf_convert/download_b2_fixture.sh
```

To fetch the optional CoC fixture into this directory:

```bash
bash tests/fixtures/pdf_convert/download_cofc_fixture.sh
```

Default source URL:

- `https://www.chaosium.com/content/FreePDFs/CoC/CHA23131%20Call%20of%20Cthulhu%207th%20Edition%20Quick-Start%20Rules.pdf`

The script writes:

- `tests/fixtures/pdf_convert/CHA23131 Call of Cthulhu 7th Edition Quick-Start Rules.pdf`

If the default URL stops working, set `COFC_PDF_URL` when running the script:

```bash
COFC_PDF_URL='https://example.com/path/to/CHA23131.pdf' \
  bash tests/fixtures/pdf_convert/download_cofc_fixture.sh
```
