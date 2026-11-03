# YOLO + configurable lot ROI

The `vehicles.py` photo command and `demand_server.py` now share one
vehicle-detection pipeline. Choose the existing tiled MobileNet-SSD detector
(default `--detector ssd`) or YOLOv8 COCO ONNX (`--detector yolo`). Both can
filter their detections against a configured lot polygon. The old
empty-reference `main.py` pipeline and its per-space `config.json` are separate.

No Java, frontend, database, capacity, rate-limit, or cache changes are needed.
The Pi response still contains only `timeStamp` and `numOfCarsParked`. The
filtered count flows through the existing authenticated POST /detect route.

## Prepare the YOLO model on a laptop

Use a separate Python 3.10+ virtual environment on your laptop for export.
The Pi executes the exported model with OpenCV DNN on its CPU, without
Ultralytics, PyTorch, a GPU, or an internet connection at inference time.

Inside the activated exporter environment, from `computer-vision/`:

```bash
python -m pip install torch==2.5.1 torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r requirements-export.txt
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt').export(format='onnx', imgsz=640, opset=12, dynamic=False, simplify=True, nms=False, half=False, batch=1, device='cpu')"
```

The export downloads pretrained `yolov8n.pt` and produces `yolov8n.onnx`.
Transfer the ONNX file to the Pi at `computer-vision/models/yolov8n.onnx`.
Model files are ignored by Git. Use your existing SSH/SCP connection to copy
it; do not try to load the `.pt` file with OpenCV. The exporter pins the YOLOv8
toolchain rather than relying on the newest YOLO model family/output format.

This adapter expects raw COCO detection outputs [1,84,N] (or [1,N,84]): four
box coordinates and eighty class scores. YOLOv5 objectness outputs, custom
class counts, segmentation, pose, and exports with embedded NMS are rejected.
`--imgsz` must match the static export size. For a 320-pixel model, export with
imgsz=320 and pass `--imgsz 320` to Terra. This trades detail for computation;
measure accuracy and latency on your Pi before using it for the dashboard.

