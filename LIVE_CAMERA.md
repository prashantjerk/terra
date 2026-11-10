# Terra: live parking camera

This workflow captures a new camera image when the backend requests a check.
The backend still shares in-flight requests and caches counts for 30 seconds,
with five status/refresh requests per minute per client IP. A cached refresh
will not trigger another capture. JSON still has only `timeStamp` and
`numOfCarsParked`. The detector estimates visible vehicle counts, not identities
or individual-space states. Validate actual cars against the annotated images.

The development workspace cannot reach your campus Pi. Camera recognition,
framing, visible capacity, and real counting accuracy must be checked there.
No saved-photo fallback is automatically selected by these commands.

## 1. Get the code on both machines

In your existing Terra clone, first check for local modifications. Do not
replace local files if Git reports conflicts:

```bash
git status
git fetch origin
git switch feature/yolo-roi
git pull --ff-only origin feature/yolo-roi
```

## 2. Prepare and test the Pi camera

SSH from laptop Git Bash or PowerShell:

```bash
ssh karkip685@karkip-pi.local
```

Use the Pi's current numeric IP if its hostname does not resolve. In the Pi
terminal, stop any old detector/camera program with Ctrl+C so the camera is free.
First verify camera discovery:

```bash
rpicam-hello --list-cameras
```

A CSI camera should be listed. If not, fix camera recognition before starting
Terra. For a USB webcam, use `TERRA_CAMERA=usb` below instead of `pi`.

From the Pi clone:

```bash
cd ~/terra/computer-vision
bash setup.sh
.venv/bin/python src/download_model.py
cp .env.pi.example .env.pi
nano .env.pi
```

Only copy the example if `.env.pi` does not already exist. Set its shared token
to exactly the laptop's `TERRA_PI_TOKEN`. The file is ignored by Git and takes
priority over old shell exports. Both quoted and unquoted single-line values
work on the Pi; whitespace inside tokens is rejected. Do not share the token.
Defaults: CSI camera, 1280x720 capture, SSD detector, confidence 0.5.

Take a fresh test image (no token or ROI is required for this step):

```bash
bash start-live.sh capture
```

This saves `~/terra/computer-vision/captures/live-frame.jpg`. Capture errors
stop the command; this command never substitutes the old demo photo.

## 3. Mark the actual parking-lot boundary

In laptop Git Bash, from `~/Desktop/codish/terra/`:

```bash
scp karkip685@karkip-pi.local:~/terra/computer-vision/captures/live-frame.jpg ./live-frame.jpg
```

Open `computer-vision/roi-editor.html` in your laptop browser. Choose that fresh
photo, click around each parking row in order, use Finish area / add next
for separate rows, and save `roi.live.json`. It works
locally with no upload. Mark the actual parking area and exclude nearby roads.
Copy the downloaded file to the Pi, adjusting the Downloads path if needed:

```bash
scp ~/Downloads/roi.live.json karkip685@karkip-pi.local:~/terra/computer-vision/roi.live.json
```

Do not reuse `roi.demo-14_58_01.json`: it belongs to the saved demo photograph.
A box is counted if its bottom-center is inside the boundary, including edges.
Keep the camera fixed after marking. A moved camera requires a new boundary.
The service rejects missing/malformed ROI files before starting.

## 4. Start the Pi service

From `~/terra/computer-vision/`:

```bash
bash start-live.sh serve
```

The camera opens and a startup preview is saved before the listening message.
No vehicle inference is performed until an authenticated request arrives.
The camera stays open between requests; the CSI queue is disabled so captures
are not reused from the previous request. USB capture drains a short buffer.
The service runs one detection job at a time. Keep this SSH terminal open.

If you only need to diagnose full-frame detection before drawing the boundary:

```bash
bash start-live.sh serve --full-frame
```

That includes any road traffic in view and is not calibrated lot occupancy.
After drawing a boundary, stop it and restart without `--full-frame`.

