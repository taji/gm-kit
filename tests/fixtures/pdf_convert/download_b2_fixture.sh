#!/usr/bin/env bash
set -euo pipefail

DEST_DIR="tests/fixtures/pdf_convert"
DEST_FILE="${DEST_DIR}/Dungeon Module B2, The Keep on the Borderlands.pdf"

# Public source; override with B2_PDF_URL if needed.
B2_PDF_URL_DEFAULT="https://archive.org/download/dungeon-module-b-2-the-keep-on-the-borderlands/Dungeon%20Module%20B2%2C%20The%20Keep%20on%20the%20Borderlands.pdf"
B2_PDF_URL="${B2_PDF_URL:-$B2_PDF_URL_DEFAULT}"

echo "Downloading B2 fixture..."
echo "URL: ${B2_PDF_URL}"
mkdir -p "${DEST_DIR}"

if command -v curl >/dev/null 2>&1; then
  curl -fL "${B2_PDF_URL}" -o "${DEST_FILE}"
elif command -v wget >/dev/null 2>&1; then
  wget -O "${DEST_FILE}" "${B2_PDF_URL}"
else
  echo "Error: curl or wget is required." >&2
  exit 1
fi

if [[ ! -s "${DEST_FILE}" ]]; then
  echo "Error: downloaded file is empty: ${DEST_FILE}" >&2
  exit 1
fi

echo "Saved fixture: ${DEST_FILE}"
