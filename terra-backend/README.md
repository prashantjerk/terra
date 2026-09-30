# Terra backend milestone

The Java/Spring Boot backend now stores individual parking spaces alongside
the existing aggregate camera-count logs. Production persistence uses
PostgreSQL. The default database is `terra_db` on localhost:5432; create it
before starting the application. The project targets Java 25.

Start from `terra-backend/` using `./mvnw spring-boot:run` (or
`mvnw.cmd spring-boot:run` on Windows). Spring initializes the tables from
`src/main/resources/db/schema.sql` and validates their entity mappings.
It also upgrades the earlier three-column parking_spaces table without
deleting its rows. Startup no longer inserts a synthetic zero-count log.
You can override the local database configuration using
`SPRING_DATASOURCE_URL`, `SPRING_DATASOURCE_USERNAME`, and
`SPRING_DATASOURCE_PASSWORD` environment variables.

## Parking-space model

| Field | Meaning |
| --- | --- |
| spaceId | Unique ID, 1–32 letters/digits/underscores/hyphens; `summary` is reserved |
| label | Display label, required, at most 100 characters |
| occupied | true = occupied, false = vacant, null = not observed yet |
| lastUpdated | Backend observation/update time, stored as LocalDateTime |
| version | Internal optimistic-lock version to reject concurrent conflicting updates |

Occupancy is nullable so newly configured spaces are not assumed vacant.
Summary capacity means the number of spaces registered through this API;
unknown spaces are counted separately and are not included in availability.
No demonstration spaces are automatically created.

## REST contract

All paths below begin with `/api/v1/parking`.

| Method | Path | Purpose |
| --- | --- | --- |
| POST | /spaces | Create a space; returns 201 and a Location header |
| GET | /spaces | List registered spaces in ID order |
| GET | /spaces/{spaceId} | Read one space |
| PUT | /spaces/{spaceId}/status | Set occupied/vacant status |
| GET | /spaces/summary | Registered total, occupied, available, and unknown counts |
| POST | /update | Existing whole-lot camera-count update; inserts parking_logs row |
| GET | /status | Existing latest aggregate log for the current frontend |

Create a space (omit occupied to start unknown):

```bash
curl -i -X POST http://localhost:8080/api/v1/parking/spaces \
  -H 'Content-Type: application/json' \
  -d '{"spaceId":"A1","label":"Row A, space 1"}'
```

Set its status and read the space summary:

```bash
curl -X PUT http://localhost:8080/api/v1/parking/spaces/A1/status \
  -H 'Content-Type: application/json' -d '{"occupied":true}'
curl http://localhost:8080/api/v1/parking/spaces/summary
```

Example summary after registering and occupying only A1:

```json
{"totalSpaces":1,"occupiedSpaces":1,"availableSpaces":0,"unknownSpaces":0}
```

Invalid inputs return 400, missing spaces return 404, and duplicate IDs or
conflicting writes return 409. Aggregate updates require a nonnegative
numOfCarsParked. Their existing `timeStamp` field remains accepted; the
backend records its own receipt time in parking_logs.

## Frontend and camera integration

The current frontend still reads `/status` and hardcodes capacity 6.
The new space API persists space states in the database, but does not
rewrite aggregate camera logs or change the current dashboard. This keeps
two different measurements from overwriting each other. A future per-space
frontend should use `/spaces` and `/spaces/summary` together. The camera
code's existing aggregate publisher remains compatible with `/update`.
Saved-photo evaluation does not publish either kind of status automatically.

## Verification

Run `./mvnw test`. Tests use an isolated in-memory H2 database in PostgreSQL
mode, including schema initialization and JPA schema validation, with no
connection to the production database. API tests cover persistence,
updates, unknown occupancy, listing, duplicate/missing spaces, validation,
and compatibility of the existing aggregate endpoints. A real PostgreSQL
deployment and Pi connection still require verification on your devices.

Development-machine verification: 10 tests passed using Java 17 with
`-Djava.version=17`. The repository's default Java 25 target remains intact.
