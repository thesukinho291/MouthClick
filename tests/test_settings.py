import tempfile
import unittest
from pathlib import Path

from mouthclick.src.settings import AppSettings


class SettingsTests(unittest.TestCase):
    def test_settings_round_trip(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "settings.json"
            settings = AppSettings(path=path)
            settings.set_value("sensitivity", 5.0)
            settings.set_tongue_thresholds(0.3, 0.12)

            self.assertTrue(settings.save())

            loaded = AppSettings.load(path)

            self.assertEqual(loaded.get_float("sensitivity", 0), 5.0)
            self.assertEqual(loaded.tongue_thresholds(), (0.3, 0.12))


if __name__ == "__main__":
    unittest.main()

