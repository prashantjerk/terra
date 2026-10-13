"""On-demand Pi detector: POST /detect from the backend."""
import argparse
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hmac
import json
import os
from pathlib import Path
import threading


def handler_for(detect, token):
    lock = threading.Lock()
    class Handler(BaseHTTPRequestHandler):
        def reply(self, status, payload):
            body = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(body)
        def do_POST(self):
            if self.path != '/detect':
                return self.reply(404, {'error': 'Not found'})
            if not hmac.compare_digest(self.headers.get('Authorization', '').encode('utf-8'), ('Bearer ' + token).encode('utf-8')):
                return self.reply(401, {'error': 'Unauthorized'})
            if not lock.acquire(blocking=False):
                return self.reply(503, {'error': 'Detection already running'})
            try:
                count = detect()
                if type(count) is not int or count < 0:
                    raise ValueError('Invalid detector result')
                self.reply(200, {'timeStamp': datetime.now(timezone.utc).isoformat(), 'numOfCarsParked': count})
            except Exception:
                self.reply(503, {'error': 'Detection failed'})
            finally:
                lock.release()
    return Handler


def main():
    import cv2
    from camera import Camera
    from vehicles import VehicleDetector
    from main import read_image, save_image, ROOT
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--input', type=Path)
    source.add_argument('--camera', help='pi, usb, or numeric USB index')
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--port', type=int, default=8090)
    args = parser.parse_args()
    token = os.environ.get('TERRA_PI_TOKEN', '')
    if len(token) < 24:
        parser.error('Set TERRA_PI_TOKEN to a shared random secret of at least 24 characters')
    if args.input and not args.input.is_file():
        parser.error('--input must be an existing image')
    camera_source = '0' if args.camera == 'usb' else args.camera
    if args.camera and camera_source != 'pi' and not camera_source.isdigit():
        parser.error('Invalid camera source')
    cv2.setNumThreads(2)
    detector = VehicleDetector()
    def detect():
        if args.input:
            frame = read_image(args.input)
        else:
            with Camera(camera_source) as camera:
                frame = camera.read()
        detections, annotated = detector.analyze(frame)
        save_image(ROOT / 'captures/demand-annotated.jpg', annotated)
        return len(detections)
    server = ThreadingHTTPServer((args.host, args.port), handler_for(detect, token))
    server.daemon_threads = True
    print(f'Pi detector listening on port {args.port}; waiting for requests', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

if __name__ == '__main__':
    main()
