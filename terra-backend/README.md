# Terra backend: timestamp and parked-car count

The API exposes only `timeStamp` and `numOfCarsParked`. Capacity is a
hardcoded frontend value (`TOTAL_CAPACITY`, currently 6 in `frontend/src/App.js`).
The frontend computes availability as capacity minus the parked count,
clamped to zero to avoid negative availability for an erroneous high count.

## Endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | `/api/v1/parking/update` | Store a parked-car count observation |
| GET | `/api/v1/parking/status` | Read the latest observation |

Example update:

```bash
curl -X POST http://localhost:8080/api/v1/parking/update \
  -H 'Content-Type: application/json' -d '{"numOfCarsParked":3}'
```

The response to GET has exactly two fields:

```json
{"timeStamp":"2026-09-29T20:00:00","numOfCarsParked":3}
```

The timestamp is the backend's receipt time for the latest count, not the
frontend polling time. Reading status never refreshes it. The current
LocalDateTime format uses the backend's local timezone; deploy the backend
and frontend with that timezone in mind. The existing Pi request's optional
`timeStamp` is accepted for compatibility; storage uses server receipt time.
There is no automatic stale-data timeout yet; the UI displays the last
update time. If no observation exists, both fields are null and the UI
shows N/A for the timestamp. Startup does not seed fake zero-count observations.
Missing/null or negative counts return 400 and do not write to the database.

The only application entity is `ParkingLog`: an internal row ID plus count
and observation time. Its row ID is not part of the public JSON contract.
No individual parking-space model, endpoints, or capacity fields are used.
Existing parking_spaces tables from earlier runs are left untouched and
unused; no table/data deletion is performed.

## Run and verify

Create PostgreSQL database `terra_db` on the backend laptop. Configure the
connection in `src/main/resources/application.properties`, or override it
with `SPRING_DATASOURCE_URL`, `SPRING_DATASOURCE_USERNAME`, and
`SPRING_DATASOURCE_PASSWORD`. Pull the latest code and restart from
`terra-backend/` with `./mvnw spring-boot:run` (Windows: `mvnw.cmd spring-boot:run`).
The repository targets Java 25.

Run `./mvnw test`. Tests use an isolated H2 database in PostgreSQL mode,
including schema creation and JPA validation, without touching your real
database. Development-machine checks use Java 17 with `-Djava.version=17`.
The Pi's aggregate publisher still works with `/update`; saved-photo tests
remain local and do not publish inaccurate candidate counts automatically.
