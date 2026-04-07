# Mitä tänään tekisi? — Random Daily Task Picker

A local web app for picking random daily tasks with cooldowns, skips, and user suggestions. Built with FastAPI, SQLite, and vanilla JS.

## Quick Start

### Option 1: Pre-built image (easiest)

Edit `docker-compose.yml` — uncomment the `image:` line and comment out `build: .`, then:

```bash
docker compose up -d
```

### Option 2: Build from source

```bash
docker compose up -d --build
```

### Open

```
http://localhost:8338
```

### GitHub Container Registry

The pre-built image is published to GitHub Container Registry via GitHub Actions on every push to the `main` branch:

```yaml
image: ghcr.io/YOUR_USERNAME/task-picker:latest
```

To enable this for public use:

1. Go to your repository's **Settings > Packages** and set the visibility to **public**
2. Anyone can then pull the image without authentication:
   ```bash
   docker pull ghcr.io/YOUR_USERNAME/task-picker:latest
   ```
3. For unauthenticated users to pull images, the package **must be public** (set in repository settings)

### Reset all data

```bash
docker compose down -v && docker compose up -d
```

## Authentication

The `/todo` management page is protected by cookie-based session auth. Default credentials are set via environment variables in `docker-compose.yml`:

```yaml
environment:
  - AUTH_USERNAME=admin
  - AUTH_PASSWORD=admin
  - AUTH_SECRET=change-this-to-a-long-random-secret-key
```

- **Home page (`/`)** — fully public, no login required
- **Todo page (`/todo`)** — requires login (Tunnus/Salasana)
- A subtle 🔒 lock icon in the top-right corner of the home page links to `/todo`
- Change `AUTH_USERNAME` and `AUTH_PASSWORD` in production
- Generate a strong `AUTH_SECRET` (any long random string)

## Stack

| Layer    | Technology                        |
|----------|-----------------------------------|
| Backend  | Python 3.12, FastAPI, Uvicorn     |
| Database | SQLite (persisted via Docker volume) |
| ORM      | SQLAlchemy 2.0 (sync)             |
| Frontend | Vanilla HTML/JS/CSS (no framework) |
| Cursor   | Three.js TubesCursor (CDN)        |
| Auth     | Cookie-based sessions (Starlette) |
| Runtime  | Docker, host port **8338** → 8000 |

## Features

### Home page (`/`)

- **Glass shimmer button** — animated gradient border, glassmorphism background, sweep shine
- **Shape wave background** — subtle grid of colorful shapes at low opacity, ripples outward on button press
- **TubesCursor** — 3D neon cursor trail (Three.js, CDN)
- **Floating task names** — random active task names animate in/out from a 5×5 grid, one at a time every 7s
- **Skip system** — 3 skips per day (`localStorage`), "Ohita X/3" button with red glass border
- **Task suggestions** — type + Enter to suggest (saved inactive, parent enables on todo page)
- **Glass feedback popup** — green glass button appears on suggestion with shape wave ripple
- **No-tasks state** — "Kaikki tehtävät tehty / lisää tulossa huomenna"

### Todo page (`/todo`)

- Login screen with Tunnus/Salasana/Kirjaudu
- Full task management: add, edit, reorder, delete, toggle active, set cooldown
- Reset cooldown (↺) per task
- Skip reset button (⟳ Nollaa ohitukset) with inline feedback
- Red logout button (🔒 Ulos) in header when authenticated
- No cursor animation on this page

## API Endpoints

### Public (no auth)

| Method   | Endpoint                  | Description |
|----------|---------------------------|-------------|
| `GET`    | `/api/tasks`              | All tasks with cooldown status |
| `GET`    | `/api/tasks/random`       | Random available task (200 or 204) |
| `GET`    | `/api/tasks/active/names` | Active task names |
| `GET`    | `/api/tasks/available/count` | Available task count |
| `POST`   | `/api/tasks/{id}/done`    | Mark done (sets `last_done`) |
| `POST`   | `/api/tasks/suggest`      | Suggest task `{name}` (saved inactive) |

### Auth required

| Method   | Endpoint                  | Description |
|----------|---------------------------|-------------|
| `GET`    | `/todo`                   | Task management page |
| `POST`   | `/api/tasks`              | Create task |
| `PUT`    | `/api/tasks/{id}`         | Update task |
| `DELETE` | `/api/tasks/{id}`         | Delete task |
| `POST`   | `/api/tasks/reorder`      | Bulk reorder |
| `POST`   | `/api/tasks/{id}/reset-cooldown` | Clear cooldown |

### Auth endpoints

| Method   | Endpoint            | Description |
|----------|---------------------|-------------|
| `POST`   | `/api/auth/login`   | Login `{username, password}` |
| `POST`   | `/api/auth/logout`  | Logout |
| `GET`    | `/api/auth/check`   | Check auth status |

### Task response

```json
{
  "id": 1,
  "name": "Play a game",
  "cooldown_days": 2,
  "last_done": "2024-01-01T12:00:00",
  "sort_order": 0,
  "active": true,
  "available": true,
  "available_at": null
}
```

## Cooldown Logic

A task is **available** when:
- `active = true`
- AND (`last_done` is `NULL` OR `last_done + cooldown_days <= now`)

## Skip System

- 3 skips per calendar day, stored in `localStorage` under `taskpicker_skips`
- Format: `{ date: "YYYY-MM-DD", used: 0 }` — auto-resets daily
- "Nollaa ohitukset" on `/todo` resets immediately
- Skipping marks task done but consumes a skip credit

## Project Structure

```
task-picker/
├── backend/
│   ├── main.py            # FastAPI app, endpoints, auth, seeding
│   ├── models.py          # SQLAlchemy ORM + Pydantic schemas
│   ├── database.py        # Engine, session, Base
│   └── requirements.txt
├── frontend/
│   ├── index.html         # Home page (picker + effects)
│   └── todo.html          # Task management (auth protected)
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
└── .gitignore
```

## Seeding

On first startup, 8 default tasks are seeded. User-suggested tasks are added with `active: false` and must be enabled via the todo page.
