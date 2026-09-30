# Terra computer vision (Raspberry Pi 4)

## Use the photos already in Terra (no camera required)

The five uploaded images live in `parkinglot/` at the repository root.
They contain vehicles and have different framing, so they cannot be used
as empty references for the original occupancy pipeline. A separate
pretrained MobileNet-SSD/OpenCV DNN command analyzes them directly:

```bash
cd ~/terra
git pull --ff-only origin main
cd computer-vision
bash setup.sh
.venv/bin/python src/download_model.py
.venv/bin/python src/vehicles.py
```

The model downloads once (~23 MB); later runs work offline. It runs on
the CPU using the OpenCV installed by setup, without PyTorch or a GPU.
Images and JSON counts are saved to `captures/photo-results/`.
To analyze one photo:

```bash
.venv/bin/python src/vehicles.py --input ../parkinglot/WIN_20260929_14_58_08_Pro.jpg
```

This mode identifies car/bus candidates in overlapping crops and removes
overlapping duplicate boxes. It does not require space polygons. Counts
are **visible-image detections**, not verified whole-lot occupancy; it
does not publish them to the backend or invent a lot capacity. Cars cut
off by image edges or seen from above may be missed, and false positives
or duplicates remain possible. Review the annotated results. CPU timing
on this development machine does not establish Raspberry Pi performance.

See `photo-evaluation.json` for the first run on the five photos. These
results are not a labeled accuracy benchmark. The model source is
[chuanqi305/MobileNet-SSD](https://github.com/chuanqi305/MobileNet-SSD);
downloaded architecture and weights are SHA-256 verified. OpenCV 4 is
required for its Caffe importer. Live empty-reference occupancy commands
below remain available for future fixed-camera calibration.

This week's prototype captures camera images, processes them with OpenCV,
and estimates occupancy in individual parking-space polygons. It runs at
640×480 without a GUI or model downloads, including over SSH. Targets Python
3.9+ on Raspberry Pi OS Bookworm or newer, with a CSI camera supported by
Picamera2 or a USB webcam supported by OpenCV.

## First run on the Pi

From your existing clone:

```bash
cd ~/terra
git pull --ff-only origin main
cd computer-vision
bash setup.sh
.venv/bin/python src/main.py capture
```

The last command saves `captures/frame.jpg`. For a USB webcam, add
`--camera usb` to every capture, reference, and run command (or `--camera 1`
for the second webcam). The default is the CSI Pi camera. Setup installs
prebuilt OS packages instead of compiling OpenCV or installing libcamera
through pip. The virtual environment inherits these system packages.

If capture fails, check the connection with the Pi powered off, ensure the
camera isn't being used by another process, and try `rpicam-hello --list-cameras`
for a CSI camera. Older OS installations may use `libcamera-hello` instead.

## Calibrate your parking spaces

1. Mount the camera in a fixed position. Copy/view `captures/frame.jpg` on
   your laptop. Edit `config.json` on the Pi (for example, `nano config.json`).
2. Replace the demo polygon with one convex polygon per visible parking
   space. Order points around each polygon. Use normalized coordinates:
   `x = pixel_x / (image_width - 1)`, `y = pixel_y / (image_height - 1)`.
   Set `capacity` to the number of mapped spaces. The example is only one
   demo region, not a configured real parking lot.
3. With **all mapped spaces empty**, capture the reference:

   ```bash
   .venv/bin/python src/main.py reference
   ```

4. Park a car in a mapped space and run:

   ```bash
   .venv/bin/python src/main.py run --once
   ```

5. Inspect `captures/annotated.jpg`, `captures/changed.png`, and
   `captures/status.json`. Red polygons indicate estimated occupancy;
   green polygons indicate estimated vacancy. Check both empty and occupied
   examples. Adjust `pixel_threshold` (brightness difference, default 30)
   and `occupied_fraction` (fraction of changed pixels, default 0.15).
   Increasing either threshold makes detection less sensitive.

For continuous processing (Ctrl+C to stop):

```bash
.venv/bin/python src/main.py run --interval 2
```

The output files are overwritten, so continuous running won't accumulate
thousands of images. Local configuration, reference images, and outputs
are ignored by Git and remain on the Pi after a pull. If the camera moves
or its resolution changes, remap the regions and recapture the reference.

## Send counts to the existing Terra backend

First map and validate **every space in the lot**. Partial camera coverage
cannot provide a whole-lot car count. The backend currently expects a total
count, not per-camera counts, so run only one publisher for a fully covered
lot. Do not publish the demo region to the real dashboard.

Start the backend on your laptop and use its LAN IP, not `localhost`:

```bash
.venv/bin/python src/main.py run --interval 5 \
  --backend-url http://192.168.1.50:8080/api/v1/parking/update \
  --publish-calibrated
```

Replace that example IP with your laptop's IP. Both devices must be able to
reach one another; permit port 8080 through the laptop firewall if needed.
The payload matches the existing backend DTO:

```json
{"timeStamp":"2026-09-30T00:00:00+00:00","numOfCarsParked":3}
```

Network failures are reported and retried with the next fresh result.
Capacity minus occupied regions is calculated locally as `available` in
`status.json`. The frontend currently hardcodes `TOTAL_CAPACITY = 6` in
`frontend/src/App.js`; keep your mapped capacity aligned with that value,
or update it to your actual lot capacity.

## Limitations and offline checks

This detects visual changes relative to an empty reference, **not vehicle
identity**. Shadows, pedestrians, rain, headlights, changing exposure, and
camera movement may produce incorrect counts. Stationary vehicles remain
detectable because the reference is fixed. This is a milestone prototype;
evaluate real camera images before relying on it or publishing counts.

Without a Pi, install `requirements.txt` in a virtual environment and run:

```bash
python -m unittest discover -s tests -v
python src/main.py run --image path/to/test.jpg \
  --reference path/to/empty.jpg --config config.example.json
```

Offline runs cannot publish to the backend. Tests use synthetic images and
a local HTTP server; camera hardware must still be verified on the Pi.

References: [Raspberry Pi camera documentation](https://www.raspberrypi.com/documentation/computers/camera_software.html),
[Picamera2 manual](https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf).
