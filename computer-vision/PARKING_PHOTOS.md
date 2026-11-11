# Check the 12 parking spaces from saved photos

Run these commands in Windows PowerShell, from the repository's
`computer-vision` folder. No Pi, backend, or database is needed.

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Put the YOLOv8n ONNX model at `models/yolov8n.onnx`. Git does not include
model weights. If you don't have it, follow the laptop export instructions in
[YOLO_ROI.md](YOLO_ROI.md) using a separate environment.

```powershell
.\.venv\Scripts\python.exe src/parking_photos.py "C:\Photos\morning.jpg" "C:\Photos\afternoon.jpg"
```

You can pass one photo or several. Each gets a JSON result in the terminal
and a numbered preview in `captures/parking-photos/`. Red outlines mean
occupied; green means no vehicle was detected in that space. The result is
an estimate: shadows, occlusion, or missed detections can make a filled
space appear available. Use the previews to check the result.

Use the same camera position, angle, and crop as the original 1920×1080
reference. A resized copy with the same aspect ratio is fine. The program
rejects a different aspect ratio but cannot detect a moved camera. Use the
original photo without drawn markings.

For distant vehicles near the top edge, add `--zoom-upper-row`. This runs a
second YOLO pass on a crop of the same fixed camera view. Detections are mapped
back to the original image; each space still counts at most once. The option
uses the same model and confidence setting. Compare against a photo where P08
is empty before relying on the option for availability reporting.

For photos framed like the cropped 1720×968 sample, select the separate
nine-space map:

```bash
.venv-photos/bin/python src/parking_photos.py --roi-config roi.cropped-9.json \
  --output-dir captures/cropped-parking-photos /path/to/photo.jpg
```

This calibration excludes the clipped white SUV space at the upper left.
Review the partly visible P07 outline beside the upper end of the right-hand
row before using the map for differently cropped images. The reference
sample reports seven occupied spaces and two available (P02 and P07).
