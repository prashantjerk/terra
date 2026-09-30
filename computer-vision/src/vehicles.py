"""Pretrained car/bus detection on saved photos, without an empty reference."""
import argparse
import json
from pathlib import Path
import time
import cv2
import numpy as np
from download_model import MODEL_DIR, FILES
import hashlib
from datetime import datetime, timezone
from main import publish

ROOT = Path(__file__).resolve().parents[1]


def positions(length, tile, stride):
    if length <= tile:
        return [0]
    return sorted(set(list(range(0, length - tile + 1, stride)) + [length - tile]))


class VehicleDetector:
    def __init__(self, confidence=.5):
        if not 0 < confidence < 1:
            raise ValueError("Confidence must be between 0 and 1")
        for name, digest in FILES.items():
            path = MODEL_DIR / name
            if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                raise ValueError("Run python src/download_model.py first to install the verified model")
        self.net = cv2.dnn.readNetFromCaffe(str(MODEL_DIR / "deploy.prototxt"),
                                         str(MODEL_DIR / "mobilenet_iter_73000.caffemodel"))
        self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
        self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
        self.confidence = confidence

    def analyze(self, frame):
        h, w = frame.shape[:2]
        boxes, scores, classes = [], [], []
        # Overlapping crops preserve the small vehicles in wide lot photos.
        # A 1920x1080 photo takes 15 CPU inference passes; no GPU required.
        for y in positions(h, 600, 240):
            for x in positions(w, 640, 320):
                crop = frame[y:y + 600, x:x + 640]
                ch, cw = crop.shape[:2]
                self.net.setInput(cv2.dnn.blobFromImage(crop, .007843, (300, 300), 127.5))
                for detection in self.net.forward()[0, 0]:
                    category = int(detection[1])
                    score = float(detection[2])
                    if category not in (6, 7) or score < self.confidence:
                        continue
                    left, top, right, bottom = detection[3:7] * [cw, ch, cw, ch]
                    left = max(0, min(w - 1, int(left) + x))
                    right = max(0, min(w, int(right) + x))
                    top = max(0, min(h - 1, int(top) + y))
                    bottom = max(0, min(h, int(bottom) + y))
                    if right <= left or bottom <= top:
                        continue
                    boxes.append([left, top, right - left, bottom - top])
                    scores.append(score)
                    classes.append("bus" if category == 6 else "car")
        indices = np.asarray(cv2.dnn.NMSBoxes(boxes, scores, self.confidence, .25)).reshape(-1)
        annotated = frame.copy()
        detections = []
        for number, index in enumerate(indices, start=1):
            i = int(index)
            x, y, bw, bh = boxes[i]
            detections.append({"number": number, "class": classes[i], "confidence": round(scores[i], 4),
                               "box_xywh": boxes[i]})
            cv2.rectangle(annotated, (x, y), (x + bw, y + bh), (0, 220, 0), 3)
            cv2.putText(annotated, f"#{number} {classes[i]} {scores[i]:.2f}", (x, max(18, y - 5)),
                        cv2.FONT_HERSHEY_SIMPLEX, .55, (0, 180, 0), 2)
        return detections, annotated


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT.parent / "parkinglot")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "captures/photo-results")
    parser.add_argument("--confidence", type=float, default=.5)
    parser.add_argument("--backend-url", help="Demo: full URL to /api/v1/parking/update; requires one image")
    args = parser.parse_args()
    paths = ([args.input] if args.input.is_file() else
             sorted(p for p in args.input.glob("*") if p.suffix.lower() in (".jpg", ".jpeg", ".png")))
    if not paths:
        parser.error(f"No images found in {args.input}")
    if args.backend_url and not args.input.is_file():
        parser.error("--backend-url requires a single image file, not a directory")
    cv2.setNumThreads(2)
    detector = VehicleDetector(args.confidence)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for path in paths:
        frame = cv2.imread(str(path))
        if frame is None:
            raise ValueError(f"Cannot read {path}")
        start = time.monotonic()
        detections, annotated = detector.analyze(frame)
        result = {"image": path.name, "detected_vehicles": len(detections),
                  "inference_seconds": round(time.monotonic() - start, 3), "detections": detections}
        results.append(result)
        if not cv2.imwrite(str(args.output_dir / f"{path.stem}-annotated.jpg"), annotated):
            raise RuntimeError("Could not save annotated image")
        print(f"{path.name}: {len(detections)} detected vehicles", flush=True)
    (args.output_dir / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    print(f"Results saved in {args.output_dir}")
    if args.backend_url:
        payload = {"timeStamp": datetime.now(timezone.utc).isoformat(),
                   "numOfCarsParked": results[0]["detected_vehicles"]}
        (args.output_dir / "demo-payload.json").write_text(json.dumps(payload, indent=2) + "\n")
        publish(args.backend_url, payload)
        print(f"Demo update sent to {args.backend_url}: {json.dumps(payload)}", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError, OSError, cv2.error) as exc:
        raise SystemExit(str(exc))
