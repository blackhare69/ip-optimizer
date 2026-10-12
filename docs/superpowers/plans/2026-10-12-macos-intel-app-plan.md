# macOS Intel 应用发布 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为现有 IP 优选器增加 Intel Mac `x86_64` 的 `.app`/`.dmg` 构建，并在 `mac-v*` 发布分支或标签上自动上传 GitHub Release。

**Architecture:** 复用现有 PySide6 程序，不改测速和界面逻辑；仅扩展 macOS 用户数据路径，并新增独立的 macOS 打包脚本和 GitHub Actions 工作流。PyInstaller 在 `macos-15-intel` runner 上生成 `IPOptimizer.app`，`hdiutil` 将带有 `/Applications` 快捷方式的暂存目录压成 DMG。

**Tech Stack:** Python 3.12, PySide6, unittest, PyInstaller, macOS `hdiutil`, GitHub Actions。

**Spec:** `docs/superpowers/specs/2026-10-12-macos-intel-app-design.md`

## Global Constraints

- 目标架构固定为 macOS Intel `x86_64`；不生成 Apple Silicon 原生包或 universal2 包。
- 发布文件名固定为 `IP-Optimizer-macOS-Intel.dmg`。
- macOS 数据目录优先为 `~/Library/Application Support/ip-optimizer`，依次回退到显式 `XDG_DATA_HOME/ip-optimizer` 和 `~/Documents/IPOptimizer`，不能把日志或导出文件写入只读 App bundle。
- macOS 构建目标为 14.4 或更高版本，工作流固定使用 `PySide6==6.12.0`。
- 保留 Windows/Linux 发布流程、现有 UI、测速算法、评分公式、稳定性复测和导出行为。
- 首版不使用 Apple Developer 证书、签名密钥或 notarization。
- 普通 `master` 推送只测试和构建；`mac-v*` 发布分支或标签才创建 Release。

## Review Focus

- `darwin` 环境下 `.app` 不可写：测试必须证明程序优先落到用户目录。
- 显式设置 `XDG_DATA_HOME` 的 macOS 环境：测试必须证明它作为第二候选路径生效。
- PyInstaller 输出架构错误：工作流必须用 `lipo -info` 检查 `x86_64`。
- DMG 暂存目录缺少 `/Applications` 快捷方式：构建脚本必须创建并检查该链接。
- 未签名应用首次启动：README 必须说明右键“打开”；macOS 15+ 还要说明“系统设置 → 隐私与安全性 → 仍要打开”，不得指导用户关闭系统安全保护。

---

### Task 1: Add macOS data-path behavior with TDD

**Files:**
- Modify: `utils/paths.py:_candidate_roots`
- Modify: `tests/test_paths.py`

**Interfaces:**
- Consumes: existing `install_root()`, `_is_writable()`, `data_root()` and `APP_DIR_NAME`.
- Produces: when `sys.platform == "darwin"`, candidates ordered as `~/Library/Application Support/ip-optimizer`, optional `XDG_DATA_HOME/ip-optimizer`, and `~/Documents/IPOptimizer`; `install_root()` is never used for persistent macOS data.

- [ ] **Step 1: Write the failing tests**

  Add tests named `test_macos_prefers_application_support_directory`, `test_macos_uses_explicit_xdg_directory_as_second_candidate`, and `test_macos_data_root_uses_first_writable_directory`. Patch only `paths.sys.platform`, `paths.Path.home`, `os.environ`, `paths._is_writable`, and `paths.install_root`; assert exact `Path` values and preserve existing Linux tests.

- [ ] **Step 2: Run the macOS path tests to verify RED**

  Run `python -m unittest tests.test_paths -v`. Expected: the new tests fail because the current implementation treats `darwin` as Windows.

- [ ] **Step 3: Implement the minimal macOS branch**

  In `_candidate_roots()`, add a `sys.platform == "darwin"` branch before the Windows fallback. Build the standard Application Support path first, append the explicit XDG path only when present and not identical, then append `~/Documents/IPOptimizer`; make `data_root()` use the same persistent user path if every probe fails.

- [ ] **Step 4: Run the focused and full tests**

  Run `python -m unittest tests.test_paths -v`, then `python -m unittest discover -s tests -v`. Expected: all focused tests and the complete suite pass.

- [ ] **Step 5: Commit**

  Commit with `feat: add macOS application support data paths`.

### Task 2: Build the Intel macOS application and DMG

**Files:**
- Create: `packaging/build-macos-app.sh`
- Create: `tests/test_macos_packaging.py`

**Interfaces:**
- Consumes: `main.py`, `requirements.txt`, PyInstaller, `packaging/ip-optimizer.svg` only if an icon conversion is available; otherwise PyInstaller's default icon.
- Produces: `dist/IPOptimizer.app` and `dist/IP-Optimizer-macOS-Intel.dmg`.

- [ ] **Step 1: Write a shell-level contract check before implementation**

  Add `test_macos_build_script_contract` to `tests/test_macos_packaging.py`. It must name the required output path and verify the build script contains `--target-arch x86_64`, `hdiutil create`, and an `/Applications` symlink. The check must fail because the script does not yet exist.

- [ ] **Step 2: Run the contract check to verify RED**

  Run the focused check and confirm it reports the missing build script or required tokens.

