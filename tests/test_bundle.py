import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


BUNDLE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('firmware', BUNDLE / 'tools/clean-napi-firmware.py')
firmware = importlib.util.module_from_spec(spec)
spec.loader.exec_module(firmware)


class BundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='napi-bundle-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'armbian build'
        for folder in ['config/boards', 'extensions']:
            (self.root / folder).mkdir(parents=True, exist_ok=True)
        self.board = self.root / 'config/boards/napi-c.csc'
        self.board.write_text('BOARD_NAME="NAPI-C"\n')
        compile_script = self.root / 'compile.sh'
        compile_script.write_text(
            '#!/bin/bash\nset -eu\n'
            'source userpatches/config-napi-minimal.conf\n'
            'printf "%s\\n" "$*" "$BOARD $RELEASE $BUILD_MINIMAL $INSTALL_HEADERS $ENABLE_EXTENSIONS"\n'
        )
        compile_script.chmod(0o755)

    def install(self, *args):
        return subprocess.run(
            ['bash', str(BUNDLE / 'install.sh'), str(self.root), *args],
            capture_output=True, text=True,
        )

    def test_install_and_repeat_preserve_board(self):
        self.assertEqual(self.install().returncode, 0)
        self.assertEqual(self.install().returncode, 0)
        self.assertEqual(self.board.read_text(), 'BOARD_NAME="NAPI-C"\n')
        self.assertEqual(
            (self.root / 'config/cleanup/napi-c.conf').read_bytes(),
            (BUNDLE / 'config/cleanup/napi-c.conf').read_bytes(),
        )

    def test_conflict_prevents_partial_install(self):
        conflict = self.root / 'tools/clean-napi-firmware.py'
        conflict.parent.mkdir()
        conflict.write_text('custom file\n')
        result = self.install()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(conflict.read_text(), 'custom file\n')
        self.assertFalse((self.root / 'config/cleanup').exists())

    def test_force_preserves_backup(self):
        self.assertEqual(self.install().returncode, 0)
        config = self.root / 'config/cleanup/napi-c.conf'
        config.write_text('custom config\n')
        self.assertEqual(self.install('--force').returncode, 0)
        backups = list(config.parent.glob('napi-c.conf.bak.*'))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(), 'custom config\n')

    def test_rejects_destination_escape(self):
        outside = Path(self.temp.name) / 'outside'
        outside.mkdir()
        (self.root / 'tools').symlink_to(outside, target_is_directory=True)
        self.assertNotEqual(self.install().returncode, 0)
        self.assertFalse(list(outside.iterdir()))

    def test_build_uses_installed_profile(self):
        result = subprocess.run(
            ['bash', str(BUNDLE / 'build.sh'), str(self.root)],
            env=dict(os.environ, REVISION='26.02.0-test'), capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('build napi-minimal REVISION=26.02.0-test', result.stdout)
        self.assertIn('napi-c noble yes no napi-minimal', result.stdout)

    def test_firmware_pruning_preserves_symlink_target(self):
        image = Path(self.temp.name) / 'image'
        (image / 'etc').mkdir(parents=True)
        (image / 'etc/armbian-release').touch()
        fw = image / 'usr/lib/firmware'
        for folder in ['rtl_nic', 'realtek', 'wifi']:
            (fw / folder).mkdir(parents=True)
        (fw / 'rtl_nic/usb.fw').symlink_to('../realtek/usb.fw')
        (fw / 'realtek/usb.fw').write_bytes(b'keep')
        unwanted = fw / 'wifi/radio.fw'
        unwanted.write_bytes(b'remove')
        firmware.clean(image, False, ['rtl_nic/*'])
        self.assertTrue(unwanted.exists())
        firmware.clean(image, True, ['rtl_nic/*'])
        self.assertFalse(unwanted.exists())
        self.assertEqual((fw / 'rtl_nic/usb.fw').read_bytes(), b'keep')
        firmware.clean(image, True, ['rtl_nic/*'])
        (fw / 'rtl_nic/escape.fw').symlink_to('/etc/passwd')
        with self.assertRaises(ValueError):
            firmware.clean(image, True, ['rtl_nic/*'])


if __name__ == '__main__':
    unittest.main()
