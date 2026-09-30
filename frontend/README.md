# Terra frontend

React displays the latest backend count and calculates availability from
`TOTAL_CAPACITY = 11` in `src/App.js`. Capacity is not sent by the Pi or backend.

## Run on the backend laptop

From this folder, after pulling the latest repository version:

```bash
npm ci
npm start
```

The backend must be running on port 8080 with PostgreSQL configured.
Open http://localhost:3000 for the counts, or
**http://localhost:3000/?demo=14_58_01** for the counts plus the saved demo photo.
See the [project demo walkthrough](../README.md) for the Pi publishing command.

## API and display behavior

| Request | Used for |
| --- | --- |
| GET `/api/v1/parking/status` | Count and timestamp, polled every 3 seconds |
| GET `/api/v1/parking/demo-image` | Saved JPEG, displayed only in demo mode |

The status response contains exactly `timeStamp` and `numOfCarsParked`:

```json
{"timeStamp":"2026-09-29T21:00:00","numOfCarsParked":8}
```

This example displays 11 total, 8 occupied, and 3 available. Availability
is clamped to zero and a warning appears if the count exceeds capacity.
Before any observation exists, null values display as unknown counts and
N/A for the update time. Polling never replaces a missing timestamp with
the current browser time. On a fetch error, an error message appears and
previously received values remain visible.

The timestamp is the backend's receipt time and currently has no timezone
offset. The browser interprets it as local time; keep deployment timezone
settings aligned. There is no automatic stale-data timeout.

The demo displays `WIN_20260929_14_58_01_Pro.jpg` from the **backend laptop**.
It is a saved source image, not a live feed or annotated detection result.
Pull a replacement photo on both the laptop and Pi, rerun detection, and
allow the next frontend poll to refresh its image URL. The backend serves
the photo with no-store caching. No image bytes travel in the status JSON.

## API address

The default is `http://localhost:8080`. To use another backend address, set
`REACT_APP_API_BASE_URL` before starting/building the app (or put it in a
local `.env.local` file):

```dotenv
REACT_APP_API_BASE_URL=http://192.168.1.50:8080
```

Restart the development server after changing it. A browser on another
computer needs the laptop's reachable address, since its localhost refers
to that other computer. Backend CORS currently permits the origin
`http://localhost:3000`; other frontend origins need a matching backend change.

## Checks

```bash
npm test -- --watchAll=false
npm run build
```

Frontend tests cover count/availability, unknown initial status, and the
saved-photo URL. The production build is written to `build/`.
