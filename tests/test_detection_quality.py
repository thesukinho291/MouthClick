import unittest

from mouthclick.src.detection_quality import DetectionQuality


class DetectionQualityTests(unittest.TestCase):
    def test_quality_becomes_good_after_stable_frames(self):
        quality = DetectionQuality()

        for _ in range(6):
            quality.update(True, (100, 100))

        self.assertEqual(quality.status, "boa")
        self.assertTrue(quality.is_good())

    def test_quality_resets_when_face_is_missing(self):
        quality = DetectionQuality()

        quality.update(True, (100, 100))
        quality.update(False, None)

        self.assertEqual(quality.status, "sem rosto")
        self.assertFalse(quality.is_good())


if __name__ == "__main__":
    unittest.main()

