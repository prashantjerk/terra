# Terra — parking availability

Terra is a group parking-detector project. The Raspberry Pi processes an
image with Python/OpenCV, sends a parked-car count to a Java backend on a
laptop, and the React frontend displays availability.

| Component | Folder | Runs on |
| --- | --- | --- |
| Python/OpenCV | `computer-vision/` | Raspberry Pi 4 |
| Java/Spring Boot + PostgreSQL | `terra-backend/` | Backend laptop |
| React frontend | `frontend/` | Laptop/browser |
| Saved demo photos | `parkinglot/` | Both repository clones |

## Current data contract

The Pi posts JSON to `POST /api/v1/parking/update`:

```json
{"timeStamp":"2026-09-30T01:00:00+00:00","numOfCarsParked":8}
```

The frontend reads `GET /api/v1/parking/status` every three seconds:

```json
{"timeStamp":"2026-09-29T21:00:00","numOfCarsParked":8}
```

These are the only two public status fields. The backend records its own
receipt time; the Pi's optional timestamp is accepted but is not used as
the stored observation time. Reading status does not refresh that time.
The response currently uses the backend's local time without a timezone
offset. It indicates when a count was received, not when a saved photo
was taken. There is no automatic stale-data timeout yet.

Capacity is hardcoded as **11** in `frontend/src/App.js`:

```text
available spaces = max(0, 11 - numOfCarsParked)
```

For example, a count of 8 displays 3 available spaces. Counts above 11
show a warning and 0 available spaces. Before the first database observation,
both status fields are null and the frontend displays unknown counts and
an N/A timestamp. Internal database row IDs are not returned by the API.

## Run the saved-photo demo

Use **`parkinglot/WIN_20260929_14_58_01_Pro.jpg`**. No camera or empty-lot
reference is needed for this workflow.

### 1. Pull the same version on both devices

Run from each device's existing Terra clone:

```bash
git pull --ff-only origin main
```

If replacing the photo with an edited version, commit/push it under the
same exact filename first, then pull on both devices. The frontend serves
the laptop's copy; the Pi analyzes its own copy. The JSON does not transfer
an image or identify which image generated a count.

### 2. Start the backend on the laptop

Start PostgreSQL and create/configure `terra_db`. The project targets
Java 25; database configuration is described in the [backend README](terra-backend/README.md).
From `terra-backend/`, run:

```bash
# Windows Command Prompt
mvnw.cmd spring-boot:run
```

On macOS/Linux, use `bash mvnw spring-boot:run`. Start from this folder so
the default relative demo-photo path resolves correctly.

### 3. Start the frontend in a second laptop terminal

From `frontend/`:

```bash
npm ci
npm start
```

Open **http://localhost:3000/?demo=14_58_01** on the laptop. The page shows
the saved photo, latest count, capacity, available spaces, and update time.
The separate `GET /api/v1/parking/demo-image` endpoint serves the JPEG;
images are not added to the status JSON or stored in PostgreSQL.

### 4. Process and publish from the Pi

From `~/terra/computer-vision/`, set up once:

```bash
bash setup.sh
.venv/bin/python src/download_model.py
```

Then run for each demo observation:

```bash
.venv/bin/python src/vehicles.py \
  --input ../parkinglot/WIN_20260929_14_58_01_Pro.jpg \
  --backend-url http://YOUR_LAPTOP_IP:8080/api/v1/parking/update
```

Replace `YOUR_LAPTOP_IP` with the laptop's LAN IPv4 address (`ipconfig` on
Windows). `localhost` on the Pi refers to the Pi, not the laptop. The devices
must have network connectivity; allow TCP port 8080 on the laptop's private
network firewall if necessary. From the Pi, test connectivity with:

```bash
curl http://YOUR_LAPTOP_IP:8080/api/v1/parking/status
```

The script runs once, posts the actual detection count, and exits. Check
its numbered annotated image in `computer-vision/captures/photo-results/`.
The frontend displays the saved source photo, not the Pi's annotated output.
Allow up to three seconds for its next poll. Failed posts report an error;
fix connectivity and rerun. A successful post creates a `parking_logs` row.

## Detection limits and further setup

The small pretrained model detects car/bus candidates and can miss vehicles
or produce duplicate/incorrect boxes. Edited photos must be checked again;
the count is calculated, not hardcoded. `photo-evaluation.json` describes
an earlier run and is not a benchmark for a replacement photo. A demo
timestamp means the saved photo was processed/submitted recently, not that
it is a recent live view of the lot.

See the component instructions:

- [Computer vision: photo evaluation and optional live camera](computer-vision/README.md)
- [Backend: endpoints, database, and tests](terra-backend/README.md)
- [Frontend: demo mode, API configuration, and tests](frontend/README.md)
