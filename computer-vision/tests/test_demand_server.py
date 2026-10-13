import json
from pathlib import Path
import sys
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.request import Request, urlopen
from urllib.error import HTTPError
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from demand_server import handler_for

class DemandServerTests(unittest.TestCase):
    def setUp(self):
        self.count = 0
        self.entered = threading.Event()
        self.release = threading.Event()
        self.block = False
        self.fail = False
        def detect():
            self.count += 1
            if self.fail:
                raise RuntimeError('camera disconnected')
            if self.block:
                self.entered.set()
                if not self.release.wait(5):
                    raise RuntimeError('test timeout')
            return 7
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), handler_for(detect, 'test-token'))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
    def tearDown(self):
        self.release.set()
        self.server.shutdown()
        self.thread.join()
        self.server.server_close()
    def request(self, token='test-token'):
        req=Request(f'http://127.0.0.1:{self.server.server_port}/detect', data=b'',
                    headers={'Authorization':'Bearer '+token}, method='POST')
        with urlopen(req, timeout=7) as response:
            return json.load(response)
    def test_no_work_until_requested_and_two_field_response(self):
        self.assertEqual(self.count, 0)
        result=self.request()
        self.assertEqual(set(result), {'timeStamp','numOfCarsParked'})
        self.assertEqual(result['numOfCarsParked'], 7)
        self.assertEqual(self.count, 1)
    def test_unauthorized_request_does_not_run_detector(self):
        with self.assertRaises(HTTPError) as error:
            self.request('wrong')
        self.assertEqual(error.exception.code, 401)
        self.assertEqual(self.count, 0)
    def test_busy_request_does_not_start_second_detection(self):
        self.block=True
        results=[]
        worker=threading.Thread(target=lambda:results.append(self.request()))
        worker.start()
        try:
            self.assertTrue(self.entered.wait(5))
            with self.assertRaises(HTTPError) as error:
                self.request()
            self.assertEqual(error.exception.code, 503)
            self.assertEqual(self.count, 1)
        finally:
            self.release.set()
            worker.join(7)
        self.assertEqual(len(results),1)
    def test_failed_detector_returns_unavailable(self):
        self.fail=True
        with self.assertRaises(HTTPError) as error:
            self.request()
        self.assertEqual(error.exception.code,503)

if __name__ == '__main__': unittest.main()
