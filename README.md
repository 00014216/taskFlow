# TaskFlow — Cloud Project Manager

A full-stack web application for managing projects and tasks, built with Django,
PostgreSQL, Redis, Docker, and deployed to Azure via GitHub Actions CI/CD.

> **Module:** 6BUIS014C Distributed Systems and Cloud Computing
> **Assessment:** Coursework 1 (50% of module grade)

---

## Features

| Feature | Description |
|---|---|
| **User Authentication** | Register, login, logout with session management |
| **Project CRUD** | Create, view, edit, and delete projects |
| **Task CRUD** | Create, view, edit, and delete tasks within projects |
| **Many-to-Many (Labels)** | Tasks can have multiple labels; labels span multiple tasks |
| **Redis Caching** | Dashboard stats cached for 2 minutes; cleared on data changes |
| **REST API** | `GET /api/tasks/` returns authenticated user's tasks as JSON |
| **Health Check** | `GET /health/` tests DB + Redis, returns JSON status |
| **Django Admin** | Full admin panel at `/admin/` for staff users |
| **CI/CD Pipeline** | GitHub Actions: test → build → deploy on every push to `main` |
| **Docker** | Multi-stage Dockerfile; dev and prod Docker Compose files |
| **Azure Deployment** | Production hosted on Ubuntu 24.04 VM, served by Nginx + Gunicorn |

---

## Technologies Used

| Layer | Technology | Version |
|---|---|---|
| Web Framework | Django | 4.2 |
| Database | PostgreSQL | 15 |
| Cache / Sessions | Redis | 7 |
| App Server | Gunicorn | 21.x |
| Web Server / Proxy | Nginx | 1.25 |
| Containerisation | Docker + Docker Compose | 24.x |
| CI/CD | GitHub Actions | — |
| Cloud Hosting | Azure VM (Ubuntu 24.04) | Standard_B1s |
| API Framework | Django REST Framework | 3.15 |
| Frontend | Bootstrap 5 (CDN) | 5.3 |
| Python | Python | 3.11 |

---

## Database Relationships

```
User ──< Project ──< Task >──< Label
          (1:many)  (1:many)  (many:many)
```

- **One-to-Many:** A user owns many projects; a project has many tasks.
- **Many-to-Many:** A task can have multiple labels; a label can be on multiple tasks.
  Implemented with `Task.labels = ManyToManyField(Label)` — Django creates a join table automatically.

---

## Project Structure

```
cloudblog/
├── .github/workflows/deploy.yml   GitHub Actions CI/CD pipeline
├── app/
│   ├── config/
│   │   ├── settings/
│   │   │   ├── base.py            Shared settings
│   │   │   ├── development.py     DEBUG=True, SQLite fallback
│   │   │   └── production.py      DEBUG=False, HTTPS settings
│   │   ├── urls.py                Root URL configuration
│   │   └── wsgi.py
│   ├── tasks/
│   │   ├── models.py              Label, Project, Task (with M2M)
│   │   ├── views.py               All CRUD views + API + health check
│   │   ├── forms.py               ProjectForm, TaskForm, LabelForm, RegisterForm
│   │   ├── serializers.py         DRF TaskSerializer (nested labels)
│   │   ├── admin.py               Django Admin configuration
│   │   ├── urls.py                All URL patterns
│   │   └── tests.py               20+ pytest tests
│   ├── templates/
│   │   ├── base.html              Sidebar layout (authenticated) + navbar (public)
│   │   ├── tasks/                 All page templates
│   │   └── registration/          Login and register pages
│   ├── static/css/style.css       Custom styles
│   ├── manage.py
│   └── requirements.txt
├── nginx/nginx.conf               Reverse proxy with upstream block
├── Dockerfile                     Multi-stage build
├── docker-compose.yml             Development environment
├── docker-compose.prod.yml        Production environment
├── .env.example                   Environment variable template
├── pytest.ini                     Test configuration
└── Instructions.md                Complete beginner setup guide
```

---

