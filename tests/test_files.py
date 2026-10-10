import importlib.util
from pathlib import Path
import tempfile
import os
import subprocess
import unittest

spec = importlib.util.spec_from_file_location('files', Path(__file__).resolve().parents[1] / 'tools/clean-napi-files.py')
files = importlib.util.module_from_spec(spec)
spec.loader.exec_module(files)


class FileTests(unittest.TestCase):
    def test_keep_licenses_examples_and_board_tree(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'etc').mkdir()
            (root / 'etc/armbian-release').touch()
            doc = root / 'usr/share/doc/pkg'
            (doc / 'examples').mkdir(parents=True)
            for name in ['copyright', 'manual.txt', 'examples/config']:
                (doc / name).write_text(name)
            files.clean(root, False, 'docs', ['*/copyright', '*/examples/*'])
            self.assertTrue((doc / 'manual.txt').exists())
            files.clean(root, True, 'docs', ['*/copyright', '*/examples/*'])
            self.assertFalse((doc / 'manual.txt').exists())
            self.assertTrue((doc / 'copyright').exists())
            self.assertTrue((doc / 'examples/config').exists())
            tree = root / 'usr/lib/linux-image-test/rockchip'
            tree.mkdir(parents=True)
            (tree / 'rk3308-napi-c.dtb').write_bytes(b'board')
            (tree / 'rk3588.dtb').write_bytes(b'other')
            files.clean(root, True, 'dtbs', ['rockchip/rk3308-napi-c.dtb'])
            self.assertTrue((tree / 'rk3308-napi-c.dtb').exists())
            self.assertFalse((tree / 'rk3588.dtb').exists())
            lists = root / 'var/lib/apt/lists'
            lists.mkdir(parents=True)
            (lists / 'lock').touch()
            (lists / 'index').write_text('index')
            files.clean(root, True, 'apt', [])
            self.assertTrue((lists / 'lock').exists())
            self.assertFalse((lists / 'index').exists())

    def test_late_hook_removes_restored_apt_indexes(self):
        bundle = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'etc').mkdir()
            (root / 'etc/armbian-release').touch()
            lists = root / 'var/lib/apt/lists'
            lists.mkdir(parents=True)
            (lists / 'restored-index').write_text('index')
            script = 'source "$SRC/extensions/napi-minimal.sh"; run_host_command_logged() { "$@"; }; post_post_debootstrap_tweaks__990_napi_minimal_apt_lists'
            result = subprocess.run(['bash', '-eu', '-c', script], env=dict(os.environ, SRC=str(bundle), SDCARD=str(root), BOARD='napi-c'), capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((lists / 'restored-index').exists())

    def test_kernel_hook_enables_system_tmpfs(self):
        bundle = Path(__file__).resolve().parents[1]
        script = 'source "$SRC/extensions/napi-minimal.sh"; opts_n=(); opts_y=(); custom_kernel_config__napi_minimal; printf "%s\\n" "${opts_y[@]}"'
        result = subprocess.run(['bash', '-eu', '-c', script], env=dict(os.environ, SRC=str(bundle), BOARD='napi-c'), capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        flags = result.stdout.splitlines()
        for flag in ['SHMEM', 'TMPFS', 'TMPFS_POSIX_ACL', 'SCSI', 'USB_STORAGE']:
            self.assertIn(flag, flags)

    def test_directory_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'etc').mkdir()
            (root / 'etc/armbian-release').touch()
            (root / 'usr/share').mkdir(parents=True)
            (root / 'usr/share/doc').symlink_to('/tmp')
            with self.assertRaises(ValueError):
                files.clean(root, True, 'docs', [])
