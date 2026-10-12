import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils import paths


class TestLinuxDataRoots(unittest.TestCase):
    def test_linux_prefers_xdg_data_home(self):
        home = Path("/home/tester")
        xdg_data_home = home / ".local" / "custom-data"

        with (
            patch.object(paths.sys, "platform", "linux"),
            patch.object(paths.Path, "home", return_value=home),
            patch.dict(
                os.environ,
                {"XDG_DATA_HOME": str(xdg_data_home)},
                clear=True,
            ),
        ):
            roots = paths._candidate_roots()

        self.assertEqual(roots[0], xdg_data_home / "ip-optimizer")
        self.assertNotIn(home / "Documents" / paths.FALLBACK_DIR_NAME, roots)

    def test_linux_uses_standard_xdg_data_home_when_unset(self):
        home = Path("/home/tester")

        with (
            patch.object(paths.sys, "platform", "linux"),
            patch.object(paths.Path, "home", return_value=home),
            patch.dict(os.environ, {}, clear=True),
        ):
            roots = paths._candidate_roots()

        self.assertEqual(roots[0], home / ".local" / "share" / "ip-optimizer")

    def test_linux_data_root_uses_first_writable_user_directory(self):
        home = Path("/home/tester")
        expected = home / ".local" / "share" / "ip-optimizer"

        with (
            patch.object(paths.sys, "platform", "linux"),
            patch.object(paths.Path, "home", return_value=home),
            patch.dict(os.environ, {}, clear=True),
            patch.object(paths, "_is_writable", return_value=True),
            patch.object(paths, "install_root", return_value=Path("/opt/IPOptimizer")),
        ):
            old_root = paths._resolved_root
            paths._resolved_root = None
            try:
                actual = paths.data_root()
            finally:
                paths._resolved_root = old_root

        self.assertEqual(actual, expected)


class TestMacOSDataRoots(unittest.TestCase):
    def test_macos_prefers_application_support_directory(self):
        home = Path("/Users/tester")
        install = Path("/Applications/IPOptimizer.app/Contents/MacOS")

        with (
            patch.object(paths.sys, "platform", "darwin"),
            patch.object(paths.Path, "home", return_value=home),
            patch.dict(os.environ, {}, clear=True),
            patch.object(paths, "install_root", return_value=install),
        ):
            roots = paths._candidate_roots()

        self.assertEqual(
            roots,
            [
                home / "Library" / "Application Support" / paths.APP_DIR_NAME,
                home / "Documents" / paths.FALLBACK_DIR_NAME,
            ],
        )

    def test_macos_uses_explicit_xdg_directory_as_second_candidate(self):
        home = Path("/Users/tester")
        xdg_data_home = Path("/tmp/xdg-data")
        install = Path("/Applications/IPOptimizer.app/Contents/MacOS")

        with (
            patch.object(paths.sys, "platform", "darwin"),
            patch.object(paths.Path, "home", return_value=home),
            patch.dict(os.environ, {"XDG_DATA_HOME": str(xdg_data_home)}, clear=True),
            patch.object(paths, "install_root", return_value=install),
        ):
            roots = paths._candidate_roots()

        self.assertEqual(
            roots,
            [
                home / "Library" / "Application Support" / paths.APP_DIR_NAME,
                xdg_data_home / paths.APP_DIR_NAME,
                home / "Documents" / paths.FALLBACK_DIR_NAME,
            ],
        )

    def test_macos_data_root_never_uses_install_root_as_fallback(self):
        home = Path("/Users/tester")
        install = Path("/Applications/IPOptimizer.app/Contents/MacOS")
        expected = home / "Documents" / paths.FALLBACK_DIR_NAME

        with (
            patch.object(paths.sys, "platform", "darwin"),
            patch.object(paths.Path, "home", return_value=home),
            patch.dict(os.environ, {}, clear=True),
            patch.object(paths, "_is_writable", return_value=False),
            patch.object(paths, "install_root", return_value=install),
        ):
            old_root = paths._resolved_root
            paths._resolved_root = None
            try:
                actual = paths.data_root()
            finally:
                paths._resolved_root = old_root

        self.assertEqual(actual, expected)

    def test_macos_data_root_uses_first_writable_directory(self):
        home = Path("/Users/tester")
        xdg_data_home = Path("/tmp/xdg-data")
        install = Path("/Applications/IPOptimizer.app/Contents/MacOS")
        expected = xdg_data_home / paths.APP_DIR_NAME

        with (
            patch.object(paths.sys, "platform", "darwin"),
            patch.object(paths.Path, "home", return_value=home),
            patch.dict(os.environ, {"XDG_DATA_HOME": str(xdg_data_home)}, clear=True),
            patch.object(paths, "_is_writable", side_effect=[False, True]),
            patch.object(paths, "install_root", return_value=install),
        ):
            old_root = paths._resolved_root
            paths._resolved_root = None
            try:
                actual = paths.data_root()
            finally:
                paths._resolved_root = old_root

        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
