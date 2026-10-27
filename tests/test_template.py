import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'skills/paper-intake/scripts'
spec = importlib.util.spec_from_file_location('init_vault', SCRIPTS / 'init_vault.py')
init = importlib.util.module_from_spec(spec)
spec.loader.exec_module(init)


class TemplateTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.vault = self.root / '阅读工作台'

    def tearDown(self):
        self.temp.cleanup()

    def test_create_empty_reading_vault_and_refresh(self):
        init.create_vault(self.vault)
        self.assertEqual(sorted(p.name for p in self.vault.iterdir() if not p.name.startswith('.')),
                         ['00 收件箱', '10 文献'])
        self.assertFalse(list(self.vault.rglob('*.pdf')))
        self.assertFalse(list(self.vault.rglob('.gitkeep')))
        self.assertFalse(list(self.vault.rglob('data.json')))
        result = subprocess.run([sys.executable, str(SCRIPTS / 'intake.py'),
                                 '--vault', str(self.vault), 'refresh'],
                                env={**os.environ, 'DEEPPAPERNOTE_CONFIG_PATH': str(self.root / 'missing.json')},
                                capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(result.stdout)['papers'], 0)
        self.assertFalse((self.vault / '99 系统与附件').exists())
        self.assertNotIn('关联项目', (self.vault / '10 文献/文献目录.md').read_text())

    def test_no_existing_folder_overwrite(self):
        self.vault.mkdir()
        important = self.vault / '用户笔记.md'
        important.write_text('keep')
        with self.assertRaises(ValueError):
            init.create_vault(self.vault)
        self.assertEqual(important.read_text(), 'keep')

    def test_no_symlink_overwrite(self):
        self.vault.symlink_to(self.root / 'missing-target')
        with self.assertRaises(ValueError):
            init.create_vault(self.vault)
        self.assertTrue(self.vault.is_symlink())

    def test_ready_to_open_download(self):
        with zipfile.ZipFile(ROOT / 'downloads/文献阅读工作台.zip') as archive:
            self.assertIsNone(archive.testzip())
            archive.extractall(self.root)
        vault = self.root / '文献阅读工作台'
        self.assertTrue((vault / '.obsidian/plugins/academic-library-helper/main.js').is_file())
        self.assertEqual(json.loads((vault / '10 文献/阅读工具/论文入库登记.json').read_text())['papers'], {})
        for folder in ['PDF', '阅读笔记', 'AI辅助阅读']:
            self.assertTrue((vault / '10 文献' / folder).is_dir())
        self.assertFalse(list(vault.rglob('*.pdf')))

    def test_visible_source_distribution(self):
        # Simulate a web upload that skips every hidden file or directory.
        copy = self.root / 'web-upload'
        shutil.copytree(ROOT / 'skills', copy / 'skills',
                        ignore=lambda directory, names: [name for name in names if name.startswith('.') or name == '__pycache__'])
        subprocess.run([sys.executable, str(copy / 'skills/paper-intake/scripts/init_vault.py'),
                        '--vault', str(self.vault)], capture_output=True, text=True, check=True)
        self.assertTrue((self.vault / '.obsidian/plugins/academic-library-helper/main.js').is_file())
        self.assertTrue((self.vault / '10 文献/PDF').is_dir())

    @unittest.skipUnless(shutil.which('node'), 'Node.js is needed for the plugin API mock')
    def test_plugin_in_isolated_vault(self):
        init.create_vault(self.vault)
        result = subprocess.run(['node', str(ROOT / 'tests/plugin_mock.js'), str(self.vault)],
                                env={**os.environ, 'TEST_PYTHON': sys.executable},
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('PASS:', result.stdout)


if __name__ == '__main__':
    unittest.main()
