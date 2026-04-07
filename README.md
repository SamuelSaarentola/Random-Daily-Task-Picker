# Mitä tänään tekisi? — Random Daily Task Picker

A local web app for picking random daily tasks with cooldowns, skips, and user suggestions. Built with FastAPI, SQLite, and vanilla JS.

## Quick Start

### 1. Start

```bash
docker compose up -d
```

### 2. Open

```
http://localhost:8338
```

### Reset all data

```bash
docker compose down -v && docker compose up -d
```

## Stack

| Layer    | Technology                        |
|----------|-----------------------------------|
| Backend  | Python 3.12, FastAPI, Uvicorn     |
| Database | SQLite (persisted via Docker volume) |
| ORM      | SQLAlchemy 2.0 (sync)             |
| Frontend | Vanilla HTML/JS/CSS (no framework) |
| Cursor   | Three.js TubesCursor (CDN)        |
| Runtime  | Docker, host port **8338** → 8000 |

## Features

### Home page (`/`)

- **Glass shimmer button** — animated gradient border, glassmorphism background, sweep shine
- **Shape wave background** — subtle grid of colorful shapes, ripples outward on button press
- **TubesCursor** — 3D neon cursor trail (Three.js, loaded from CDN)
- **Floating task names** — random active task names animate in/out from a 5×5 grid, one at a time every 7s
- **Skip system** — 3 skips per day (stored in `localStorage`), shown as "Ohita X/3" button with red glass border
- **Task suggestions** — type and press Enter to suggest a new task (saved as inactive, parent enables on todo page)
- **No-tasks state** — "Kaikki tehtävät tehty / lisää tulossa huomenna" when all are on cooldown

### Todo page (`/todo`)

- Full task management: add, edit, reorder, delete, toggle active, set cooldown
- Reset cooldown button (↺) per task
- Skip recharge button (⟳ Lataa ohitukset) — resets daily skip counter immediately
- No cursor animation on this page

## API Endpoints

### Tasks

| Method   | Endpoint                  | Description |
|----------|---------------------------|-------------|
| `GET`    | `/api/tasks`              | All tasks with cooldown status |
| `GET`    | `/api/tasks/random`       | Random available task (200 or 204) |
| `GET`    | `/api/tasks/active/names` | Active task names (for floating animation) |
| `GET`    | `/api/tasks/available/count` | Count of currently available tasks |
| `POST`   | `/api/tasks`              | Create task `{name, cooldown_days}` |
| `PUT`    | `/api/tasks/{id}`         | Update task `{name?, cooldown_days?, active?}` |
| `DELETE` | `/api/tasks/{id}`         | Delete task |
| `POST`   | `/api/tasks/{id}/done`    | Mark done (sets `last_done`) |
| `POST`   | `/api/tasks/{id}/reset-cooldown` | Clear cooldown |
| `POST`   | `/api/tasks/reorder`      | Bulk reorder `[{id, sort_order}, ...]` |
| `POST`   | `/api/tasks/suggest`      | Suggest task `{name}` (saved inactive) |

### Task response

```json
{
  "id": 1,
  "name": "Pokemon Violet",
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

- 3 skips per calendar day, stored in `localStorage` under key `taskpicker_skips`
- Format: `{ date: "YYYY-MM-DD", used: 0 }` — auto-resets each new day
- "Lataa ohitukset" on `/todo` resets the counter immediately
- Skipping marks the task as done (clears cooldown) but consumes a skip credit

## Project Structure

```
task-picker/
├── backend/
│   ├── main.py            # FastAPI app, endpoints, seeding
│   ├── models.py          # SQLAlchemy ORM + Pydantic schemas
│   ├── database.py        # Engine, session, Base
│   └── requirements.txt
├── frontend/
│   ├── index.html         # Home page (picker + effects)
│   └── todo.html          # Task management page
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── .gitignore
├── shapewave.md           # Shape wave reference
└── shimmerbutton.md       # Glass button reference
```

## Seeding

On first startup, 8 default tasks are seeded. User-suggested tasks are added with `active: false` and must be enabled via the todo page.
