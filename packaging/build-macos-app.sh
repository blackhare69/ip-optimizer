#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${ROOT_DIR}/build"
DIST_DIR="${ROOT_DIR}/dist"
STAGING_DIR="${BUILD_DIR}/macos-dmg"
APP_PATH="${DIST_DIR}/IPOptimizer.app"
DMG_PATH="${DIST_DIR}/IP-Optimizer-macOS-Intel.dmg"

cd "${ROOT_DIR}"
rm -rf "${BUILD_DIR}" "${DIST_DIR}"
mkdir -p "${BUILD_DIR}" "${DIST_DIR}"

python -m PyInstaller \
  --name IPOptimizer \
  --windowed \
  --onedir \
  --noconfirm \
  --clean \
  --target-arch x86_64 \
  --osx-bundle-identifier com.blackhare69.ipoptimizer \
  --distpath "${DIST_DIR}" \
  --workpath "${BUILD_DIR}/pyinstaller" \
  --specpath "${BUILD_DIR}" \
  "${ROOT_DIR}/main.py"

test -d "${APP_PATH}"
mkdir -p "${STAGING_DIR}"
cp -R "${APP_PATH}" "${STAGING_DIR}/"
ln -s /Applications "${STAGING_DIR}/Applications"

hdiutil create \
  -volname "IP Optimizer" \
  -srcfolder "${STAGING_DIR}" \
  -ov \
  -format UDZO \
  "${DMG_PATH}"

test -s "${DMG_PATH}"
echo "Created ${APP_PATH}"
echo "Created ${DMG_PATH}"

