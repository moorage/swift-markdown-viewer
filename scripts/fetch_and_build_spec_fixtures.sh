#!/bin/zsh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TMP_DIR="${ROOT_DIR}/tmp"
COMMONMARK_DIR="${TMP_DIR}/third_party/commonmark-spec"
GFM_DIR="${TMP_DIR}/third_party/cmark-gfm"
COMMONMARK_JSON="${TMP_DIR}/commonmark-tests.json"
GFM_JSON="${TMP_DIR}/gfm-tests.json"
OUTPUT_DIR="${TMP_DIR}/spec-fixtures"

[[ -d "${COMMONMARK_DIR}" ]] || {
  echo "Missing CommonMark checkout at ${COMMONMARK_DIR}" >&2
  exit 1
}

[[ -d "${GFM_DIR}" ]] || {
  echo "Missing GFM checkout at ${GFM_DIR}" >&2
  exit 1
}

mkdir -p "${TMP_DIR}"

(
  cd "${COMMONMARK_DIR}"
  python3 test/spec_tests.py --dump-tests < spec.txt > "${COMMONMARK_JSON}"
)

(
  cd "${GFM_DIR}"
  python3 test/spec_tests.py --dump-tests --spec test/spec.txt > "${GFM_JSON}"
)

python3 "${ROOT_DIR}/scripts/build_markdown_fixtures.py" \
  "${COMMONMARK_JSON}" \
  "${GFM_JSON}" \
  "${OUTPUT_DIR}"

echo "Done. Fixtures written to ${OUTPUT_DIR}"
