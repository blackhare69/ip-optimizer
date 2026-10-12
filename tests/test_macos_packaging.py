import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestMacOSPackagingContracts(unittest.TestCase):
    def test_macos_build_script_contract(self):
        script_path = PROJECT_ROOT / "packaging" / "build-macos-app.sh"
        self.assertTrue(script_path.exists(), "macOS build script is missing")

        script = script_path.read_text(encoding="utf-8")
        required_tokens = (
            "IPOptimizer.app",
            "IP-Optimizer-macOS-Intel.dmg",
            "--target-arch x86_64",
            "hdiutil create",
            "ln -s /Applications",
            "test -s",
        )
        for token in required_tokens:
            with self.subTest(token=token):
                self.assertIn(token, script)

    def test_macos_build_script_uses_unix_line_endings(self):
        script_path = PROJECT_ROOT / "packaging" / "build-macos-app.sh"
        script_bytes = script_path.read_bytes()
        self.assertNotIn(b"\r\n", script_bytes)

    def test_macos_workflow_contract(self):
        workflow_path = PROJECT_ROOT / ".github" / "workflows" / "macos-intel.yml"
        self.assertTrue(workflow_path.exists(), "macOS Intel workflow is missing")

        workflow = workflow_path.read_text(encoding="utf-8")
        required_tokens = (
            "runs-on: macos-15-intel",
            "python-version: '3.12'",
            'PySide6==6.12.0',
            'MACOSX_DEPLOYMENT_TARGET: "14.4"',
            "python -m unittest discover -s tests -v",
            "bash packaging/build-macos-app.sh",
            "lipo -info",
            "actions/upload-artifact@v4",
            "IP-Optimizer-macOS-Intel",
            "startsWith(github.ref, 'refs/heads/mac-v')",
            "startsWith(github.ref, 'refs/tags/mac-v')",
            "gh release create",
        )
        for token in required_tokens:
            with self.subTest(token=token):
                self.assertIn(token, workflow)

    def test_readme_documents_macos_intel_release(self):
        readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
        required_tokens = (
            "IP-Optimizer-macOS-Intel.dmg",
            "macOS Intel",
            "x86_64",
            "拖入“应用程序”",
            "右键应用并选择“打开”",
            "macOS 14.4 或更高版本",
            "系统设置 → 隐私与安全性",
            "仍要打开",
            "未签名",
            "未公证",
            "~/Library/Application Support/ip-optimizer",
        )
        for token in required_tokens:
            with self.subTest(token=token):
                self.assertIn(token, readme)

    def test_macos_build_script_has_unix_eol_policy(self):
        attributes_path = PROJECT_ROOT / ".gitattributes"
        self.assertTrue(attributes_path.exists(), ".gitattributes is missing")

        attributes = attributes_path.read_text(encoding="utf-8")
        self.assertIn(
            "packaging/build-macos-app.sh text eol=lf",
            attributes,
        )


if __name__ == "__main__":
    unittest.main()
