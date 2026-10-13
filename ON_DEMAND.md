# On-demand parking updates

The frontend reads stored status once on page load. Refresh requests use
`POST /api/v1/parking/refresh`. There is no periodic browser polling and
no periodic Pi detection in this workflow. Stop the old continuous
`main.py run` publisher when using this mode.

The backend calls the Pi only when its 30-second shared cache expires.
Simultaneous callers share one in-flight job. Five status/refresh requests
per minute are allowed per client IP, including the initial status read;
excess requests return 429 and Retry-After. This is an anonymous LAN demo,
not authenticated per-user throttling. Users sharing an IP share a limit.
The limiter/cache are in memory for one backend instance and reset on restart.
Do not trust user-supplied forwarding headers or put this unchanged behind
multiple servers. Account-based limiting requires adding authentication.

## Start the Pi service

Pull this version on both devices. On the Pi, install the existing environment
and model if needed:

```bash
cd ~/terra
git pull --ff-only origin main
cd computer-vision
bash setup.sh
.venv/bin/python src/download_model.py
.venv/bin/python -c 'import secrets; print(secrets.token_urlsafe(32))'
```

Copy the generated random secret to both processes; do not commit it. On the Pi:

```bash
export TERRA_PI_TOKEN='PASTE_YOUR_GENERATED_SECRET'
.venv/bin/python src/demand_server.py \
  --input ../parkinglot/WIN_20260929_14_58_01_Pro.jpg
```

Keep this process running. It waits on port 8090 and reloads the saved photo
on each actual detection. To capture live images instead, replace `--input ...`
with `--camera pi` or `--camera usb`. This uses the existing pretrained vehicle
model, not the empty-reference polygon pipeline. Counts are estimates of
vehicles visible in the image; verify coverage and accuracy before treating
them as whole-lot occupancy. Annotated output: `captures/demand-annotated.jpg`.

## Start the backend laptop

Find the Pi's current IP with `hostname -I` on the Pi. Both devices must be
mutually reachable (some campus networks isolate clients). Allow the backend
laptop to reach Pi TCP port 8090. The frontend talks to the backend on port 8080;
it never knows the Pi token. Use this only on a trusted LAN: HTTP does not
encrypt the token. The existing manual `/update` endpoint is also LAN-only.

In Windows Command Prompt, from `terra-backend/`:

```cmd
set TERRA_PI_URL=http://YOUR_PI_IP:8090/detect
set TERRA_PI_TOKEN=PASTE_YOUR_GENERATED_SECRET
set SPRING_DATASOURCE_PASSWORD=YOUR_DATABASE_PASSWORD
mvnw.cmd spring-boot:run
```

On Linux/macOS use `export` and `bash mvnw spring-boot:run`.
Start PostgreSQL and supply your database password through `SPRING_DATASOURCE_PASSWORD`. The application no longer embeds a database password.
Start the frontend from `frontend/` using `npm ci` and `npm start`.
Open http://localhost:3000/?demo=14_58_01 and click Refresh parking status.
The backend calls the Pi, receives its two-field JSON, saves the result,
and returns it to the frontend. Within the next 30 seconds, refreshes reuse
that result. The saved demo image remains served from the backend laptop;
this service does not upload camera images to the frontend.

## JSON and database behavior

The response still has exactly `timeStamp` and `numOfCarsParked`. No capacity
or user information is added. Capacity stays hardcoded at 11 in the frontend.

`timeStamp` now means the backend receipt time of the latest successful check,
including checks whose count did not change. Cached reads do not advance it.
It is not the capture date of the saved photo. Existing timestamps remain
backend local time without an offset, so keep the backend/browser in the same
timezone for this demo.

Compare counts, not whole JSON: timestamps naturally change. If the count is
unchanged, no new `parking_logs` history row is inserted. One row in
`parking_latest_check` stores the current count and successful-check timestamp;
this survives restarts. Updating that singleton still writes to PostgreSQL,
but avoids unlimited identical history rows. Equal counts do not mean the
same vehicles are still parked. The Pi always replies to a requested check
so unchanged occupancy is distinguishable from a disconnected Pi.

A Pi failure/timeout returns 503 with Retry-After: 10 and retains the previous
result. For 10 seconds the backend will not retry a failed detection. The UI
shows a failure message and keeps old counts visible. It disables refresh
while waiting or cooling down. No background retry is scheduled.

Configuration in `application.properties`: `terra.cache-seconds` (30),
`terra.requests-per-minute` (5), `terra.pi-timeout-seconds` (60). The browser
waits at most 70 seconds; keep the backend timeout below that or change both.

## Verification

- Empty, partially occupied, and fully occupied synthetic polygon tests remain
  in `computer-vision/tests/test_pipeline.py`; these do not establish model accuracy.
- Pi HTTP tests cover token rejection, busy rejection, count/timestamp payload,
  failure, and no detection before a request.
- Backend tests cover one shared job, caching, failures/retry cooldown, IP limits,
  input validation, unchanged counts, and multiple changed counts (0, 3, 11).
- Frontend tests cover the button, request method, disabled cooldown, old-count
  retention, and the two-field display.
- GitHub Actions runs the vision/frontend checks and backend checks against
  H2 plus a disposable PostgreSQL 16 instance.

For the real-device demonstration, click refresh after more than 30 seconds,
check the annotated image, and run:

```sql
SELECT * FROM parking_latest_check;
SELECT id, num_cars_parked, recorded_at FROM parking_logs ORDER BY id DESC LIMIT 5;
```

Repeat without changing occupancy: latest-check time advances after expiry,
history does not grow. Change occupancy: history gets one new row. Rapid
requests receive 429. Stop the Pi service: after the cache expires, refresh
returns 503 while the frontend preserves the old values. Restart the backend:
GET status still retrieves the persisted latest result.

Implementation verification on the development machine: 14 backend tests passed
against H2 (Java 17 override), 6 frontend tests passed, 11 vision tests passed
including the downloaded-model blank-image smoke test, and the frontend production
build passed. The project Java 25 target is unchanged. Real Pi hardware and the
actual PostgreSQL installation still need the device checks above.
