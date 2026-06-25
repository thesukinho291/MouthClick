import unittest

from mouthclick.src.config import MAX_CURSOR_SENSITIVITY, MIN_CURSOR_SENSITIVITY
from mouthclick.src.visual_cursor import VisualCursor, limit_step


class VisualCursorTests(unittest.TestCase):
    def test_y_sensitivity_is_always_one_above_x(self):
        cursor = VisualCursor(3.0)

        self.assertEqual(cursor.sensitivity_x, 3.0)
        self.assertEqual(cursor.sensitivity_y, 4.0)

        cursor.adjust_sensitivity(1.5)

        self.assertEqual(cursor.sensitivity_y, cursor.sensitivity_x + 1.0)

    def test_sensitivity_stays_inside_limits(self):
        cursor = VisualCursor(3.0)

        cursor.adjust_sensitivity(100)
        self.assertEqual(cursor.sensitivity_x, MAX_CURSOR_SENSITIVITY)

        cursor.adjust_sensitivity(-100)
        self.assertEqual(cursor.sensitivity_x, MIN_CURSOR_SENSITIVITY)

    def test_max_step_grows_with_sensitivity(self):
        slow_cursor = VisualCursor(2.0)
        fast_cursor = VisualCursor(6.0)

        self.assertGreater(fast_cursor.max_step_pixels, slow_cursor.max_step_pixels)

    def test_limit_step_reduces_large_jump(self):
        x, y = limit_step(0, 0, 100, 0, 10)

        self.assertEqual(x, 10)
        self.assertEqual(y, 0)


if __name__ == "__main__":
    unittest.main()