The model follows the upstream [Ultralytics license](https://www.ultralytics.com/license).
[Upstream YOLOv8 OpenCV example](https://github.com/ultralytics/ultralytics/tree/main/examples/YOLOv8-OpenCV-ONNX-Python).

## Prepare the Pi YOLO runtime

The distro OpenCV installed by `setup.sh` may be too old for this ONNX graph.
Use a separate runtime environment on 64-bit Raspberry Pi OS Bookworm
(Python 3.11), or another Python 3.9-3.12 installation with binary wheels:

```bash
bash setup.sh
/usr/bin/python3 -m venv --system-site-packages .venv-yolo
.venv-yolo/bin/python -m pip install --only-binary=:all: -r requirements-yolo.txt
```

This pins OpenCV 4.11 and keeps NumPy below 2 for compatibility with distro
camera extensions. Picamera2 is inherited from the system installation.
The old `.venv` SSD setup stays available. Python 3.13+, 32-bit Pi OS and other
OpenCV builds need separate dependency verification. No PyTorch is installed
by `requirements-yolo.txt`.

## Configure the lot boundary

Copy `roi.example.json` to `roi.json` and replace its points with the boundary
of the actual lot visible in your image. The supplied trapezoid is an example,
not a calibrated boundary for the saved demo photo.
For that specific photo, `roi.demo-14_58_01.json` provides a visually reviewed
parking-row boundary that excludes most of the road and trees. It is not a
per-space map, and it must not be reused for a different camera angle.

```json
{
  "polygon": [[0.10,0.15], [0.90,0.15], [0.95,0.95], [0.05,0.95]]
}
```

Coordinates are normalized: x = pixel_x / (image_width - 1),
y = pixel_y / (image_height - 1). Top left is [0,0]; bottom right is [1,1].
Order points around the boundary. Simple convex and concave polygons work;
self-crossing polygons, duplicate vertices, and zero-area shapes are rejected.
Do not repeat the first vertex at the end.

A vehicle is counted when its bounding box's bottom-center falls inside or
on the ROI boundary. A box merely overlapping the lot is not enough. This is
a geometric approximation, not proof a vehicle is parked. Moving vehicles
inside the boundary are also counted. Occluded cars and tilted camera views
can make the anchor inaccurate. This is one lot ROI, not a per-space map.

Omitting `--roi-config` counts all retained vehicle detections in the frame.
The ROI is loaded when the application starts; restart the service after edits.
Normalized coordinates scale with resolution but do not compensate for a
changed camera angle. Remap the lot if the camera moves.

## Test a saved photo before publishing

From `computer-vision/`, using the YOLO runtime above:

```bash
.venv-yolo/bin/python src/vehicles.py \
  --input ../parkinglot/WIN_20260929_14_58_01_Pro.jpg \
  --detector yolo --model models/yolov8n.onnx --roi-config roi.json
```

On Windows use your environment's Python (`python` or `.venv-yolo/Scripts/python.exe`).
The photo command writes `captures/photo-results/results.json` plus annotated
images. Only vehicles inside the ROI contribute to `detected_vehicles` and its
`detections` list. Green numbered boxes are counted; gray boxes are excluded;
the blue polygon is the ROI and the dot is the vehicle anchor. Numbering is
restarted after filtering. No backend update occurs without `--backend-url`.

Defaults: confidence 0.5, NMS IoU 0.45, input 640, classes 2 (car), 5 (bus),
and 7 (truck). Add `--classes 2` for cars only, or `--classes 2 3 5 7` to include
motorcycles. The default SSD path keeps its original car/bus classes and NMS
settings; `--classes`, `--imgsz`, and `--iou` configure YOLO only.

YOLO keeps aspect ratio with letterboxing, uses RGB values scaled to [0,1],
decodes boxes into original image coordinates, suppresses duplicates across
vehicle classes, then filters by ROI. It processes the whole image once;
the SSD path retains overlapping crops. A new model does not establish better
accuracy without labeled comparisons, especially for distant small cars.

## Start the on-demand Pi service

After setup and model transfer, supply the existing shared token, then run:

```bash
export TERRA_PI_TOKEN='YOUR_EXISTING_SHARED_TOKEN'
.venv-yolo/bin/python src/demand_server.py \
  --input ../parkinglot/WIN_20260929_14_58_01_Pro.jpg \
  --detector yolo --model models/yolov8n.onnx --roi-config roi.json
```

For live capture replace `--input ...` with `--camera pi` or `--camera usb`.
The camera should cover the whole lot whose capacity the frontend displays.
The server still listens on port 8090. It loads the model once and runs
inference only for authenticated requests, with the existing one-job lock.
The service saves `captures/demand-annotated.jpg`. The backend's demo-image
endpoint still serves its configured saved JPEG, not this annotated output.

`setup.sh` installs distro OpenCV and does not install export dependencies.
ONNX operator support varies by OpenCV version; use the pinned separate YOLO
runtime above. Do not replace libcamera via pip.
The service logs detection exceptions locally; the HTTP error stays generic.
A slow Pi request can exceed the backend timeout; measure latency before
changing `terra.pi-timeout-seconds` and the corresponding frontend timeout.

## Checks

```bash
python -m unittest discover -s tests -v
```

Tests cover decoding, RGB normalization, letterboxing, NMS, malformed outputs,
multiple vehicles, ROI inclusion/exclusion/boundaries, concave polygons,
resolution scaling, invalid geometry, shared entry-point wiring, and the
unchanged two-field authenticated HTTP contract. Mocked-network tests do
not establish real model accuracy or Raspberry Pi performance.

## Development verification

The real YOLOv8n model was exported with Ultralytics 8.3.0, CPU PyTorch 2.5.1,
and ONNX opset 12, then loaded by OpenCV 4.14.0. At confidence 0.5 it produced
5 detections on the selected demo photo with the demo-row ROI. A real inference
request through POST /detect returned those 5 detections in the existing
two-field contract. Visual review found missed cars, so this is not an accuracy
improvement claim. `yolo-evaluation.json` records model/image hashes and settings.
The automated tests include a real-model blank-image test when the local
ONNX file is present; otherwise that optional test is skipped. Raspberry Pi
latency and the distro OpenCV importer still need verification on the device.

All 28 computer-vision tests passed locally with model files installed, on both
OpenCV 4.14 and OpenCV 4.11 / NumPy 1.26.4. The selected photo also returned
5 detections under OpenCV 4.11. CI skips model-dependent smoke tests unless
the weights are installed; all geometry and decoding tests run without weights.
