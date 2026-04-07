# Mitä tänään tekisi? — Random Daily Task Picker

A local web application for picking random daily tasks with cooldown logic. Built with FastAPI, SQLite, and vanilla JS.

## URL

**http://192.168.50.10:8338/**

## Quick start

### 1. Build the Docker image

```bash
docker compose build
```

### 2. Start the container

```bash
docker compose up -d
```

The app is now available at **http://192.168.50.10:8338/**.

### Reset all data

```bash
docker compose down -v && docker compose up -d
```

## Stack

| Layer    | Technology                          |
|----------|-------------------------------------|
| Backend  | Python 3.12, FastAPI, Uvicorn       |
| Database | SQLite (`/data/tasks.db`)           |
| ORM      | SQLAlchemy 2.0 (sync)               |
| Frontend | Single `index.html` — vanilla JS/CSS |
| Runtime  | Docker, host port **8338** → 8000   |

## Default tasks

| Task                | Cooldown |
|---------------------|----------|
| Pokemon Violet      | 2 days   |
| Piirtämistä         | 1 day    |
| Värityskirja        | 1 day    |
| Minecraft           | 2 days   |
| YouTube             | 1 day    |
| Näppäinharjoittelua | 1 day    |
| Lukemista           | 1 day    |
| Ponileikki          | 1 day    |

## API endpoints

| Method   | Endpoint                  | Description                           |
|----------|---------------------------|---------------------------------------|
| `GET`    | `/api/tasks`              | List all tasks (with cooldown status) |
| `GET`    | `/api/tasks/random`       | Random available task (200 or 204)    |
| `POST`   | `/api/tasks`              | Create task — body: `{name, cooldown_days}` |
| `PUT`    | `/api/tasks/{id}`         | Update task — body: `{name?, cooldown_days?, active?}` |
| `DELETE` | `/api/tasks/{id}`         | Delete task                           |
| `POST`   | `/api/tasks/{id}/done`    | Mark task as done (sets `last_done`)  |
| `POST`   | `/api/tasks/reorder`      | Bulk reorder — body: `[{id, sort_order}, ...]` |

### Task response schema

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

## Cooldown logic

A task is **available** when:
- `active = true`
- AND (`last_done` is `NULL` OR `last_done + cooldown_days <= now`)

If no tasks are available, the UI shows *"Kaikki tehtävät jäähtyvät"*.

## Frontend features

- **Big "Arvo tehtävä!" button** — picks a random available task
- **"✓ Tehty!" button** — marks task done, auto-picks a new one after 600 ms
- **Edit panel** (⚙ gear icon, top-right):
  - Drag-and-drop reorder (☰ handle)
  - Inline name editing (`contenteditable`)
  - Cooldown toggle: `1 pv` / `2 pv`
  - Active/inactive toggle
  - Delete with confirmation
  - Add new task at the bottom
  - Cooldown pill: `jäähtymässä — vapautuu 8.4.`
- **Responsive**: full-width edit panel on screens < 480px

## Project structure

```
task-picker/
├── backend/
│   ├── main.py            # FastAPI app, endpoints, seeding
│   ├── models.py          # SQLAlchemy ORM + Pydantic schemas
│   ├── database.py        # Engine, session, Base
│   └── requirements.txt
├── frontend/
│   └── index.html         # Complete single-file UI
├── data/                  # SQLite DB at runtime
├── Dockerfile
├── docker-compose.yml
└── .dockerignore
```
