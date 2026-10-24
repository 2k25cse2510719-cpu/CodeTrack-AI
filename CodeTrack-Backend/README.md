# CodeTrack Backend

Spring Boot REST API for the CodeTrack React frontend. Java 17+, Maven, and MySQL 8+.

## 1. Prerequisites
- JDK 17 or newer
- MySQL Server 8+
- IntelliJ IDEA or VS Code with Java support
- Maven (or use the IDE's Maven integration)

## 2. Create the database
In MySQL Workbench or a MySQL terminal, run:

```sql
CREATE DATABASE codetrack;
```

## 3. Configure your local MySQL credentials
Open `src/main/resources/application.properties`. Change `spring.datasource.username` and `spring.datasource.password`, or set environment variables:
- `DB_USERNAME`
- `DB_PASSWORD`
- optional `DB_URL`

Do not commit real passwords to GitHub. The default password `change_me` is a placeholder.

## 4. Run the backend
Open this folder as a Maven project in IntelliJ/VS Code, wait for dependencies to download, then run `CodeTrackApplication.java`.

Or, if Maven is installed, run from this folder:

```bash
mvn spring-boot:run
```

The API runs at `http://localhost:8080`.

Check `http://localhost:8080/api/health`. Expected response:

```json
{"status":"UP","application":"CodeTrack Backend"}
```

JPA creates/updates the `problems` table automatically. This is convenient for a student prototype; for a production system, use database migrations.

## 5. API endpoints
Base URL: `http://localhost:8080/api/v1/problems`

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/problems` | List problems |
| GET | `/api/v1/problems/{id}` | Get one problem |
| POST | `/api/v1/problems` | Create a problem |
| PUT | `/api/v1/problems/{id}` | Replace/update a problem |
| DELETE | `/api/v1/problems/{id}` | Delete a problem |

Example POST body:

```json
{
  "title": "Two Sum",
  "platform": "LeetCode",
  "difficulty": "Easy",
  "topic": "Arrays",
  "status": "SOLVED",
  "solvedDate": "2026-10-22",
  "notes": "Use a map to remember previously seen values."
}
```

Allowed status values: `TODO`, `IN_PROGRESS`, `SOLVED`. Dates use `YYYY-MM-DD` or `null`.

## 6. Test with Postman
1. Start the backend.
2. Send `GET http://localhost:8080/api/v1/problems`.
3. Send a `POST` to the same URL with Body > raw > JSON and the example above.
4. Send GET again to confirm the new record is stored.
5. Try `PUT http://localhost:8080/api/v1/problems/1` and `DELETE` on an existing ID.

## Important current limitations
- This is the initial backend: problem CRUD only.
- Authentication and separate user accounts are not implemented yet.
- Revision notes are currently stored in each problem's `notes` field, not a separate notes table.
- CORS allows the local Vite frontend at port 5173.
- The React prototype currently uses browser `localStorage`; it will not use this backend until its data-loading and save/delete handlers are changed. See `FRONTEND-INTEGRATION.md`.
