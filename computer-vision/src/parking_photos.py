"""Check parking availability in saved photos from Terra's fixed 12-space view."""
import argparse
import json
from pathlib import Path

import cv2
import numpy as np

from main import ROOT, read_image, save_image
from roi import LotROI
from yolo import YoloDetector


def detect_vehicles(frame, detector, zoom_upper_row=False):
    detections, _ = detector.analyze(frame)
    if not zoom_upper_row:
        return detections

    # Crop in reference-photo coordinates, scaled to the input resolution.
    height, width = frame.shape[:2]
    left, right = round(550 * width / 1920), round(1040 * width / 1920)
    bottom = round(220 * height / 1080)
    if right <= left or not bottom:
        return detections
    extra, _ = detector.analyze(frame[:bottom, left:right])
    for item in extra:
        x, y, w, h = item['box_xywh']
        box = (x + left, y, w, h)
        # Keep full-frame assignments for vehicles already detected there.
        if any(box_iou(box, original['box_xywh']) >= .45 for original in detections):
            continue
        detections.append({**item, 'box_xywh': box})
    return detections


def box_iou(first, second):
    x, y, w, h = first
    a, b, c, d = second
    intersection = (max(0, min(x + w, a + c) - max(x, a))
                    * max(0, min(y + h, b + d) - max(y, b)))
    union = w * h + c * d - intersection
    return intersection / union if union else 0


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
    parser.add_argument('--zoom-upper-row', action='store_true',
                        help='Also scan a crop around the distant upper parking row')
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
            detections = detect_vehicles(frame, detector, args.zoom_upper_row)
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
