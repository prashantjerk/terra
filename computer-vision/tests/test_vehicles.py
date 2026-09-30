import sys
from pathlib import Path
import unittest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from vehicles import positions, VehicleDetector
from download_model import MODEL_DIR


class TilingTests(unittest.TestCase):
    def test_tiles_cover_odd_sized_image_and_edges(self):
        for length in (50, 640, 1080, 1921):
            starts = positions(length, 640, 320)
            covered = np.zeros(length, dtype=bool)
            for start in starts:
                covered[start:start + 640] = True
            self.assertTrue(covered.all())
            self.assertEqual(len(starts), len(set(starts)))

    @unittest.skipUnless((MODEL_DIR / "mobilenet_iter_73000.caffemodel").exists(),
                         "Download the optional model before the inference smoke test")
    def test_blank_image_does_not_create_vehicles(self):
        detector = VehicleDetector()
        detections, annotated = detector.analyze(np.zeros((480, 640, 3), dtype=np.uint8))
        self.assertEqual(detections, [])
        self.assertEqual(annotated.shape, (480, 640, 3))
