# Connect the existing CodeTrack React frontend

The React prototype was built with browser `localStorage`. Starting this backend alone does **not** automatically connect the two. You need to change the frontend's load/create/update/delete handlers to call the API.

## 1. Start both applications
- Backend: `http://localhost:8080`
- Frontend (Vite): usually `http://localhost:5173`

## 2. Add a small API helper
Create `src/api.js` in the frontend project:

```js
const API_BASE = "http://localhost:8080/api/v1";

export async function getProblems() {
  const response = await fetch(`${API_BASE}/problems`);
  if (!response.ok) throw new Error("Could not load problems");
  return response.json();
}

export async function createProblem(problem) {
  const response = await fetch(`${API_BASE}/problems`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(toApiProblem(problem)),
  });
  if (!response.ok) throw new Error("Could not create problem");
  return response.json();
}

export async function updateProblem(id, problem) {
  const response = await fetch(`${API_BASE}/problems/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(toApiProblem(problem)),
  });
  if (!response.ok) throw new Error("Could not update problem");
  return response.json();
}

export async function deleteProblem(id) {
  const response = await fetch(`${API_BASE}/problems/${id}`, {
    method: "DELETE",
  });
  if (!response.ok) throw new Error("Could not delete problem");
}

function toApiProblem(problem) {
  return {
    title: problem.title,
    platform: problem.platform ?? "",
    difficulty: normalizeDifficulty(problem.difficulty),
    topic: problem.topic ?? "",
    status: normalizeStatus(problem.status),
    solvedDate: problem.solvedDate || null,
    notes: problem.notes ?? "",
  };
}

function normalizeStatus(status) {
  const value = String(status ?? "TODO").toUpperCase().replaceAll(" ", "_");
  if (value === "DONE" || value === "COMPLETED") return "SOLVED";
  if (value === "IN PROGRESS") return "IN_PROGRESS";
  if (["TODO", "IN_PROGRESS", "SOLVED"].includes(value)) return value;
  return "TODO";
}

function normalizeDifficulty(difficulty) {
  const value = String(difficulty ?? "").toUpperCase();
  if (value === "MEDIUM") return "Medium";
  if (value === "HARD") return "Hard";
  if (value === "EASY") return "Easy";
  return difficulty ?? "";
}
```

## 3. Match your existing frontend's field names
The starter frontend's exact state and event-handler names may differ from the examples above. In `src/App.jsx`, find the code that:
- reads `localStorage` when the app loads,
- saves changes to `localStorage`,
- adds a problem,
- edits a problem,
- deletes a problem.

Replace those data operations with the API functions. The API returns records with these fields: `id`, `title`, `platform`, `difficulty`, `topic`, `status`, `solvedDate`, `notes`, `createdAt`, and `updatedAt`.

Important: the API's `status` values are `TODO`, `IN_PROGRESS`, and `SOLVED`. If your UI uses labels such as “To Do”, “In Progress”, or “Solved”, map them at the UI boundary.

## 4. Verify the connection
1. Start MySQL and the Spring Boot backend.
2. Start the React app.
3. Add a problem in the UI after its handlers have been wired to `createProblem`.
4. Refresh the page. The record should still appear because it is stored in MySQL, not only in the browser.
5. Open `http://localhost:8080/api/v1/problems` to inspect the JSON response.

## Troubleshooting
- **Connection refused:** check that Spring Boot is running on port 8080.
- **Access denied for user:** correct the username/password in `application.properties`.
- **Unknown database:** run `CREATE DATABASE codetrack;` in MySQL.
- **CORS error:** use the Vite URL on port 5173; if you changed the port, add that origin to `WebConfig.java`.
- **400 Bad Request:** make sure `title` is not empty and `status` is one of `TODO`, `IN_PROGRESS`, `SOLVED`.
