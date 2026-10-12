#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${ROOT_DIR}/build"
DIST_DIR="${ROOT_DIR}/dist"
APP_DIR="${BUILD_DIR}/AppDir"
APPIMAGETOOL="${APPIMAGETOOL:-appimagetool}"

cd "${ROOT_DIR}"
rm -rf "${BUILD_DIR}" "${DIST_DIR}"
mkdir -p "${BUILD_DIR}" "${DIST_DIR}"

python -m PyInstaller \
  --name IPOptimizer \
  --windowed \
  --noconfirm \
  --clean \
  --onedir \
  --distpath "${DIST_DIR}" \
  --workpath "${BUILD_DIR}/pyinstaller" \
  --specpath "${BUILD_DIR}" \
  "${ROOT_DIR}/main.py"

mkdir -p \
  "${APP_DIR}/usr/bin" \
  "${APP_DIR}/usr/share/applications" \
  "${APP_DIR}/usr/share/icons/hicolor/scalable/apps"

cp -a "${DIST_DIR}/IPOptimizer/." "${APP_DIR}/usr/bin/"
cp "${ROOT_DIR}/packaging/ip-optimizer.desktop" "${APP_DIR}/"
cp "${ROOT_DIR}/packaging/ip-optimizer.desktop" "${APP_DIR}/usr/share/applications/"
cp "${ROOT_DIR}/packaging/AppRun" "${APP_DIR}/"
cp "${ROOT_DIR}/packaging/ip-optimizer.svg" \
  "${APP_DIR}/ip-optimizer.svg"
cp "${ROOT_DIR}/packaging/ip-optimizer.svg" \
  "${APP_DIR}/usr/share/icons/hicolor/scalable/apps/ip-optimizer.svg"
chmod +x "${APP_DIR}/AppRun" "${APP_DIR}/usr/bin/IPOptimizer"

"${APPIMAGETOOL}" "${APP_DIR}" "${DIST_DIR}/IP-Optimizer-Linux-x86_64.AppImage"
echo "Created ${DIST_DIR}/IP-Optimizer-Linux-x86_64.AppImage"