- [ ] **Step 3: Implement `packaging/build-macos-app.sh`**

  Use `set -euo pipefail`, resolve the repository root, clear only `${ROOT_DIR}/build` and `${ROOT_DIR}/dist`, run PyInstaller with `--windowed --onedir --clean --noconfirm --target-arch x86_64 --osx-bundle-identifier com.blackhare69.ipoptimizer`, stage the app beside a symlink named `Applications` pointing to `/Applications`, and run `hdiutil create -format UDZO` to produce the fixed DMG filename. End with an explicit existence and non-zero-size check.

- [ ] **Step 4: Validate script syntax and static contract**

  On macOS CI, run `bash -n packaging/build-macos-app.sh`, `test -x packaging/build-macos-app.sh`, and the output checks. On the current Windows host, only inspect the script and use PowerShell-safe text checks; do not claim macOS execution locally.

- [ ] **Step 5: Commit**

  Commit with `build: add Intel macOS app and dmg packaging`.

### Task 3: Add the Intel macOS GitHub Actions workflow

**Files:**
- Create: `.github/workflows/macos-intel.yml`
- Modify: `tests/test_macos_packaging.py`

**Interfaces:**
- Consumes: Task 1 path behavior, Task 2 build script, existing `tests` suite, and GitHub Actions `contents: write` permission.
- Produces: a successful Intel runner build, an artifact named `IP-Optimizer-macOS-Intel`, and a Release asset on `mac-v*` refs.

- [ ] **Step 1: Write workflow contract assertions**

  Add `test_macos_workflow_contract` to `tests/test_macos_packaging.py`. It must check the workflow contains `runs-on: macos-15-intel`, Python 3.12 setup, the full unittest command, `bash packaging/build-macos-app.sh`, `lipo -info`, artifact upload, and the `mac-v*` release condition. The assertions must fail before the workflow exists.

- [ ] **Step 2: Run the assertions to verify RED**

  Run the focused workflow contract check and confirm the expected missing-file failure.

- [ ] **Step 3: Implement the workflow**

  Trigger on pull requests, `master`, `mac-v*` branches/tags, and manual dispatch. Install dependencies, run all tests, build the DMG, verify the app executable reports `x86_64`, verify the DMG is non-empty, upload the artifact, and run `gh release create "$GITHUB_REF_NAME" ... --target "$GITHUB_SHA"` only for `refs/heads/mac-v*` or `refs/tags/mac-v*`.

- [ ] **Step 4: Validate the workflow locally**

  Run YAML parsing or a repository-safe static validation available on the runner, plus `git diff --check`. The definitive build validation occurs on GitHub's `macos-15-intel` runner.

- [ ] **Step 5: Commit**

  Commit with `ci: build and publish Intel macOS dmg`.

### Task 4: Document macOS download and first launch

**Files:**
- Modify: `README.md`
- Modify: `tests/test_macos_packaging.py`

**Interfaces:**
- Consumes: `IP-Optimizer-macOS-Intel.dmg`, the public Releases URL, and the macOS path behavior from Task 1.
- Produces: a clear macOS Intel download section with no claim of signing or notarization.

- [ ] **Step 1: Add documentation checks**

  Add `test_readme_documents_macos_intel_release` to `tests/test_macos_packaging.py`. It must assert the exact DMG filename, Intel/x86_64 wording, macOS 14.4+ requirement, drag-to-Applications instructions, right-click “打开” guidance, macOS 15+ “系统设置 → 隐私与安全性” and “仍要打开” guidance, and `~/Library/Application Support/ip-optimizer` data path.

- [ ] **Step 2: Run documentation checks to verify RED**

  Confirm the current README lacks the macOS-specific content.

- [ ] **Step 3: Update README**

  Add macOS Intel beside the Linux and Windows download instructions, state that the first launch may require Finder’s right-click “打开”, and explain that the package is unsigned/not notarized. Keep existing platform instructions unchanged.

- [ ] **Step 4: Run documentation checks to verify GREEN**

  Run the focused assertions and `git diff --check`.

- [ ] **Step 5: Commit**

  Commit with `docs: add Intel macOS download instructions`.

### Task 5: Full verification and release

**Files:**
- Verify: all files changed by Tasks 1–4, including `tests/test_macos_packaging.py`, and the GitHub Actions workflow run.

- [ ] **Step 1: Run the complete local verification**

  Run `python -m unittest discover -s tests -v`, `python -m compileall -q core gui utils main.py tests`, and repository text checks. Record the test count and exit codes.

- [ ] **Step 2: Push the implementation to the fork**

  Update `master` with the verified commits through the authenticated GitHub repository connection; do not modify the original upstream repository.

- [ ] **Step 3: Trigger a macOS release build**

  Create or update `mac-v1.0.0` from the verified commit so the existing branch-trigger release workaround produces a release asset without requiring an unavailable direct tag API.

- [ ] **Step 4: Verify the GitHub Actions run**

  Confirm the macOS job ran on `macos-15-intel`, tests passed, `lipo -info` reported `x86_64`, DMG creation succeeded, and the artifact upload succeeded.

- [ ] **Step 5: Verify the Release asset**

  Confirm `IP-Optimizer-macOS-Intel.dmg` appears on the `mac-v1.0.0` Release. Report that signing/notarization and real Intel Mac GUI launch remain unverified unless separately tested.

## Review Focus Mapping

- macOS user path ordering and read-only bundle fallback: Task 1 tests.
- Explicit XDG override behavior: Task 1 tests.
- x86_64 binary architecture: Task 3 `lipo -info` assertion.
- DMG drag-to-Applications layout: Task 2 script contract and Task 3 build.
- Gatekeeper first-launch guidance: Task 4 documentation assertions.
