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
