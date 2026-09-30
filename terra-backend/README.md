# Terra backend

Java/Spring Boot stores aggregate parked-car observations in PostgreSQL.
Its status contract has only `timeStamp` and `numOfCarsParked`; the frontend
hardcodes capacity 11 and calculates availability. There are no individual
parking-space APIs or capacity fields.

## REST endpoints

| Method | Endpoint | Result |
| --- | --- | --- |
| POST | `/api/v1/parking/update` | Validate and store one count; returns a success message |
| GET | `/api/v1/parking/status` | Latest timestamp/count JSON |
| GET | `/api/v1/parking/demo-image` | Configured saved JPEG, separate from status JSON |

Example Pi/demo request:

```json
{"timeStamp":"2026-09-30T01:00:00+00:00","numOfCarsParked":8}
```

The count is required and must be a nonnegative integer. Missing/null or
negative counts return 400. `timeStamp` in the request is optional: the
backend records its own receipt time instead. Successful updates insert
rows into `parking_logs`; the response to POST is text, not the status JSON.

Example GET response:

```json
{"timeStamp":"2026-09-29T21:00:00","numOfCarsParked":8}
```

GET does not modify the stored timestamp or create observations. With no
observations it returns `{"timeStamp":null,"numOfCarsParked":null}`. Startup
does not insert fake zero-count logs. The timestamp uses backend local time
without an offset; the frontend browser interprets it in its local timezone.
This records receipt time, not the saved image's capture time, and there is
no automatic stale-data timeout.

`ParkingLog` has an internal row ID, count, and observation time. The row
ID is not exposed in JSON. Older parking_spaces tables, if present, are
unused and are not deleted by startup.

## Database and startup

The repository targets Java 25 and includes a Maven wrapper. Create the
PostgreSQL database `terra_db` on the backend laptop. Configure
`src/main/resources/application.properties`, or override the connection
with `SPRING_DATASOURCE_URL`, `SPRING_DATASOURCE_USERNAME`, and
`SPRING_DATASOURCE_PASSWORD`. Startup creates the logs table from
`src/main/resources/db/schema.sql` and validates the JPA mapping.

From **terra-backend/**:

```bash
# Windows Command Prompt
mvnw.cmd spring-boot:run
```

On macOS/Linux: `bash mvnw spring-boot:run`. HTTP defaults to port 8080.
For Pi access, use the laptop's LAN IP and permit that port on the private
network firewall when necessary. Backend CORS permits http://localhost:3000.

## Demo photo

The default path is `../parkinglot/WIN_20260929_14_58_01_Pro.jpg`, resolved
relative to the backend process's working directory. The image endpoint
serves only this configured file, with no-store caching, and returns 404
if it is missing. It does not accept arbitrary paths, upload images, or
store image bytes in the database.

Start from terra-backend/ or set `terra.demo-image` to an absolute path,
for example in a local configuration override:

```properties
terra.demo-image=C:/projects/terra/parkinglot/WIN_20260929_14_58_01_Pro.jpg
```

Pull the same photo version on the laptop and Pi before presenting. The
frontend at http://localhost:3000/?demo=14_58_01 shows the laptop's photo
alongside the latest database count. There is no image association in the
two-field JSON; use the selected demo file on both devices. Full walkthrough:
[project README](../README.md).

## Verification

```bash
# Windows
mvnw.cmd test
# macOS/Linux
bash mvnw test
```

Tests use isolated H2 storage in PostgreSQL mode, including schema creation
and JPA validation. They do not connect to the real database. Development
checks used Java 17 with `-Djava.version=17`; the default target remains 25.
Tests cover the count contract, validation, null initial state, timestamp
stability on polling, and demo-image success/missing-file behavior.
