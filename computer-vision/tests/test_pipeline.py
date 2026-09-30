import json
from pathlib import Path
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import unittest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from detector import Detector, validate_config
from main import publish


def config():
    return {"capacity": 2, "regions": [
        {"id": "A", "points": [[.05,.1],[.45,.1],[.45,.9],[.05,.9]]},
        {"id": "B", "points": [[.55,.1],[.95,.1],[.95,.9],[.55,.9]]}]}


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.empty = np.zeros((100, 200, 3), np.uint8)
        self.detector = Detector(self.empty, config())

    def test_empty_and_stationary_vehicle(self):
        result, _, _ = self.detector.analyze(self.empty)
        self.assertEqual((result["numOfCarsParked"], result["available"]), (0, 2))
        car = self.empty.copy()
        car[25:75, 20:75] = 200
        for _ in range(3):
            result, _, _ = self.detector.analyze(car)
            self.assertEqual((result["numOfCarsParked"], result["available"]), (1, 1))
            self.assertFalse(result["regions"][1]["occupied"])

    def test_change_outside_regions_is_ignored(self):
        frame = self.empty.copy()
        frame[:, 96:104] = 255
        self.assertEqual(self.detector.analyze(frame)[0]["numOfCarsParked"], 0)

    def test_two_occupied_regions(self):
        frame = self.empty.copy()
        frame[25:75, 20:75] = 200
        frame[25:75, 125:175] = 200
        result, _, _ = self.detector.analyze(frame)
        self.assertEqual((result["numOfCarsParked"], result["available"]), (2, 0))

    def test_invalid_calibration_and_resolution(self):
        invalid = config()
        invalid["capacity"] = 200
        with self.assertRaises(ValueError):
            validate_config(invalid)
        invalid = config()
        invalid["regions"][0]["points"][0] = [-1, 0]
        with self.assertRaises(ValueError):
            validate_config(invalid)
        with self.assertRaises(ValueError):
            self.detector.analyze(np.zeros((50, 50, 3), np.uint8))

    def test_backend_payload_matches_dto(self):
        received = []
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                received.append((self.path, json.loads(self.rfile.read(int(self.headers["Content-Length"])))))
                self.send_response(200)
                self.end_headers()
            def log_message(self, *_):
                pass
        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            publish(f"http://127.0.0.1:{server.server_port}/api/v1/parking/update",
                    {"timeStamp": "test", "numOfCarsParked": 2, "available": 0})
            self.assertEqual(received, [("/api/v1/parking/update", {"timeStamp": "test", "numOfCarsParked": 2})])
        finally:
            server.shutdown()
            thread.join()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
