# Eventshuffle Backend API

Django backend API for creating events, collecting votes, and finding suitable dates for all participants.

---

## Tech Stack
- Django + Django REST Framework
- PostgreSQL
- OpenAPI/Swagger (drf-spectacular)
- Docker + Docker Compose
- uv for dependency management
- Testing: pytest
- Linting: Black, isort, Flake8

---

## Prerequisites
- Docker
- Docker Compose
- **uv** (for local development only; optional if using Docker)

### Install uv
uv is a fast Python package manager and runner. Install it from [astral.sh/uv](https://astral.sh/uv):

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

After installation, sync dependencies for local work:
```sh
uv sync
```

**Note:** All commands can run inside Docker containers. Uv is only needed if working locally (e.g., generating migrations, linting).

---

## Environment Setup

Before running the project, create a `.env` file from the provided template:

```sh
cp .env.example .env
```

Edit `.env` with your own values for all variables. See `.env.example` for the list of required environment variables.


## Migration Management

Migrations must be version-controlled and generated locally (requires `uv` installed):

```sh
# Generate migrations (after model changes)
uv run python manage.py makemigrations

# Commit migration files to git
git add events/migrations/
git commit -m "Add migration for..."
```

Or use Docker if `uv` is not installed locally:
```sh
docker-compose run --rm api python manage.py makemigrations
```

The container will automatically run `python manage.py migrate` on startup to apply pending migrations.

## Local Development (Optional)

If you have `uv` installed locally, you can work without Docker:

```sh
# Sync dependencies
uv sync

# Run tests
uv run pytest

# Format and lint code
uv run black .
uv run isort .
uv run flake8 .

# Start Django development server
SECRET_KEY=dev-key uv run python manage.py runserver
```

Otherwise, all these commands work inside Docker containers.

---

## Quick Start
1. Build and start services:
   ```sh
   docker-compose build --no-cache
   docker-compose up -d
   ```
2. Access API docs:
   [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)

---

## API Endpoints
Base path: `/api/v1`
- `GET /event/list`
- `POST /event`
- `GET /event/{id}`
- `POST /event/{id}/vote`
- `GET /event/{id}/results`

Docs:
- Schema: `/api/schema/`
- Swagger UI: `/api/docs/`

---

## Container Management
- Stop services:
  ```sh
  docker-compose down
  ```
- Remove local images:
  ```sh
  docker-compose down --rmi local
  ```
- Remove volumes (deletes DB data):
  ```sh
  docker-compose down --volumes
  ```
- List running containers:
  ```sh
  docker-compose ps
  ```
- View logs:
  ```sh
  docker-compose logs -f api
  ```

---

## Shell & Database Access
- Open backend shell:
  ```sh
  docker-compose exec api sh
  ```
- Django admin shell:
  ```sh
  docker-compose exec api sh
  uv run python manage.py shell
  ```
- Django database shell:
  ```sh
  docker-compose exec api sh
  uv run python manage.py dbshell
  ```
- PostgreSQL shell:
  ```sh
  docker-compose exec db psql -U eventshuffle -d eventshuffle
  ```

---

## Testing
- Run tests (recommended):
  ```sh
  docker-compose run --rm api uv run pytest
  ```
- Run tests in running container:
  ```sh
  docker-compose exec api sh
  uv run pytest
  ```

---

## Linting

With `uv` installed locally:
```sh
uv run black .
uv run isort .
uv run flake8 .
```

Or in Docker:
```sh
docker-compose run --rm api uv run black .
docker-compose run --rm api uv run isort .
docker-compose run --rm api uv run flake8 .
```

---

## Extending the API: Adding a New Django App
To add a new app:
1. Open a shell in the API container:
   ```sh
   docker-compose exec api sh
   ```
2. Create a new Django app (replace `myapp`):
   ```sh
   uv run python manage.py startapp myapp
   ```
3. Register your app in `config/settings.py` under `INSTALLED_APPS`.
4. Add your app's URLs to `config/urls.py`.
5. Implement your models, views, serializers, and tests.
6. Run migrations:
   ```sh
   uv run python manage.py makemigrations myapp
   uv run python manage.py migrate
   ```
7. Restart the API container if needed:
   ```sh
   docker-compose restart api
   ```

---
