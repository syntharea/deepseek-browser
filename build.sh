#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
UPSTREAM="${1:-${UPSTREAM_DIR:-}}"

if [[ -z "${UPSTREAM}" || ! -f "${UPSTREAM}/manifest.json" ]]; then
  cat >&2 <<'EOF'
usage: ./build.sh /path/to/upstream-2.0.24_0
   or: UPSTREAM_DIR=/path/to/upstream-2.0.24_0 ./build.sh

The upstream browser-agent extension 2.0.24 is not included in this repo.
Point this script at your own local copy.
EOF
  exit 1
fi

for command in python3 ffmpeg zip; do
  command -v "${command}" >/dev/null 2>&1 || {
    echo "missing required command: ${command}" >&2
    exit 1
  }
done

python3 - <<'PY' || {
import sys
try:
    import PIL  # noqa: F401
except Exception:
    sys.exit(1)
PY
  echo "missing Python Pillow: pip install pillow" >&2
  exit 1
}

EXT="${ROOT}/work/deepseek-ext"
DIST="${ROOT}/dist"
rm -rf "${EXT}"
mkdir -p "${EXT}" "${DIST}"
cp -a "${UPSTREAM}/." "${EXT}/"
chmod -R u+w "${EXT}"

export EXT_DIR="${EXT}"
python3 "${ROOT}/tools/patch_extension.py"
python3 "${ROOT}/tools/rebrand_deepseek.py"
python3 "${ROOT}/tools/cleanup_i18n.py"
python3 "${ROOT}/tools/make_brand_assets.py"

rm -f "${DIST}/deepseek-browser-2.0.24.zip"
(cd "${EXT}" && zip -qr "${DIST}/deepseek-browser-2.0.24.zip" . -x '_metadata/*')

echo
echo "built:  ${EXT}"
echo "zip:    ${DIST}/deepseek-browser-2.0.24.zip"
echo "load:   chrome://extensions -> Developer mode -> Load unpacked -> ${EXT}"
