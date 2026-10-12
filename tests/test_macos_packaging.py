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

    def test_macos_workflow_contract(self):
        workflow_path = PROJECT_ROOT / ".github" / "workflows" / "macos-intel.yml"
        self.assertTrue(workflow_path.exists(), "macOS Intel workflow is missing")

        workflow = workflow_path.read_text(encoding="utf-8")
        required_tokens = (
            "runs-on: macos-15-intel",
            "python-version: '3.12'",
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
            "未签名",
            "未公证",
            "~/Library/Application Support/ip-optimizer",
        )
        for token in required_tokens:
            with self.subTest(token=token):
                self.assertIn(token, readme)


if __name__ == "__main__":
    unittest.main()

