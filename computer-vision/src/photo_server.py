"""Serve on-demand checks of the straight-on saved photos."""
import argparse
import base64
import hmac
import json
import logging
import os
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock

import cv2

from parking_photos import ROOT, LotROI, YoloDetector, analyze_photo


def photo_handler(folder, token, analyze):
    lock = Lock()

    def photos():
        return {p.name: p for p in sorted(folder.iterdir())
                if not p.is_symlink() and p.is_file()
                and len(p.name) <= 255 and p.suffix.lower() in {'.jpg', '.jpeg', '.png'}}

    class Handler(BaseHTTPRequestHandler):
        def reply(self, status, payload):
            body = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def authorized(self):
            return hmac.compare_digest(self.headers.get('Authorization', '').encode(),
                                       ('Bearer ' + token).encode())

        def do_GET(self):
            if not self.authorized():
                return self.reply(401, {'error': 'Unauthorized'})
            if self.path != '/photos':
                return self.reply(404, {'error': 'Unknown endpoint'})
            self.reply(200, list(photos()))

        def do_POST(self):
            if not self.authorized():
                return self.reply(401, {'error': 'Unauthorized'})
            if self.path != '/check-photo':
                return self.reply(404, {'error': 'Unknown endpoint'})
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 4096:
                    raise ValueError('Invalid body length')
                name = json.loads(self.rfile.read(length))['photo']
                if not isinstance(name, str):
                    raise ValueError('Expected a filename')
            except (ValueError, TypeError, KeyError):
                return self.reply(400, {'error': 'Invalid photo request'})
            photo = photos().get(name)
            if photo is None:
                return self.reply(404, {'error': 'Photo not found'})
            if not lock.acquire(blocking=False):
                return self.reply(503, {'error': 'Photo analysis is busy'})
            try:
                result, preview = analyze(photo)
                height, width = preview.shape[:2]
                if width > 1280:
                    preview = cv2.resize(preview, (1280, max(1, round(height * 1280 / width))))
                ok, encoded = cv2.imencode('.jpg', preview, [cv2.IMWRITE_JPEG_QUALITY, 80])
                if not ok or encoded.size > 2_000_000:
                    raise ValueError('Could not encode preview within the size limit')
                payload = {**result, 'photo': name, 'checkedAt': datetime.now(timezone.utc).isoformat(),
                           'previewJpeg': base64.b64encode(encoded).decode('ascii')}
            except (ValueError, OSError, cv2.error):
                logging.exception('Could not analyze saved photo')
                return self.reply(422, {'error': 'Photo cannot be analyzed; check the file and framing'})
            finally:
                lock.release()
            self.reply(200, payload)

    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--photos-dir', type=Path, required=True)
    parser.add_argument('--model', type=Path, default=ROOT / 'models/yolov8n.onnx')
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--port', type=int, default=8091)
    args = parser.parse_args()
    token = os.environ.get('TERRA_PI_TOKEN', '')
    if len(token) < 24 or any(c.isspace() for c in token):
        parser.error('Set TERRA_PI_TOKEN to the shared secret (at least 24 characters, no whitespace)')
    if not args.photos_dir.is_dir():
        parser.error('--photos-dir must be an existing directory')
    cv2.setNumThreads(2)
    roi = LotROI.load(ROOT / 'roi.straight-9.json')
    model = YoloDetector(args.model)
    with ThreadingHTTPServer((args.host, args.port),
                             photo_handler(args.photos_dir.resolve(), token,
                                           lambda photo: analyze_photo(photo, model, roi))) as server:
        print(f'Saved-photo detector listening on port {args.port}', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
