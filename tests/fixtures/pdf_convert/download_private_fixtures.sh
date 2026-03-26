#!/usr/bin/env bash
# Download private PDF test fixtures from the gm-kit-fixtures GitHub release.
#
# Prerequisites:
#   - gh CLI installed and authenticated (or GH_TOKEN env var set)
#   - FIXTURES_REPO_TOKEN set in CI (injected via GH_TOKEN below)
#
# Usage:
#   Local:  bash tests/fixtures/pdf_convert/download_private_fixtures.sh
#   CI:     GH_TOKEN=$FIXTURES_REPO_TOKEN bash tests/fixtures/pdf_convert/download_private_fixtures.sh
set -euo pipefail

DEST_DIR="tests/fixtures/pdf_convert"
FIXTURES_REPO="${FIXTURES_REPO:-taji/gm-kit-fixtures}"
FIXTURES_TAG="${FIXTURES_TAG:-v1.0.0}"

mkdir -p "${DEST_DIR}"

# Verify gh CLI is available.
if ! command -v gh >/dev/null 2>&1; then
    echo "Error: gh CLI is required to download private fixtures." >&2
    echo "Install from https://cli.github.com/ or set up the action in CI." >&2
    exit 1
fi

echo "Downloading private fixtures from ${FIXTURES_REPO}@${FIXTURES_TAG}..."

# Each entry: "asset-name-on-github|local-filename-expected-by-tests"
# GitHub replaces spaces with dots on upload; tests expect the original spaced names.
FIXTURE_MAP=(
    "CHA23131.Call.of.Cthulhu.7th.Edition.Quick-Start.Rules.pdf|CHA23131 Call of Cthulhu 7th Edition Quick-Start Rules.pdf"
    "Dungeon.Module.B2.The.Keep.on.the.Borderlands.pdf|Dungeon Module B2, The Keep on the Borderlands.pdf"
)

for entry in "${FIXTURE_MAP[@]}"; do
    asset_name="${entry%%|*}"
    local_name="${entry##*|}"
    dest_file="${DEST_DIR}/${local_name}"

    if [[ -f "${dest_file}" ]]; then
        echo "  Already present, skipping: ${local_name}"
        continue
    fi

    echo "  Downloading: ${asset_name}"
    # Download to a temp dir then rename to avoid partial overwrites.
    tmp_dir=$(mktemp -d)
    gh release download "${FIXTURES_TAG}" \
        --repo "${FIXTURES_REPO}" \
        --pattern "${asset_name}" \
        --dir "${tmp_dir}"

    # Rename from dot-separated asset name to spaced local name.
    downloaded="${tmp_dir}/${asset_name}"
    if [[ -f "${downloaded}" ]]; then
        mv "${downloaded}" "${dest_file}"
        rm -rf "${tmp_dir}"
        echo "  Saved as: ${local_name}"
    else
        rm -rf "${tmp_dir}"
        echo "Error: expected file not found after download: ${asset_name}" >&2
        exit 1
    fi
done

echo "Private fixtures downloaded successfully."