## Local Setup (Development)

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- [Git](https://git-scm.com/downloads) installed

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/cloudblog.git
cd cloudblog

# 2. Copy the environment file and fill in values
cp .env.example .env
# Edit .env — set POSTGRES_PASSWORD and DJANGO_SECRET_KEY at minimum

# 3. Start all containers (database, Redis, Django)
docker compose up -d

# 4. Run database migrations
docker compose exec web python manage.py migrate

# 5. Create a superuser (admin account)
docker compose exec web python manage.py createsuperuser

# 6. Open the app
# Main app:    http://localhost:8000
# Admin panel: http://localhost:8000/admin/
# Health check: http://localhost:8000/health/
# REST API:    http://localhost:8000/api/tasks/
```

### Running Tests

```bash
# Run all tests with coverage
docker compose exec web pytest --tb=short -v

# Run linting
docker compose exec web flake8 . --max-line-length=120 --exclude=tasks/migrations/
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in these values:

| Variable | Description | Example |
|---|---|---|
| `DJANGO_SECRET_KEY` | Long random string for security | `abc123...` (50+ chars) |
| `DJANGO_DEBUG` | `True` for dev, `False` for production | `False` |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated allowed domains | `yourdomain.com,1.2.3.4` |
| `POSTGRES_DB` | Database name | `cloudblog_db` |
| `POSTGRES_USER` | Database user | `cloudblog_user` |
| `POSTGRES_PASSWORD` | Database password | `StrongPassword123!` |
| `POSTGRES_HOST` | Database host (Docker service name) | `db` |
| `POSTGRES_PORT` | Database port | `5432` |
| `REDIS_URL` | Redis connection URL | `redis://redis:6379/1` |
| `DOCKERHUB_USERNAME` | Your Docker Hub username | `johndoe` |

---

## CI/CD Pipeline

Every push to the `main` branch triggers three jobs in sequence:

```
push to main
     │
     ▼
┌─────────┐    pass    ┌───────┐    pass    ┌────────┐
│  TEST   │ ─────────▶ │ BUILD │ ─────────▶ │ DEPLOY │
│         │            │       │            │        │
│ flake8  │            │Docker │            │SSH into│
│ pytest  │            │ build │            │Azure VM│
│         │            │& push │            │& restart│
└─────────┘            └───────┘            └────────┘
 (PRs too)           (main only)           (main only)
```

### GitHub Secrets Required

Go to your GitHub repository → **Settings → Secrets and variables → Actions**,
then add these secrets:

| Secret Name | Value |
|---|---|
| `DOCKERHUB_USERNAME` | Your Docker Hub username |
| `DOCKERHUB_TOKEN` | Docker Hub access token (not your password!) |
| `SSH_HOST` | Your Azure VM's public IP address |
| `SSH_USERNAME` | `azureuser` |
| `SSH_PRIVATE_KEY` | Contents of your `~/.ssh/id_ed25519` private key file |

---

## Production Deployment (Azure VM)

The production server uses:
- **Nginx** as a reverse proxy (handles SSL, serves static files)
- **Gunicorn** as the Django WSGI server (3 workers)
- **Docker Compose** (`docker-compose.prod.yml`) to orchestrate all containers

### First-time Setup on Azure VM

```bash
# SSH into your VM
ssh azureuser@YOUR_VM_IP

# Clone the repository
git clone https://github.com/YOUR_USERNAME/cloudblog.git ~/cloudblog
cd ~/cloudblog

# Create .env file (copy and fill in production values)
cp .env.example .env
nano .env   # set DJANGO_DEBUG=False, strong passwords, correct ALLOWED_HOSTS

# Pull and start production containers
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d

# Run migrations and create admin user
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

After the first setup, all future deployments happen **automatically** via GitHub Actions
whenever you push to `main`.

---

## API Endpoints

| Endpoint | Method | Auth Required | Description |
|---|---|---|---|
| `/api/tasks/` | GET | Yes (session) | List all tasks for the logged-in user |
| `/api/tasks/?search=docker` | GET | Yes | Search tasks by title or description |
| `/health/` | GET | No | Returns DB + Redis status as JSON |

### Example API Response

```json
{
  "count": 3,
  "results": [
    {
      "id": 1,
      "title": "Set up Docker containers",
      "status": "done",
      "priority": "high",
      "project": "Cloud Coursework",
      "labels": [{"id": 1, "name": "DevOps", "color": "#3498db"}],
      "created_at": "2026-01-15T10:30:00Z"
    }
  ]
}
```

### Example Health Check Response

```json
{
  "status": "healthy",
  "database": "connected",
  "cache": "connected",
  "timestamp": 1736945400.0,
  "version": "2.0.0"
}
```

---

## Redis Caching

Redis is used in two ways:

1. **Dashboard stats cache** — the total project/task counts are cached for 2 minutes.
   When a project or task is created/edited/deleted, the cache is cleared immediately.
   This prevents the database from being queried on every dashboard page load.

2. **Session storage** — Django uses Redis to store user sessions (login state).

The caching logic is in [app/tasks/views.py](app/tasks/views.py):
```python
cache_key = f'dashboard_stats_{request.user.id}'
stats = cache.get(cache_key)        # Try cache first
if not stats:
    stats = {...}                   # Query database only if cache miss
    cache.set(cache_key, stats, timeout=120)  # Cache for 2 minutes
```

---

## Screenshots

> *Add screenshots of your running application here for the submission.*
>
> Suggested screenshots:
> 1. Landing page (public)
> 2. Login page
> 3. Dashboard with stats
> 4. Project detail (kanban columns)
> 5. Task form showing the Many-to-Many labels checkboxes
> 6. Labels management page
> 7. REST API JSON response (`/api/tasks/`)
> 8. Health check JSON response (`/health/`)
> 9. Django Admin panel
> 10. GitHub Actions pipeline (3 green jobs)

---

## Troubleshooting

**Containers won't start:**
```bash
docker compose logs web    # View Django errors
docker compose logs db     # View PostgreSQL errors
```

**Database connection error:**
```bash
# Check if PostgreSQL is healthy
docker compose ps
# Wait 10 seconds and retry — db might still be starting
```

**Static files not loading in production:**
```bash
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

**GitHub Actions failing:**
- Check that all 5 GitHub Secrets are set correctly (Settings → Secrets)
- Check the Actions tab for the specific error message

---

## Licence

This project is created for educational purposes as part of the WIUT DSCC module coursework.
