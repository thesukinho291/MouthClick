import unittest

from mouthclick.src.tongue_detector import TongueDetector


class TongueDetectorTests(unittest.TestCase):
    def test_cursor_hold_waits_for_full_tongue_gesture(self):
        detector = TongueDetector(mouth_open_threshold=0.2, color_ratio_threshold=0.1)
        detector.mouth_open_ratio = 0.18
        detector.color_ratio = 0.12

        self.assertFalse(detector.should_start_cursor_hold())

        detector.mouth_open_ratio = 0.21

        self.assertTrue(detector.should_start_cursor_hold())

    def test_cursor_hold_expires(self):
        detector = TongueDetector(mouth_open_threshold=0.2, color_ratio_threshold=0.1)
        detector.last_cursor_hold_at = 10.0

        self.assertTrue(detector.is_cursor_hold_active(10.1))
        self.assertFalse(detector.is_cursor_hold_active(20.0))


if __name__ == "__main__":
    unittest.main()
