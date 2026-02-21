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

All commands run inside Docker containers. No local Python setup required.

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
Run from project root:
- `uv run black .`
- `uv run isort .`
- `uv run flake8 .`

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
