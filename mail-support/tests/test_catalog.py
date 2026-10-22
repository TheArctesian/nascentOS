import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('merge_catalog', ROOT / 'merge-catalog.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.mail = json.loads((ROOT / 'catalog.json').read_text())
        self.base = {**self.mail, 'apps': [{'id': 'firefox'}]}

    def test_merge_preserves_baseline_and_only_proton_default(self):
        result = module.merge(self.base, self.mail)
        self.assertEqual(result['apps'][0], {'id': 'firefox'})
        self.assertEqual([a['id'] for a in result['apps'] if a.get('default')], ['protonmail-desktop'])
        self.assertEqual(len(self.base['apps']), 1)

    def test_rejects_pin_and_schema_mismatch(self):
        for field in ('schemaVersion', 'nixpkgsRevision'):
            with self.assertRaises(ValueError):
                module.merge({**self.base, field: 'changed'}, self.mail)

    def test_rejects_second_merge(self):
        with self.assertRaises(ValueError):
            module.merge(module.merge(self.base, self.mail), self.mail)

    def test_bridge_is_addon_not_default_reader(self):
        bridge = next(a for a in self.mail['apps'] if a['id'] == 'protonmail-bridge')
        self.assertFalse(bridge['default'])
        self.assertEqual(bridge['package'], 'protonmail-bridge-gui')


if __name__ == '__main__':
    unittest.main()
