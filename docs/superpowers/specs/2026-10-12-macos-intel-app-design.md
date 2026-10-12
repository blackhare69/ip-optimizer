# macOS Intel 应用发布设计

## 目标

为现有 IP 优选器增加一个可在 Intel Mac（x86_64）上运行的 macOS 应用，并通过 GitHub Actions 自动构建和发布 `IP-Optimizer-macOS-Intel.dmg`。

## 已确认的范围

- 保留现有 PySide6 界面、测速流程、评分、稳定性复测和导出功能。
- 目标架构为 macOS Intel `x86_64`，不把 Apple Silicon 原生包混入本次交付。
- 用户下载一个 `.dmg`，打开后将应用拖入“应用程序”目录即可使用。
- 首版不配置 Apple Developer 证书、不做 notarization；首次打开时可能需要在 Finder 中右键应用并选择“打开”，macOS 15+ 还可能需要到“系统设置 → 隐私与安全性”点击“仍要打开”。
- 现有 Windows 和 Linux 发布流程继续保留。
- macOS 运行数据使用用户可写目录，不写入只读的 `.app` 包内部。
- 构建目标为 macOS 14.4 或更高版本，使用 Intel `x86_64` 架构的 PySide6 6.12.0 依赖。

## 方案

GitHub Actions 使用 Intel macOS runner `macos-15-intel`。工作流安装 Python 3.12、项目依赖和 PyInstaller，运行完整单元测试，然后使用 PyInstaller 的 `--windowed`、`--target-arch x86_64` 和固定 bundle identifier 生成 `.app`。随后使用系统自带的 `hdiutil create` 将 `.app` 制作成压缩 DMG，并上传为 Actions artifact；在 `mac-v*` 发布分支或标签上，将 DMG 附加到 GitHub Release。

选择 DMG 而不是只上传 ZIP，是为了让 Linux Mint 用户之外的 macOS 用户也能按常见的拖拽安装方式使用。选择未签名发布，是因为签名和 notarization 需要 Apple Developer 账号、证书和 GitHub Secrets，超出本次需求；工作流会在说明中明确这一点。

## 组件与文件职责

- `utils/paths.py`：补充 macOS 数据目录候选路径，优先使用 `~/Library/Application Support/ip-optimizer`，确保日志和导出文件不写入只读 App bundle。
- `tests/test_paths.py`：增加 macOS 路径行为测试，并保持现有 Windows/Linux 路径测试。
- `packaging/build-macos-app.sh`：在 macOS runner 上执行 PyInstaller，生成 `dist/IPOptimizer.app`，并用 `hdiutil` 生成 `dist/IP-Optimizer-macOS-Intel.dmg`。
- `Contents/Info.plist`：由 PyInstaller 根据命令行参数生成应用元数据，首版不额外维护静态 plist 文件，也不包含签名信息。
- 应用图标：首版允许使用 PyInstaller 默认图标，不新增独立 ICNS 资源；这不影响功能交付。
- `.github/workflows/macos-intel.yml`：负责 macOS Intel 测试、构建、artifact 上传和 Release 发布。
- `README.md`：增加 macOS Intel 下载、首次打开和数据目录说明，并保留 Windows/Linux 下载说明。

## 数据流

```text
macos-15-intel runner
    -> checkout
    -> Python 3.12 + requirements.txt + PySide6==6.12.0 + PyInstaller
    -> unittest 全量测试
    -> PyInstaller x86_64 .app
    -> hdiutil 压缩 DMG
    -> Actions artifact
    -> mac-v* 发布分支或标签
    -> GitHub Release 附件
```

## 路径策略

macOS 运行时按以下顺序选择可写数据目录：

1. `~/Library/Application Support/ip-optimizer`；
2. `XDG_DATA_HOME/ip-optimizer`（仅作为显式环境变量覆盖，便于测试和兼容受控环境）；
3. `~/Documents/IPOptimizer`。

路径探测仍通过创建和删除临时文件验证可写性。`.app` 内部资源只读或无法持久化时，程序必须回退到用户目录，不能把数据写入可替换的 `.app` 包，也不能因为日志或 CSV 导出失败而启动失败。

## 错误处理与用户提示

- PyInstaller、依赖安装或单元测试失败时，Actions 直接失败，不上传伪造的 DMG。
- `hdiutil` 失败时，Actions 直接失败，并保留构建日志。
- 未签名导致 macOS Gatekeeper 阻止首次打开时，README 提供 Finder“右键应用 -> 打开”的明确步骤；macOS 15+ 同时提供“系统设置 → 隐私与安全性 -> 仍要打开”，不指导用户关闭系统安全设置。
- 用户没有写入应用目录权限时，日志和导出结果仍写入用户目录。
- Release 发布只在 `mac-v*` 触发；普通 `master` 推送只执行测试和构建，不创建正式 Release。

## 测试与验收

- 先为 macOS 路径规则添加失败测试，再修改 `utils/paths.py`，完成 TDD 的 RED -> GREEN 循环。
- 本地运行完整 Python 单元测试和 `compileall`。
- GitHub Actions 在 `macos-15-intel` 上运行完整单元测试。
- 工作流检查生成文件确实存在，且 DMG 文件名为 `IP-Optimizer-macOS-Intel.dmg`。
- Release 验收包含一个同名 DMG 资产；构建日志显示 runner 为 Intel，PyInstaller 目标为 `x86_64`。
- 不声称已完成 Apple 签名、公证或在真实 Intel Mac 上的视觉启动验证，除非有对应证据。

## 非目标

- 本次不制作 Apple Silicon 原生包或 universal2 包。
- 本次不引入自动更新、安装器脚本、系统网络设置修改或后台服务。
- 本次不改变测速算法、评分公式、界面布局或原有 Windows/Linux 功能。
- 本次不添加 Apple Developer 证书、签名密钥或公证凭据。
