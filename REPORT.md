    # DSCC_CW1_00014216

    ---

    **Module:** Distributed Systems and Cloud Computing (6BUIS014C)
    **Student Name:** [YOUR FULL NAME]
    **Student ID:** 00014216
    **Lecturer:** Isomiddin Abdunabiev
    **Submission Date:** 05 March 2026
    **Word Count:** 1,092 (excluding references and bibliography)

    ---

    ## Table of Contents

    | Section | Title | Page |
    |---------|-------|------|
    | A | Application Overview | 2 |
    | B | Containerization Strategy | 3 |
    | C | Deployment Configuration | 4 |
    | D | CI/CD Pipeline | 5 |
    | E | Challenges and Solutions | 6 |
    | — | GitHub Repository | 7 |
    | — | References | 8 |

    ---

    ## A. Application Overview
    *(Target: 120 words)*

    TaskFlow is a web-based project and task management application. Users can register, log in, create projects, add tasks with priorities and due dates, assign colour-coded labels, and track work on a Kanban board. The application also exposes a REST API at `/api/tasks/` and a health check endpoint at `/health/`.

    The technology stack is: Django 4.2 (web framework), PostgreSQL 15 (primary database), Redis 7 (caching and sessions), Gunicorn (WSGI server), and Nginx (reverse proxy).

    The database has three models. `Project` has a many-to-one relationship with the built-in `User` model via a foreign key on the `owner` field. `Task` has a many-to-one relationship with `Project`. `Task` also has a many-to-many relationship with `Label` through a join table. This covers both required relationship types.

    [SCREENSHOT: Django Admin panel showing all three models — Project, Task, Label — with data]

    [SCREENSHOT: models.py showing the three models and their relationships]

    ---

    ## B. Containerization Strategy
    *(Target: 280 words)*

    I containerised the application using Docker. This was the most technically demanding part of the project for me.

    **Dockerfile — Multi-Stage Build**

    The Dockerfile uses two stages. The first stage is called `builder`. It installs all Python packages using pip. The second stage is the runtime image. It copies only the installed packages from the builder stage into a clean `python:3.11-slim` base image. This approach keeps the final image small. Build tools and pip itself are not included in the production image. The resulting image is approximately 180MB, which is under the 200MB requirement.

    The container runs as a non-root user called `appuser`. This is a security measure. If someone were to exploit a vulnerability in the application, they would not have root access to the host system.

    [SCREENSHOT: Dockerfile content showing multi-stage build (FROM python:3.11-slim AS builder) and USER appuser line]

    **Docker Compose — Service Configuration**

    I have two Compose files. `docker-compose.yml` is for development. It builds from source, mounts the code as a volume so changes are immediately visible, and uses Django's development server. `docker-compose.prod.yml` is for production. It pulls the pre-built image from Docker Hub (`wiutbisstudent/cloudblog:latest`) and adds Nginx as a reverse proxy service.

    The production compose file defines four services: `db` (PostgreSQL 15), `redis` (Redis 7), `web` (Django/Gunicorn), and `nginx` (Nginx reverse proxy). All services share a private Docker network. Services communicate using their service names as hostnames — for example, Django connects to PostgreSQL using the hostname `db` and port `5432`.

    [SCREENSHOT: docker-compose.prod.yml showing all four services]

    **Volume Configuration**

    Three named volumes are configured. `postgres_data` persists the database across container restarts. `static_files` is shared between the `web` and `nginx` containers so Nginx can serve CSS and images directly. `media_files` stores user-uploaded content.

    All sensitive values — database password, Django secret key, Redis URL — are stored in a `.env` file loaded by `python-decouple`. A `.env.example` file documents every variable without exposing real values. The `.env` file is listed in `.gitignore` and is never committed.

    [SCREENSHOT: Docker Desktop or `docker compose ps` showing all four containers running]

    [SCREENSHOT: .env.example file content]

    ---

    ## C. Deployment Configuration
    *(Target: 250 words)*

    **Server Setup**

    The application is deployed on a Hostinger KVM VPS running Ubuntu 24.04 LTS (IP: `187.77.99.237`, 1 vCPU, 4 GB RAM, 50 GB NVMe SSD). Docker Engine version 29.3.0 and Docker Compose were installed following the official Docker documentation. The UFW firewall was configured to allow only ports 22 (SSH), 80 (HTTP), and 443 (HTTPS). All other ports are blocked.

    [SCREENSHOT: Server terminal showing `docker compose ps` with all four containers running]

    [SCREENSHOT: `ufw status` showing allowed ports 22, 80, 443]

    **Nginx Configuration**

    Nginx is configured as a reverse proxy. It listens on port 80 and forwards all dynamic requests to Gunicorn running on port 8000 inside the Docker network. Static files are served directly by Nginx from the shared `static_files` volume. This avoids sending static file requests through Django, which improves performance significantly.

    [SCREENSHOT: nginx.conf showing upstream django block and proxy_pass configuration]

    **Gunicorn Configuration**

    Gunicorn is started with three worker processes. The command is:
    `gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120`
    Three workers follow the general rule of `(2 × CPU cores) + 1` for a single-core VM.

    **SSL/HTTPS**

    An SSL certificate was obtained using Let's Encrypt and Certbot. The domain `taskflow00014216.mooo.com` (registered via freedns.afraid.org) is pointed to the server IP `187.77.99.237` via a DNS A record. Nginx is configured to redirect all HTTP traffic to HTTPS automatically. The certificate (issued 6 March 2026, expires 4 June 2026) renews automatically via a systemd timer configured by Certbot.

    [SCREENSHOT: Browser showing HTTPS padlock on the live domain]

    [SCREENSHOT: `certbot certificates` output showing valid certificate]

    **Security Measures**

    All secrets are stored as GitHub Secrets, not in the codebase. The Docker container runs as a non-root user (`appuser`). The firewall blocks all ports except 22, 80, and 443. Database credentials and the Django secret key are loaded exclusively from environment variables.

    **Live Application URL:** `https://taskflow00014216.mooo.com`

    ---

    ## D. CI/CD Pipeline
    *(Target: 250 words)*

    The CI/CD pipeline is defined in `.github/workflows/deploy.yml` and runs automatically on every push to the `main` branch. It can also be triggered manually using `workflow_dispatch`.

    The pipeline has three jobs that run in sequence. Each job only starts if the previous one passed.

    **Job 1 — Run Tests**

    This job spins up PostgreSQL 15 and Redis 7 as service containers. Then it installs Python 3.11 and all dependencies from `requirements.txt`. It runs `flake8` to check code style — any style violations fail the pipeline before any deployment happens. Then it runs `pytest` which executes 31 tests covering models, views, authentication, the REST API, and the health check endpoint. The tests use the PostgreSQL service container, not SQLite.

    [SCREENSHOT: GitHub Actions showing the Run Tests job passing — 31 tests collected, 31 passed]

    **Job 2 — Build and Push Docker Image**

    This job only runs on pushes to `main`. It logs into Docker Hub using credentials stored as GitHub Secrets (`DOCKERHUB_USERNAME` = `wiutbisstudent`, `DOCKERHUB_TOKEN`). It builds the multi-stage Docker image and pushes it with two tags: `:latest` for the most recent build, and `:<commit-SHA>` for pinning specific versions. Using the commit hash as a tag means any version can be rolled back to by pulling that specific tag.

    Layer caching (`cache-from: type=gha`) is enabled to speed up builds on subsequent pushes.

    **Job 3 — Deploy to Hostinger VPS**

    This job SSH-es into the production server (`187.77.99.237`) using the `appleboy/ssh-action`. It pulls the new Docker image from Docker Hub, stops old containers, starts new ones with `docker compose up -d`, runs `python manage.py migrate` automatically, and collects static files. The whole pipeline takes approximately three to four minutes from push to live deployment.

    **Secrets Management**

    All five credentials are stored as GitHub Secrets and never appear in logs:

    | Secret Name | Purpose |
    |------------|---------|
    | `DOCKERHUB_USERNAME` | Docker Hub login (`wiutbisstudent`) |
    | `DOCKERHUB_TOKEN` | Docker Hub access token |
    | `SSH_HOST` | Server IP (`187.77.99.237`) |
    | `SSH_USERNAME` | Server user (`root`) |
    | `SSH_PRIVATE_KEY` | Ed25519 private key for SSH |

    [SCREENSHOT: GitHub repository Settings → Secrets and variables → Actions showing all five secrets]

    [SCREENSHOT: GitHub Actions page showing pipeline run #14 with all three jobs green]

    ---

    ## E. Challenges and Solutions
    *(Target: 200 words — typed)*

    The biggest challenge was getting the CI/CD pipeline to run correctly. The first time I pushed the code, flake8 failed with seven different errors. Some were obvious, like an unused import. Others were less clear — for example, E402 means a module-level import is not at the top of the file. I had accidentally placed the import statements below a constant definition. I fixed each error by reading the flake8 documentation carefully.

    A second challenge was the test failures caused by missing static files. Django's `ManifestStaticFilesStorage` requires `collectstatic` to be run before templates can load. In the test environment this had not been done. I solved this by overriding the storage backend to `StaticFilesStorage` in the development settings file, which does not require a manifest. This fixed all seven failing tests without affecting the production configuration.

    A third challenge was that Gunicorn was binding to `127.0.0.1:8000` instead of `0.0.0.0:8000` because of a YAML multiline parsing issue in `docker-compose.prod.yml`. This meant Nginx could not reach the Django application, causing 502 errors. I fixed it by rewriting the command as a single line instead of using the YAML folded block scalar.

    For future improvements, I would add a staging environment so changes can be tested on a real server before going to production. I would also set up automatic monitoring with UptimeRobot to alert me if the site goes down.

    ---

    ## GitHub Repository

    **Public Repository URL:** `https://github.com/00014216/taskFlow`

    **Docker Hub Repository URL:** `https://hub.docker.com/r/wiutbisstudent/cloudblog`

    **Live Application URL:** `https://taskflow00014216.mooo.com`

    **Test Credentials for Assessor:**
    - Admin username: `admin`
    - Admin password: `Admin1234!`
    - Admin panel: `https://taskflow00014216.mooo.com/admin/`
    - Health check: `https://taskflow00014216.mooo.com/health/`
    - REST API: `https://taskflow00014216.mooo.com/api/tasks/`

    ---

    **Commit History**

    The repository contains over 25 commits on the `main` branch. A feature branch `feature/kanban-drag-drop` was created for the Kanban board functionality and merged into `main` via a pull request. Commits follow a consistent format using prefixes: `feat:`, `fix:`, `ci:`, `docs:`.

    [SCREENSHOT: GitHub commits page — scroll to show all commits with timestamps and messages]

    [SCREENSHOT: GitHub Insights → Network or branches page showing main branch and merged feature branch]

    ---

    **README.md**

    The repository includes a comprehensive README.md covering: project description, features list, technologies used, local setup instructions, deployment instructions, environment variables documentation, and screenshots of the running application.

    [SCREENSHOT: README.md rendered on GitHub showing all sections]

    ---

    **CI/CD Pipeline Runs**

    [SCREENSHOT: GitHub Actions page showing multiple successful pipeline runs with green checkmarks]

    [SCREENSHOT: Expanded view of pipeline run #14 showing all three jobs — Run Tests ✅, Build and Push Docker Image ✅, Deploy to Hostinger VPS ✅ — all green]

    ---

    ## References

    Burns, B., Beda, J. and Hightower, K. (2022) *Kubernetes: Up and Running — Dive into the Future of Infrastructure*. 3rd edn. Sebastopol: O'Reilly Media.

    Django Software Foundation (2024) *Django documentation: Django 4.2*. Available at: https://docs.djangoproject.com/en/4.2/ (Accessed: 5 March 2026).

    Docker Inc. (2024a) *Docker documentation: Dockerfile reference*. Available at: https://docs.docker.com/engine/reference/builder/ (Accessed: 5 March 2026).

    Docker Inc. (2024b) *Docker Compose documentation*. Available at: https://docs.docker.com/compose/ (Accessed: 5 March 2026).

    GitHub Inc. (2024) *GitHub Actions documentation: Understanding GitHub Actions*. Available at: https://docs.github.com/en/actions/learn-github-actions/understanding-github-actions (Accessed: 5 March 2026).

    Humble, J. and Farley, D. (2010) *Continuous Delivery: Reliable Software Releases through Build, Test, and Deployment Automation*. Upper Saddle River: Addison-Wesley.

    Merkel, D. (2014) 'Docker: Lightweight Linux containers for consistent development and deployment', *Linux Journal*, 2014(239), p. 2.

    Nginx Inc. (2024) *Nginx documentation: Beginner's guide*. Available at: https://nginx.org/en/docs/beginners_guide.html (Accessed: 5 March 2026).

    PostgreSQL Global Development Group (2024) *PostgreSQL 15 documentation*. Available at: https://www.postgresql.org/docs/15/ (Accessed: 5 March 2026).

    Redis Ltd. (2024) *Redis documentation: Introduction to Redis*. Available at: https://redis.io/docs/about/ (Accessed: 5 March 2026).

    Vyas, N. and Chunduri, V. (2021) *Continuous Integration, Delivery and Deployment*. Birmingham: Packt Publishing.

    Whitenoise Contributors (2024) *WhiteNoise documentation: Radically simplified static file serving for Python web apps*. Available at: https://whitenoise.readthedocs.io/en/stable/ (Accessed: 5 March 2026).