On each successful detection, the annotated image is overwritten at
`computer-vision/captures/demand-annotated.jpg`. The startup preview remains at
`captures/live-frame.jpg`. For a USB camera or different capture resolution,
change `.env.pi`, recapture a preview, and verify the boundary again.

SSD remains the default. If YOLO weights and `.venv-yolo` already exist,
set `TERRA_DETECTOR=yolo` and `TERRA_MODEL=models/yolov8n.onnx` in `.env.pi`, then:

```bash
TERRA_PYTHON=.venv-yolo/bin/python bash start-live.sh serve
```

See `computer-vision/YOLO_ROI.md` for export and runtime setup. A model swap
alone does not guarantee better accuracy. Inference timing must be measured
on the Pi; existing laptop measurements do not predict camera performance.

## 5. Configure and start the laptop backend

The Java API and database contract are unchanged; an existing current JAR can
be reused. From `terra-backend/`, create `.env` from `.env.example` if needed.
Supply your PostgreSQL credentials, Pi URL and matching token. The hostname
`http://karkip-pi.local:8090/detect` can avoid manual IP changes where mDNS works;
otherwise update the URL when the Pi address changes.

Ensure PostgreSQL is running. In laptop PowerShell:

```powershell
cd C:\Users\prash\Desktop\codish\terra\terra-backend
.\run-backend.ps1
```

The helper finds Java 25+, uses the existing JAR, loads `.env`, and removes stale
inherited settings for keys defined in that file. No repeated JAVA_HOME/token
exports are needed. Keep this terminal open.

If script execution is disabled, the existing Git Bash command still works
with Java 25 on PATH (clear stale overrides first):

```bash
cd ~/Desktop/codish/terra/terra-backend
unset TERRA_PI_TOKEN TERRA_PI_URL SPRING_DATASOURCE_PASSWORD SPRING_DATASOURCE_URL SPRING_DATASOURCE_USERNAME
java -jar ./target/terra-backend-0.0.1-SNAPSHOT.jar --spring.config.import='file:./.env[.properties]'
```

The backend needs TCP access to Pi port 8090. If the Pi's UFW firewall is active,
allow the laptop's **current** IP, not one from a past Wi-Fi connection:

```bash
sudo ufw allow from LAPTOP_CURRENT_IP to any port 8090 proto tcp
```

Check from laptop PowerShell:

```powershell
Test-NetConnection -ComputerName karkip-pi.local -Port 8090
```

The result must say `TcpTestSucceeded : True`. This does not verify the token;
401 responses in the Pi log mean the backend and Pi tokens differ.

## 6. Set visible capacity and start the frontend

Create `frontend/.env.local` from `.env.local.example`, and replace
`REACT_APP_TOTAL_CAPACITY=11` with the actual number of spaces covered by your
camera ROI. Eleven is only the old demo default. If the camera sees only one
row, use that row's capacity. Restart npm start after editing the value;
production frontend builds need rebuilding for environment changes.

In a separate laptop Git Bash terminal:

```bash
cd ~/Desktop/codish/terra/frontend
npm start
```

Open http://localhost:3000/ **without the saved-demo query string**. Click Refresh
parking status. Green numbered boxes in the Pi annotation show included cars;
gray boxes are outside the boundary. The frontend shows the count, configured
capacity minus count, and successful-check timestamp. The page is not a live
video stream; the saved-demo photo endpoint is not repurposed to show camera
images.

## Verification

Compare actual cars with `captures/demand-annotated.jpg`. Test a changed count
and an unchanged count, waiting at least 30 seconds between fresh checks. A
successful unchanged count updates the singleton latest-check time without
another history row. Inspect these in the same PostgreSQL instance/database
configured for the backend:

```sql
SELECT * FROM public.parking_latest_check;
SELECT * FROM public.parking_logs ORDER BY id DESC LIMIT 10;
```

If the camera fails, the Pi returns an error, the backend keeps the last result,
and the frontend displays the failure. No count of zero is fabricated. A
startup camera/model/ROI error is printed on the Pi before it starts listening.
For Pi networking, verify the current address and firewall before changing code.
