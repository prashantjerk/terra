"""Check parking availability in saved photos from Terra's fixed 12-space view."""
import argparse
import json
from pathlib import Path

import cv2
import numpy as np

from main import ROOT, read_image, save_image
from roi import LotROI
from yolo import YoloDetector


def assess(frame, detections, roi):
    polygons = roi.polygons(frame.shape)
    occupied = set()
    for detection in detections:
        anchor = roi.anchor(detection, frame.shape)
        scores = [cv2.pointPolygonTest(polygon, anchor, True) for polygon in polygons]
        best = max(range(len(scores)), key=scores.__getitem__)
        if scores[best] >= 0:
            occupied.add(best)

    preview = frame.copy()
    spaces = {}
    for index, polygon in enumerate(polygons):
        name = f'P{index + 1:02d}'
        filled = index in occupied
        spaces[name] = 'occupied' if filled else 'available'
        color = (0, 0, 240) if filled else (0, 220, 0)
        points = np.rint(polygon).astype(np.int32)
        cv2.polylines(preview, [points], True, color, 3)
        x, y = points.mean(axis=0).astype(int)
        cv2.putText(preview, name, (x, y), cv2.FONT_HERSHEY_SIMPLEX, .65, (0, 0, 0), 4)
        cv2.putText(preview, name, (x, y), cv2.FONT_HERSHEY_SIMPLEX, .65, color, 2)
    return {
        'capacity': len(spaces),
        'occupied': len(occupied),
        'available': len(spaces) - len(occupied),
        'spaces': spaces,
    }, preview


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('photos', nargs='+', type=Path)
    parser.add_argument('--model', type=Path, default=ROOT / 'models/yolov8n.onnx')
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'captures/parking-photos')
    parser.add_argument('--confidence', type=float, default=.5)
    args = parser.parse_args()
    if not args.model.is_file():
        parser.error(f'YOLO model missing: {args.model}. See YOLO_ROI.md for export instructions.')
    roi = LotROI.load(ROOT / 'roi.spaces-12-20261110.json')
    detector = YoloDetector(args.model, args.confidence)
    failed = False
    for index, photo in enumerate(args.photos, 1):
        try:
            frame = read_image(photo)
            roi.polygons(frame.shape)
            detections, _ = detector.analyze(frame)
            result, preview = assess(frame, detections, roi)
            output = args.output_dir / f'{index:03d}-{photo.stem}-parking.jpg'
            if any(output.resolve() == source.resolve() for source in args.photos):
                raise ValueError('Output would overwrite an input photo; use another --output-dir')
            save_image(output, preview)
            print(json.dumps({'photo': str(photo), **result, 'preview': str(output)}))
        except (OSError, ValueError, RuntimeError, cv2.error) as error:
            print(json.dumps({'photo': str(photo), 'error': str(error)}))
            failed = True
    return int(failed)


if __name__ == '__main__':
    raise SystemExit(main())
