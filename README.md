# CodeTrack-AI

**Your Personal DSA Workspace**

CodeTrack-AI is a full-stack web application for tracking Data Structures and Algorithms practice. It provides user authentication and a personal workspace to organize coding problems and track progress.

**Live Demo:** https://code-track-ai-three.vercel.app

## Features

- User registration and login with JWT-based authentication
- Create and manage personal coding problem records
- Persistent storage using MySQL
- User-specific problem data isolation
- Responsive interface for desktop and mobile
- Cloud deployment with separate frontend and backend services

## Tech Stack

| Layer | Technologies |
|---|---|
| Frontend | React, Vite, JavaScript, CSS |
| Backend | Java 17, Spring Boot |
| Security | Spring Security, JWT |
| Database | MySQL, Aiven |
| Deployment | Vercel, Render |
| Build Tools | npm, Maven |

## Architecture

```text
Browser
   |
   v
React + Vite (Vercel)
   |
   | REST API + JWT
   v
Spring Boot (Render)
   |
   | Spring Data JPA
   v
MySQL (Aiven)
```

## Getting Started

### Prerequisites

- Node.js and npm
- Java 17
- Maven
- A MySQL database

### Clone the repository

```bash
git clone https://github.com/2k25cse2510719-cpu/CodeTrack-AI.git
cd CodeTrack-AI
```

### Configure the backend

Configure these environment variables for the backend:

- `DB_URL` — MySQL JDBC connection URL
- `DB_USERNAME` — Database username
- `DB_PASSWORD` — Database password
- `JWT_SECRET` — Secure JWT signing secret
- `JWT_EXPIRATION_MS` — Token expiration time in milliseconds

Never commit actual passwords, signing secrets, or production credentials.

Start the Spring Boot backend using Maven from `CodeTrack-Backend`.

### Configure the frontend

```bash
cd CodeTrack-Frontend
npm install
```

Create a local `.env` file with:

```env
VITE_API_BASE_URL=http://localhost:8081
```

Start the development server:

```bash
npm run dev
```

Use the appropriate API URL for your local or deployed environment.

## Deployment

- **Frontend:** [CodeTrack-AI on Vercel](https://code-track-ai-three.vercel.app)
- **Backend:** Spring Boot hosted on Render
- **Database:** MySQL hosted on Aiven

## Project Structure

```text
CodeTrack-AI/
├── CodeTrack-Frontend/
├── CodeTrack-Backend/
├── .gitignore
└── README.md
```

## Learning Outcomes

- Full-stack web application development
- React-based frontend development
- REST API integration
- JWT authentication and authorization
- MySQL database integration
- Environment-based configuration
- Git, GitHub, and cloud deployment

## Future Improvements

- Problem search and filtering
- Topic and difficulty categorization
- Progress statistics and dashboards
- Expanded automated test coverage

---

Built as a hands-on full-stack development project.
