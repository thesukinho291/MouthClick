import unittest

from mouthclick.src.config import CONTROL_AREA_HEIGHT, CONTROL_AREA_WIDTH
from mouthclick.src.cursor_calibration import CursorCalibration


class CursorCalibrationTests(unittest.TestCase):
    def test_calibration_maps_center_to_control_center(self):
        calibration = CursorCalibration(
            {
                "points": {
                    "center": [100, 100],
                    "left": [60, 100],
                    "right": [140, 100],
                    "up": [100, 70],
                    "down": [100, 130],
                }
            }
        )

        x, y = calibration.map_to_control((100, 100), 3.0, 4.0)

        self.assertAlmostEqual(x, CONTROL_AREA_WIDTH / 2)
        self.assertAlmostEqual(y, CONTROL_AREA_HEIGHT / 2)

    def test_invalid_calibration_is_not_ready(self):
        calibration = CursorCalibration(
            {
                "points": {
                    "center": [100, 100],
                    "left": [99, 100],
                    "right": [101, 100],
                    "up": [100, 99],
                    "down": [100, 101],
                }
            }
        )

        self.assertFalse(calibration.is_ready())


if __name__ == "__main__":
    unittest.main()

