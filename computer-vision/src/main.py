"""Run from any directory: python src/main.py --help."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time
from urllib.request import Request, urlopen
from urllib.error import URLError
import cv2
from camera import Camera
from detector import Detector

ROOT = Path(__file__).resolve().parents[1]


def save_image(path, frame):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(path), frame):
        raise RuntimeError(f"Cannot write {path}")


def read_image(path):
    frame = cv2.imread(str(path))
    if frame is None:
        raise ValueError(f"Cannot read image: {path}")
    return frame


def publish(url, result):
    payload = {"timeStamp": result["timeStamp"], "numOfCarsParked": result["numOfCarsParked"]}
    request = Request(url, data=json.dumps(payload).encode(),
                      headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=5) as response:
        response.read()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["capture", "reference", "run"])
    parser.add_argument("--camera", default="pi", help="pi, usb (index 0), or a numeric USB index")
    parser.add_argument("--config", type=Path, default=ROOT / "config.json")
    parser.add_argument("--reference", type=Path, default=ROOT / "captures/empty.jpg")
    parser.add_argument("--output", type=Path, default=ROOT / "captures/frame.jpg")
    parser.add_argument("--image", type=Path, help="Analyze a saved image instead of a camera")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--interval", type=float, default=2)
    parser.add_argument("--backend-url", help="Full URL, e.g. http://LAPTOP_IP:8080/api/v1/parking/update")
    parser.add_argument("--publish-calibrated", action="store_true", help="Confirm all lot spaces are mapped and thresholds tested")
    args = parser.parse_args()
    if not 0.1 <= args.interval <= 3600:
        parser.error("--interval must be between 0.1 and 3600 seconds")
    if args.backend_url and (not args.publish_calibrated or args.image or args.command != "run"):
        parser.error("Publishing requires live run and --publish-calibrated after full-lot calibration")
    camera_source = "0" if args.camera == "usb" else args.camera
    if camera_source != "pi" and not camera_source.isdigit():
        parser.error("--camera must be pi, usb, or a nonnegative index")
    if args.command == "run":
        config = json.loads(args.config.read_text())
        detector = Detector(read_image(args.reference), config)
    else:
        if args.image:
            parser.error("--image is only supported for run")
        with Camera(camera_source) as camera:
            path = args.reference if args.command == "reference" else args.output
            save_image(path, camera.read())
            print(f"Saved {path}")
        return
    camera = None
    try:
        if not args.image:
            camera = Camera(camera_source)
        while True:
            start = time.monotonic()
            frame = read_image(args.image) if args.image else camera.read()
            result, annotated, changed = detector.analyze(frame)
            result["timeStamp"] = datetime.now(timezone.utc).isoformat()
            save_image(ROOT / "captures/annotated.jpg", annotated)
            save_image(ROOT / "captures/changed.png", changed)
            target = ROOT / "captures/status.json"
            temporary = target.with_suffix(".tmp")
            temporary.write_text(json.dumps(result, indent=2) + "\n")
            temporary.replace(target)
            print(json.dumps(result), flush=True)
            if args.backend_url:
                try:
                    publish(args.backend_url, result)
                except (URLError, TimeoutError, OSError) as exc:
                    print(f"Backend update failed (will retry next frame): {exc}", file=sys.stderr)
            if args.once or args.image:
                break
            time.sleep(max(0, args.interval - (time.monotonic() - start)))
    finally:
        if camera:
            camera.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    except (RuntimeError, ValueError, OSError, cv2.error) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
