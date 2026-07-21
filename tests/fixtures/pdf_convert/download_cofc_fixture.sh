#!/usr/bin/env bash
set -euo pipefail

DEST_DIR="tests/fixtures/pdf_convert"
DEST_FILE="${DEST_DIR}/CHA23131 Call of Cthulhu 7th Edition Quick-Start Rules.pdf"

# Public source; override with COFC_PDF_URL if needed.
COFC_PDF_URL_DEFAULT="https://www.chaosium.com/content/FreePDFs/CoC/CHA23131%20Call%20of%20Cthulhu%207th%20Edition%20Quick-Start%20Rules.pdf"
COFC_PDF_URL="${COFC_PDF_URL:-$COFC_PDF_URL_DEFAULT}"

echo "Downloading CoC fixture..."
echo "URL: ${COFC_PDF_URL}"
mkdir -p "${DEST_DIR}"

if command -v curl >/dev/null 2>&1; then
  curl -fL "${COFC_PDF_URL}" -o "${DEST_FILE}"
elif command -v wget >/dev/null 2>&1; then
  wget -O "${DEST_FILE}" "${COFC_PDF_URL}"
else
  echo "Error: curl or wget is required." >&2
  exit 1
fi

if [[ ! -s "${DEST_FILE}" ]]; then
  echo "Error: downloaded file is empty: ${DEST_FILE}" >&2
  exit 1
fi

echo "Saved fixture: ${DEST_FILE}"
