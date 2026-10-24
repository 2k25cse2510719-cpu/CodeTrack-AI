# CodeTrack Frontend

React + Vite frontend prototype for CodeTrack, a personal coding and DSA progress tracker.

## Run in VS Code
1. Extract this ZIP and open the `CodeTrack-Frontend` folder in VS Code.
2. Install Node.js LTS if you do not already have it.
3. Open **Terminal → New Terminal** and run:

   ```bash
   npm install
   npm run dev
   ```

4. Open the local URL Vite prints, usually `http://localhost:5173`.

**Important:** This is a React/Vite project. Do not run `index.html` with the Live Server extension. Use `npm run dev`.

## Included
- Overview dashboard and charts
- Add/edit/delete coding problems
- Search and filter by status/difficulty
- Revision notes view
- Analytics and weekly goals screens
- Responsive sidebar
- Browser-local persistence with `localStorage`

## Current limitations
This is frontend-only. Sample problem records and demo chart values are included. No Spring Boot REST API or MySQL database is connected yet; the data stays in the current browser.
