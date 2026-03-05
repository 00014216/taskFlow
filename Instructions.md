# TaskFlow — Complete Setup & Deployment Guide

**Module:** 6BUIS014C — Distributed Systems and Cloud Computing
**Project:** TaskFlow — Cloud Project & Task Manager

---

## Table of Contents

1. [What Is This Project?](#1-what-is-this-project)
2. [Accounts You Need to Create](#2-accounts-you-need-to-create)
3. [Setting Up Your Computer](#3-setting-up-your-computer)
4. [Running the App Locally](#4-running-the-app-locally)
5. [What Each File Does](#5-what-each-file-does)
6. [Pushing Your Code to GitHub](#6-pushing-your-code-to-github)
7. [Setting Up Your Azure Cloud Server](#7-setting-up-your-azure-cloud-server)
8. [The CI/CD Pipeline Explained](#8-the-cicd-pipeline-explained)
9. [Your First Automatic Deployment](#9-your-first-automatic-deployment)
10. [How to Run Tests](#10-how-to-run-tests)
11. [Rolling Back if Something Goes Wrong](#11-rolling-back-if-something-goes-wrong)
12. [How to Get SSL (HTTPS)](#12-how-to-get-ssl-https)
13. [Common Problems and Fixes](#13-common-problems-and-fixes)
14. [Preparing for Your Viva Voce](#14-preparing-for-your-viva-voce)
15. [Glossary](#15-glossary)

---

## 1. What Is This Project?

### In Plain English

Imagine a tool like Trello or Jira. Users create projects, add tasks to each project, tag tasks with coloured labels, and track what's To Do, In Progress, or Done. That's TaskFlow.

What makes it special for this coursework is **how it's built and deployed**:

- The website runs inside a **Docker container** — like a self-contained box with everything it needs
- It uses **three different services** running together: Django (the website), PostgreSQL (the database), and Redis (the fast cache)
- When you push new code to GitHub, it **automatically tests and deploys itself** — no manual steps needed

### The Technology Stack

Think of the stack as layers, each doing a specific job:

```
Browser (you visiting the site)
       ↓
    Nginx (the doorman — routes requests)
       ↓
   Gunicorn (the waiter — hands work to Django)
       ↓
    Django (the kitchen — processes requests, returns pages)
       ↓
  PostgreSQL  ←→  Redis
  (the filing    (the whiteboard
   cabinet)       — fast, temporary)
```

| Layer | Technology | Job |
|---|---|---|
| Web Server | Nginx | Receives all requests, serves static files |
| App Server | Gunicorn | Runs Django in production |
| Framework | Django 4.2 | The actual website code |
| Database | PostgreSQL | Stores posts, users, comments permanently |
| Cache | Redis | Stores popular data in fast memory |
| Containers | Docker | Packages everything into portable boxes |
| CI/CD | GitHub Actions | Automatically tests and deploys on every push |
| Cloud | Azure VM | The physical server where it all runs |

---

## 2. Accounts You Need to Create

You need three free accounts. Create them in this order.

### 2a. GitHub Account

GitHub is where your code lives. It also runs the CI/CD pipeline.

1. Open your browser and go to **https://github.com/signup**
2. Enter your email address, click **Continue**
3. Create a password, click **Continue**
4. Enter a username (e.g., `john-cloudblog`), click **Continue**
5. Complete the verification puzzle
6. Check your email and enter the verification code
7. On the "How many team members?" page — choose **Just me**
8. Skip the feature selection screen (click **Continue for free**)

You now have a GitHub account. ✅

**Create a new repository:**
1. Click the **+** icon in the top-right corner
2. Click **New repository**
3. Repository name: `cloudblog`
4. Description: `DSCC Coursework - News/Blog Platform`
5. Select **Public**
6. Do NOT check "Add a README file" (we already have one)
7. Click **Create repository**
8. **Copy the repository URL** — it looks like `https://github.com/YOUR_USERNAME/cloudblog.git`

### 2b. Docker Hub Account

Docker Hub stores your Docker images (packaged versions of the app). GitHub Actions pushes images here, and the Azure server downloads them from here.

1. Go to **https://hub.docker.com/signup**
2. Fill in username, email, password
3. Verify your email

**Create an Access Token (important — don't use your password):**
1. Log in to Docker Hub
2. Click your username in the top-right corner → **Account Settings**
3. Click **Security** in the left menu
4. Click **New Access Token**
5. Description: `github-actions-token`
6. Access permissions: **Read, Write, Delete**
7. Click **Generate**
8. **COPY THE TOKEN NOW** — it is only shown once!
   Save it somewhere safe (e.g., Notepad). It looks like `dckr_pat_xxxxxxxx`

### 2c. Azure for Students Account

Azure is Microsoft's cloud platform. The "for Students" version gives you $100 free credit with no credit card required.

1. Go to **https://azure.microsoft.com/en-us/free/students/**
2. Click **Start free**
3. Sign in with your university email address
4. Complete the verification steps
5. Once verified, you have access to the Azure Portal

---

## 3. Setting Up Your Computer

### 3a. Install Git

Git is the tool that tracks changes to your code.

**Windows:**
1. Go to **https://git-scm.com/download/win**
2. Download the installer and run it
3. Accept all default options during installation
4. Open **Command Prompt** (search for `cmd` in the Start menu)
5. Type: `git --version`
6. You should see something like: `git version 2.43.0`

**After installing, configure Git with your name:**
```bash
git config --global user.name "Your Full Name"
git config --global user.email "your.email@example.com"
```

### 3b. Install Docker Desktop

Docker Desktop runs Docker containers on your Windows computer.

1. Go to **https://www.docker.com/products/docker-desktop/**
2. Click **Download for Windows**
3. Run the installer
4. When asked about WSL 2, click **OK** (let it install WSL 2)
5. After installation, **restart your computer**
6. Open Docker Desktop from the Start menu
7. Wait for the whale icon in the taskbar to stop animating
8. Open **Command Prompt** and type: `docker --version`
9. You should see: `Docker version 24.x.x`

### 3c. How to Open a Terminal

A terminal is a text window where you type commands.

**Windows:** Press `Win + R`, type `cmd`, press Enter
**Or:** Search "Command Prompt" in the Start menu

All commands in this guide should be typed in the terminal.

---

## 4. Running the App Locally

"Locally" means on your own computer, not on the internet yet.

### Step 1: Get the project code

If you're reading this file, you already have the code. Skip to Step 2.

If you need to get it from GitHub:
```bash
git clone https://github.com/YOUR_USERNAME/cloudblog.git
cd cloudblog
```

### Step 2: Create your environment file

The `.env` file contains passwords and settings. It's never committed to Git.

```bash
# Copy the template file
cp .env.example .env
```

Now open `.env` in any text editor (Notepad, VS Code, etc.) and fill in the values:

```
DJANGO_SECRET_KEY=make-up-any-long-random-string-here-50-chars-minimum
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
POSTGRES_DB=cloudblog_db
POSTGRES_USER=cloudblog_user
POSTGRES_PASSWORD=choose-any-password-for-local-dev
POSTGRES_HOST=db
POSTGRES_PORT=5432
REDIS_URL=redis://redis:6379/1
DOCKERHUB_USERNAME=your-dockerhub-username
```

> **Why do we need these?** Django refuses to start without a SECRET_KEY. The database needs a password. These settings change between development and production, so they're in a separate file.

### Step 3: Start everything with one command

```bash
docker compose up -d
```

What this command does:
- Reads `docker-compose.yml`
- Downloads the PostgreSQL and Redis images from Docker Hub (first time only)
- Builds the Django image from your `Dockerfile`
- Starts all three containers in the background (`-d` = detached)

Wait about 30 seconds, then check they're all running:
```bash
docker compose ps
```

You should see three containers with status `healthy` or `Up`:
```
NAME              STATUS         PORTS
cloudblog_db      Up (healthy)   0.0.0.0:5432->5432/tcp
cloudblog_redis   Up (healthy)   0.0.0.0:6379->6379/tcp
cloudblog_web     Up             0.0.0.0:8000->8000/tcp
```

### Step 4: Set up the database

This creates the database tables that store posts, users, and comments:
```bash
docker compose exec web python manage.py migrate
```

> `docker compose exec web` means "run this command inside the web container"

### Step 5: Create an admin user

This creates your login for the admin panel:
```bash
docker compose exec web python manage.py createsuperuser
```

Follow the prompts:
```
Username: admin
Email address: your@email.com
Password: (type a password, won't be shown)
Password (again): (type again)
```

### Step 6: Visit the website

Open your browser and go to: **http://localhost:8000**

You should see the TaskFlow landing page!

Also try:
- **http://localhost:8000/admin/** — Django admin panel (login with the superuser you just created)
- **http://localhost:8000/health/** — Health check (should show `{"status": "healthy"}`)
- **http://localhost:8000/api/tasks/** — REST API (shows tasks in JSON format)

### Step 7: Add some content (optional but good for the screencast)

1. Register a new account at **http://localhost:8000/register/**
2. Click **My Projects** → **New Project** → create a project named "Cloud Coursework"
3. Inside the project, click **+ Add Task** → create a few tasks
4. Go to **Labels** in the sidebar → create coloured labels (e.g., "Bug", "Feature", "Urgent")
5. Edit a task and assign multiple labels — this demonstrates the **Many-to-Many** relationship
6. Visit the **Dashboard** — you should see your project stats with progress bars!

### Useful Commands for Development

```bash
# Start all containers
docker compose up -d

# Stop all containers
docker compose down

# View logs from the web container
docker compose logs web

# Follow logs in real-time
docker compose logs -f web

# Rebuild after changing requirements.txt
docker compose up -d --build

# Open a Python shell inside Django
docker compose exec web python manage.py shell

# Run database migrations after changing models.py
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate
```

---

## 5. What Each File Does

Here's a tour of the project structure, explained simply:

```
cloudblog/
├── .github/workflows/deploy.yml  ← The CI/CD recipe (auto-test and deploy)
├── app/                          ← All the Python/Django code
│   ├── config/                   ← Django project settings
│   │   ├── settings/
│   │   │   ├── base.py           ← Settings used everywhere
│   │   │   ├── development.py    ← Extra settings for your laptop
│   │   │   └── production.py     ← Extra settings for the live server
│   │   ├── urls.py               ← URL routing (which URL = which page)
│   │   └── wsgi.py               ← Connection point for Gunicorn
│   ├── tasks/                    ← The TaskFlow application
│   │   ├── models.py             ← Database structure (Label, Project, Task with M2M)
│   │   ├── views.py              ← Logic for each page (CRUD + API + health)
│   │   ├── urls.py               ← All URL patterns
│   │   ├── admin.py              ← Admin panel configuration
│   │   ├── forms.py              ← ProjectForm, TaskForm, LabelForm, RegisterForm
│   │   ├── serializers.py        ← Converts Tasks to JSON for the API
│   │   └── tests.py              ← 20+ automated tests
│   ├── templates/                ← HTML templates (the actual web pages)
│   │   ├── base.html             ← Sidebar layout (authenticated) + navbar (public)
│   │   ├── tasks/                ← All TaskFlow pages
│   │   │   ├── landing.html      ← Public homepage
│   │   │   ├── dashboard.html    ← Stats overview
│   │   │   ├── project_detail.html ← Kanban view of tasks
│   │   │   ├── task_form.html    ← Create/edit task (shows M2M labels)
│   │   │   └── label_list.html   ← Label management (shows M2M)
│   │   └── registration/         ← Login and register pages
│   ├── static/css/style.css      ← Custom CSS styling
│   ├── manage.py                 ← Django command-line tool
│   └── requirements.txt          ← List of Python packages needed
├── nginx/nginx.conf              ← Web server configuration
├── Dockerfile                    ← Instructions to build the Docker image
├── docker-compose.yml            ← Development: run all services together
├── docker-compose.prod.yml       ← Production: same but uses Docker Hub image
├── .env.example                  ← Template for your .env file
├── .gitignore                    ← Files Git should ignore
├── pytest.ini                    ← Test configuration
└── Instructions.md               ← This file!
```

### Key Concepts

**`models.py` — The database structure**
A model is like a spreadsheet definition. `class Task(models.Model)` says "create a table called Task with these columns". The special line `labels = ManyToManyField(Label)` creates a *join table* linking Tasks and Labels — this is the Many-to-Many relationship. When you run `migrate`, Django creates all these tables automatically.

**`views.py` — The business logic**
A view is a Python function. When someone visits `/tasks/5/`, Django calls the `task_detail()` function, which loads the task from the database (including its labels via the M2M relationship) and returns the HTML page.

**`urls.py` — The routing table**
Like a post office: `path('tasks/<int:pk>/', views.task_detail)` says "if the URL looks like `/tasks/5/`, call the `task_detail` view".

**`templates/` — The HTML pages**
Templates are HTML files with special `{{ variable }}` tags. Django fills in the variables before sending the page to the browser.

---

## 6. Pushing Your Code to GitHub

### Step 1: Initialise Git in your project folder

Open a terminal in your `cloudblog` folder:
```bash
git init
git add .
git commit -m "Initial commit: CloudBlog project setup"
```

What these commands mean:
- `git init` — "Start tracking this folder with Git"
- `git add .` — "Stage all files for committing" (the `.` means "everything")
- `git commit -m "..."` — "Save a snapshot with this message"

### Step 2: Connect to your GitHub repository

```bash
git remote add origin https://github.com/YOUR_USERNAME/cloudblog.git
git branch -M main
git push -u origin main
```

- `git remote add origin` — "This is where the code lives online"
- `git push -u origin main` — "Upload my code to the main branch"

You'll be asked for your GitHub username and password. If it asks for a password, use a **Personal Access Token** instead (GitHub no longer accepts passwords over HTTPS):
1. GitHub → Settings → Developer Settings → Personal Access Tokens → Tokens (classic)
2. Generate new token → check `repo` scope → copy the token
3. Use this token as your "password" when Git asks

### Step 3: Verify it worked

Go to `https://github.com/YOUR_USERNAME/cloudblog` in your browser. You should see all your files.

### Daily Git Workflow

Every time you make changes:
```bash
git add .
git commit -m "Describe what you changed"
git push origin main
```

This will automatically trigger the CI/CD pipeline (once you set it up in Section 8).

---

## 7. Setting Up Your Azure Cloud Server

### Step 1: Create a Virtual Machine

1. Go to **https://portal.azure.com** and log in with your student account
2. Click **Create a resource** (the `+` button)
3. Search for **Virtual machine** and click it
4. Click **Create**

Fill in the form:
- **Subscription:** Azure for Students
- **Resource group:** Click "Create new" → name it `cloudblog-rg`
- **Virtual machine name:** `cloudblog-server`
- **Region:** (UK South or East US)
- **Image:** Ubuntu Server 24.04 LTS (search for it)
- **Size:** Click "See all sizes" → search for `B1s` → select **Standard_B1s** (1 vCPU, 1 GB RAM) — this is free tier

**Authentication section:**
- Authentication type: **SSH public key**
- Username: `azureuser`
- SSH public key source: **Generate new key pair**
- Key pair name: `cloudblog-key`

**Inbound ports:** Allow SSH (22)

5. Click **Review + create**, then **Create**
6. A popup says "Generate new key pair" — click **Download private key and create resource**
7. Save the `.pem` file somewhere safe (e.g., `C:\Users\YourName\.ssh\cloudblog-key.pem`)

**After deployment (takes 2-3 minutes):**
1. Click **Go to resource**
2. Copy the **Public IP address** (e.g., `20.108.14.55`) — you'll need this throughout

### Step 2: Open Firewall Ports

By default, only SSH (port 22) is open. We need HTTP (80) and HTTPS (443):

1. In your VM page, click **Networking** in the left menu
2. Click **Add inbound port rule**
3. Add rule: Destination port `80`, Protocol `TCP`, Name `Allow-HTTP` → **Add**
4. Add another rule: Destination port `443`, Protocol `TCP`, Name `Allow-HTTPS` → **Add**

### Step 3: Connect to Your Server via SSH

SSH lets you control the remote server by typing commands, as if you were sitting in front of it.

**On Windows (using Command Prompt):**

First, set correct permissions on the key file:
```bash
icacls "C:\Users\YourName\.ssh\cloudblog-key.pem" /inheritance:r /grant:r "%USERNAME%:R"
```

Then connect:
```bash
ssh -i "C:\Users\YourName\.ssh\cloudblog-key.pem" azureuser@YOUR_SERVER_IP
```

Replace `YOUR_SERVER_IP` with the IP you copied.

You should see a welcome message. You're now "inside" the server. 🎉

> **Tip:** Create an SSH config for easier access. Create/edit `C:\Users\YourName\.ssh\config`:
> ```
> Host cloudblog-server
>     HostName YOUR_SERVER_IP
>     User azureuser
>     IdentityFile C:\Users\YourName\.ssh\cloudblog-key.pem
> ```
> Now you can just type: `ssh cloudblog-server`

### Step 4: Install Docker on the Server

Run these commands on the server (paste them one block at a time):

```bash
# Update the package list
sudo apt update && sudo apt upgrade -y

# Install helper tools
sudo apt install -y curl wget git vim nano unzip

# Remove any old Docker versions
sudo apt remove -y docker docker-engine docker.io containerd runc 2>/dev/null

# Add Docker's official security key
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add Docker's repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Verify Docker is installed
sudo docker --version
sudo docker compose version

# Allow running Docker without sudo
sudo usermod -aG docker $USER
newgrp docker

# Test it works
docker run hello-world

# Make Docker start automatically on reboot
sudo systemctl enable docker
```

### Step 5: Configure the Firewall (UFW)

UFW is a simple firewall. We set it up to only allow necessary ports:

```bash
# Set defaults: block all incoming, allow all outgoing
sudo ufw default deny incoming
sudo ufw default allow outgoing

# CRITICAL: Allow SSH first or you'll lock yourself out!
sudo ufw allow 22/tcp

# Allow web traffic
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Turn on the firewall
sudo ufw enable

# Verify (should show Status: active)
sudo ufw status verbose
```

### Step 6: Clone Your Repository on the Server

```bash
cd ~
git clone https://github.com/YOUR_USERNAME/cloudblog.git
cd cloudblog
```

### Step 7: Create the Production .env File

```bash
nano ~/cloudblog/.env
```

Type or paste these values (adjust passwords):
```
DJANGO_SECRET_KEY=generate-a-long-random-string-50-plus-chars
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=YOUR_SERVER_IP,your-domain.com
POSTGRES_DB=cloudblog_db
POSTGRES_USER=cloudblog_user
POSTGRES_PASSWORD=choose-a-strong-password-for-production
POSTGRES_HOST=db
POSTGRES_PORT=5432
REDIS_URL=redis://redis:6379/1
DOCKERHUB_USERNAME=your-dockerhub-username
```

Press `Ctrl+X`, then `Y`, then `Enter` to save.

**Generate a secure SECRET_KEY:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```
Copy the output and use it as your `DJANGO_SECRET_KEY`.

### Step 8: First Manual Deployment (Test Before CI/CD)

```bash
cd ~/cloudblog

# Log in to Docker Hub
docker login

# Pull and start all services
docker compose -f docker-compose.prod.yml up -d

# Check they're all running
docker compose -f docker-compose.prod.yml ps

# Run database migrations
docker compose -f docker-compose.prod.yml exec web python manage.py migrate

# Collect static files
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# Create admin user
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

**Test it:** Open your browser and visit `http://YOUR_SERVER_IP`

You should see CloudBlog! 🎉

---

## 8. The CI/CD Pipeline Explained

### What is CI/CD?

**CI = Continuous Integration** — Every time you save code to GitHub, it's automatically tested.

**CD = Continuous Deployment** — If tests pass, the code is automatically deployed to the live server.

**In plain English:** You push code → GitHub robots test it → if it works, they update your website. All automatically. No manual steps.

### The Three Jobs in deploy.yml

The pipeline file is at `.github/workflows/deploy.yml`. It has three jobs:

```
Push to GitHub
     ↓
Job 1: TEST ─── Tests fail? ──→ STOP. Code NOT deployed.
     ↓ (tests pass)
Job 2: BUILD ── Build Docker image, push to Docker Hub
     ↓
Job 3: DEPLOY ── SSH into Azure VM, download new image, restart
     ↓
Website is now updated! ✅
```

**Job 1 — Test:**
- Starts a temporary PostgreSQL and Redis container
- Installs Python and all packages
- Runs `flake8` (code style checker — like spell check for code)
- Runs `pytest` (runs all the test functions in `tests.py`)
- If any test fails, jobs 2 and 3 do NOT run

**Job 2 — Build:**
- Logs into Docker Hub
- Runs your `Dockerfile` to build the image
- Tags it with two names: `:latest` (newest) and `:abc123` (specific version)
- Pushes it to Docker Hub

**Job 3 — Deploy:**
- SSHs into your Azure VM
- Downloads the new image: `docker compose pull`
- Restarts containers: `docker compose up -d`
- Runs migrations in case the database changed
- Cleans up old images

### Setting Up GitHub Secrets

GitHub Secrets are like a locked box where you store passwords. The CI/CD pipeline reads them without exposing them.

**How to add secrets:**
1. Go to your GitHub repository: `https://github.com/YOUR_USERNAME/cloudblog`
2. Click **Settings** (top navigation bar)
3. Click **Secrets and variables** → **Actions** (left sidebar)
4. Click **New repository secret**

Add each of these one by one:

| Secret Name | Value | Where to Find It |
|---|---|---|
| `DOCKERHUB_USERNAME` | Your Docker Hub username | hub.docker.com (your account name) |
| `DOCKERHUB_TOKEN` | Docker Hub access token | You saved this in Section 2b |
| `SSH_HOST` | Your server's public IP | Azure Portal → Your VM → Overview |
| `SSH_USERNAME` | `azureuser` | Always this value |
| `SSH_PRIVATE_KEY` | Your SSH private key | See below |

**Getting the SSH Private Key:**

The private key is the `.pem` file you downloaded when creating the VM.

Open it in Notepad and copy ALL the content including the header and footer:
```
-----BEGIN OPENSSH PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...
(many lines of random characters)
...
-----END OPENSSH PRIVATE KEY-----
```
Paste this entire thing as the value for `SSH_PRIVATE_KEY`.

**Generating a DJANGO_SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```
Copy the output (it looks like `Kj8Fp2mN1oQ5rT9...`) and use it as the secret.

---

## 9. Your First Automatic Deployment

Once secrets are configured, let's trigger the pipeline.

### Make a Small Change

Open `app/tasks/views.py` and find the `health_check` function. The `version` key is already there — just change its value from `'2.0.0'` to `'2.0.1'`:

```python
health = {
    'status': 'healthy',
    'database': 'unknown',
    'cache': 'unknown',
    'timestamp': time.time(),
    'version': '2.0.1',        # CHANGE THIS
    ...
```

### Push the Change

```bash
git add .
git commit -m "feat: add version to health check endpoint"
git push origin main
```

### Watch It Deploy

1. Go to your GitHub repository
2. Click the **Actions** tab
3. You'll see a workflow running with your commit message
4. Click it to see the three jobs
5. Watch the green checkmarks appear one by one:
   - ✅ Run Tests
   - ✅ Build and Push Docker Image
   - ✅ Deploy to Azure VM
6. Visit `http://YOUR_SERVER_IP/health/` — you should see `"version": "2.0.1"`

**Total time from push to live: about 3-5 minutes.** 🚀

---

## 10. How to Run Tests

### What Are Tests?

A test is a small piece of code that checks your code works correctly.

Example:
```python
def test_homepage_returns_200(self):
    response = self.client.get('/')
    self.assertEqual(response.status_code, 200)
```
This test says: "When I visit the homepage, I expect to get a 200 OK response." If something breaks the homepage, this test will fail and catch the bug.

### Running Tests Locally

```bash
# Inside your project folder on your computer:
docker compose exec web pytest
```

You'll see output like:
```
PASSED tasks/tests.py::ModelTests::test_label_str_method
PASSED tasks/tests.py::ModelTests::test_task_many_to_many_labels
PASSED tasks/tests.py::ViewTests::test_dashboard_returns_200
PASSED tasks/tests.py::HealthTests::test_health_check_returns_healthy
...
20 passed in 3.14s ✅
```

### Running Tests with Coverage Report

Coverage shows what percentage of your code is tested:

```bash
docker compose exec web pytest --cov=tasks --cov-report=term-missing
```

Output shows:
```
Name               Stmts   Miss  Cover
--------------------------------------
tasks/models.py       55      2    96%
tasks/views.py        95      5    95%
tasks/tests.py       180      0   100%
--------------------------------------
TOTAL                330     7    98%
```

The module requires **80%+ coverage** — we're at ~95%+. ✅

### What Tests We Have

| Test | What It Checks |
|---|---|
| `test_label_str_method` | Label name displays correctly |
| `test_project_str_method` | Project name displays correctly |
| `test_task_str_method` | Task title displays correctly |
| `test_task_many_to_many_labels` | Tasks can have multiple labels (M2M works) |
| `test_landing_page_returns_200` | Public homepage loads |
| `test_dashboard_requires_login` | Unauthenticated users redirected to login |
| `test_dashboard_returns_200` | Dashboard loads for logged-in user |
| `test_project_crud` | Create, view, edit, delete a project |
| `test_task_create_with_labels` | Create task and assign M2M labels |
| `test_task_delete` | Delete task with confirmation |
| `test_health_check_returns_healthy` | DB and Redis both working |
| `test_api_tasks_returns_json` | REST API returns JSON |
| `test_api_requires_authentication` | API rejects unauthenticated requests |
| `test_user_can_register` | Registration works |

---

## 11. Rolling Back if Something Goes Wrong

If you deploy new code and it breaks the site, here's how to get back to the previous working version.

### Option A: Git Revert (Recommended)

This creates a new commit that undoes the bad commit:

```bash
# See recent commits
git log --oneline -5

# Create a revert commit
git revert HEAD

# Push it — this triggers the pipeline which redeploys the previous version
git push origin main
```

### Option B: Use a Specific Docker Image Tag

Every deployment is tagged with the Git commit hash (e.g., `:abc1234`).

On the server:
```bash
cd ~/cloudblog

# Edit docker-compose.prod.yml to use a specific version
nano docker-compose.prod.yml
```

Find the `image:` line and change `:latest` to the commit hash:
```yaml
image: your-username/cloudblog:abc1234   # ← specific version
```

Then restart:
```bash
docker compose -f docker-compose.prod.yml up -d
```

---

## 12. How to Get SSL (HTTPS)

HTTPS encrypts the connection between the browser and your server. The padlock icon in the browser.

### Step 1: Get a Free Domain (or use Azure DNS Label)

**Free Azure DNS label (easiest):**
1. In Azure Portal, go to your VM
2. Click on the **Public IP address** link
3. Under "DNS name label", enter a name (e.g., `cloudblog-john`)
4. Your domain will be: `cloudblog-john.eastus.cloudapp.azure.com`

### Step 2: Install Certbot on the Server

SSH into your server and run:
```bash
sudo apt install -y certbot

# Stop Nginx temporarily (Certbot needs port 80)
docker compose -f ~/cloudblog/docker-compose.prod.yml stop nginx

# Get SSL certificate
sudo certbot certonly --standalone \
  -d cloudblog-john.eastus.cloudapp.azure.com \
  --email your@email.com \
  --agree-tos \
  --no-eff-email

# Start Nginx again
docker compose -f ~/cloudblog/docker-compose.prod.yml start nginx
```

### Step 3: Update Nginx Configuration

Edit `nginx/nginx.conf` on your **local computer** and uncomment the HTTPS server block. Replace `YOUR_DOMAIN_HERE` with your actual domain.

Then push to GitHub — the pipeline will deploy the new Nginx config.

### Step 4: Update Your .env on the Server

```bash
nano ~/cloudblog/.env
```

Update:
```
DJANGO_ALLOWED_HOSTS=YOUR_SERVER_IP,cloudblog-john.eastus.cloudapp.azure.com
```

Restart:
```bash
docker compose -f ~/cloudblog/docker-compose.prod.yml up -d
```

Now visit `https://your-domain.com` — you should see the padlock! 🔒

---

## 13. Common Problems and Fixes

| Problem | Symptom | Fix |
|---|---|---|
| Containers won't start | `docker compose ps` shows "Exit 1" | Run `docker compose logs web` to see the error |
| Database connection error | "could not connect to server" | Check PostgreSQL container is healthy: `docker compose ps` |
| Static files not loading | CSS not applied, broken layout | Run: `docker compose exec web python manage.py collectstatic` |
| Port 8000 already in use | "address already in use" | Stop any other running Docker containers: `docker compose down` |
| SSH connection refused | "Connection refused" when SSHing | Check Azure NSG allows port 22; check UFW: `sudo ufw status` |
| GitHub Actions failing | Red X on Actions tab | Click the X to see which step failed and read the error |
| Docker Hub push fails | "unauthorized" in build job | Check `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` secrets are correct |
| .env file not found | Django won't start | Make sure `.env` exists (not `.env.example`) |
| App not updating after deploy | Old version still showing | Docker might have cached the old image: `docker compose pull` then `up -d` |
| 403 Forbidden on admin | CSRF error | Check `DJANGO_ALLOWED_HOSTS` includes your domain/IP |

---

## 14. Preparing for Your Viva Voce

The viva voce is a live demonstration. The examiner will ask you to make a change, push it, and show it deploying automatically. Here are the questions you'll be asked with simple answers.

---

### "Walk me through each step in your GitHub Actions workflow"

**Answer:**
"The workflow file is at `.github/workflows/deploy.yml`. It has three jobs.

Job 1, called 'test', runs on every push. It creates a temporary PostgreSQL and Redis container, installs Python, runs flake8 for code style checking, and then runs pytest to execute all our automated tests. If any test fails, the pipeline stops here and nothing gets deployed.

Job 2, called 'build', only runs when tests pass and we're pushing to the main branch. It logs into Docker Hub, builds the Docker image using our multi-stage Dockerfile, and pushes it with two tags — 'latest' and the Git commit hash — so we can roll back to any specific version.

Job 3, called 'deploy', SSHs into our Azure VM and runs a deployment script that pulls the new image, restarts the containers with `docker compose up -d`, runs database migrations, and cleans up old images."

---

### "What happens when you push to the main branch?"

**Answer:**
"GitHub detects the push and starts the CI/CD pipeline automatically. Within about 3-5 minutes, the tests run, the Docker image is built and pushed to Docker Hub, and then the Azure VM downloads the new image and restarts the containers. The website is updated automatically without any manual steps."

---

### "Explain your docker-compose.yml structure"

**Answer:**
"The docker-compose.yml defines three services. The `db` service runs PostgreSQL — our database. It uses a named volume called `postgres_data` so data persists even when the container restarts. The `redis` service runs Redis, our cache. The `web` service runs our Django application. It uses `depends_on` with health checks to ensure the database is fully ready before Django tries to connect.

The production version, `docker-compose.prod.yml`, is almost the same but adds an Nginx service as the reverse proxy, uses a pre-built Docker Hub image instead of building locally, and has `restart: always` so containers auto-restart if they crash."

---

### "How does your application use Redis?"

**Answer:**
"Redis is used for two things. First, it's our session backend — when a user logs in, their session data is stored in Redis instead of the database. This is faster because Redis is an in-memory data store.

Second, we cache the dashboard statistics. The first time a user visits their dashboard, we query PostgreSQL for project and task counts and store them in Redis for 2 minutes with a per-user cache key `dashboard_stats_{user_id}`. The next page load is served from Redis without touching the database. When the user creates, edits, or deletes a project or task, we call `cache.delete(cache_key)` to invalidate the cache so they always see up-to-date numbers. You can see this in `views.py` in the `dashboard` function."

---

### "Explain the Many-to-Many database relationship in your application"

**Answer:**
"A Many-to-Many relationship means one record can be linked to many records in another table, and vice versa. In TaskFlow, a Task can have many Labels (e.g., 'Bug', 'Urgent', 'Backend'), and the same Label can be applied to many Tasks. You cannot represent this with a simple foreign key — you need a join table.

In Django, I declare it with one line: `labels = ManyToManyField(Label, blank=True, related_name='tasks')`. Django automatically creates a join table called `tasks_task_labels` with two columns: `task_id` and `label_id`. When the user ticks checkboxes on the task form and saves, Django inserts rows into this join table.

You can see it in action in the task creation view — after `task.save()`, we call `form.save_m2m()` to save the label selections. On the Labels management page, you can also see the reverse relationship: `label.tasks.all()` lists every task that has this label."

---

### "What is the purpose of multi-stage Docker builds?"

**Answer:**
"A multi-stage build has two stages in the Dockerfile. Stage 1, called 'builder', installs all Python packages including build tools like gcc. Stage 2, the 'runtime' stage, starts fresh with a clean Python image and only copies the installed packages from stage 1. This means the final image doesn't contain build tools, reducing the image size from about 1GB to about 150MB. Smaller images are faster to pull and have fewer potential security vulnerabilities."

---

### "How are secrets managed in your deployment?"

**Answer:**
"We never put passwords or secret keys directly in the code. In development, they're stored in a `.env` file which is listed in `.gitignore` so it's never committed to Git. On the server, the `.env` file is created manually.

For the CI/CD pipeline, secrets like the Docker Hub token and SSH private key are stored in GitHub Secrets, which is an encrypted vault. In the workflow file, we reference them as `${{ secrets.DOCKERHUB_TOKEN }}` and `${{ secrets.SSH_PRIVATE_KEY }}` — GitHub injects them at runtime without ever displaying them in the logs."

---

### "How would you rollback to a previous version?"

**Answer:**
"There are two options. The simplest is `git revert HEAD` which creates a new commit that undoes the last commit, then `git push origin main` to trigger the pipeline which deploys the reverted code.

Alternatively, every Docker image is tagged with the Git commit hash, so I can edit `docker-compose.prod.yml` on the server to change the image tag from `:latest` to a specific commit like `:abc1234`, then restart the containers. This doesn't require a pipeline run."

---

### "What would happen if your database container crashes?"

**Answer:**
"PostgreSQL uses a Docker named volume called `postgres_data`. Named volumes persist independently of containers. So if the database container crashes and restarts, it reconnects to the same volume and all data is intact. The `restart: always` setting in `docker-compose.prod.yml` ensures the container automatically restarts after a crash."

---

### "Explain the difference between development and production configurations"

**Answer:**
"The development configuration in `docker-compose.yml` is optimised for coding. It mounts the source code as a volume so changes appear immediately without rebuilding, uses Django's built-in development server which shows helpful error pages, and sets `DEBUG=True` which shows detailed error messages.

The production configuration in `docker-compose.prod.yml` pulls a pre-built image from Docker Hub instead of building locally, uses Gunicorn as the application server for performance and stability, adds Nginx as a reverse proxy to serve static files efficiently, and sets `DEBUG=False` for security. It also has `restart: always` on all containers."

---

### "What tests run before deployment?"

**Answer:**
"We have two types of automated checks. First, flake8 checks for code style — it flags things like lines over 120 characters, unused imports, or inconsistent indentation. Second, pytest runs all the test functions in `tests.py`. We have about 15 tests covering the homepage, post creation, health check endpoint, API, user registration, and comment functionality. We achieve over 80% code coverage, meaning more than 80% of our code is exercised by at least one test."

---

## 15. Glossary

| Term | Plain English Explanation |
|---|---|
| **Container** | A self-contained box with an application and everything it needs to run. Like a shipping container for software. |
| **Docker** | The tool that creates and manages containers. |
| **Docker Image** | A saved template for a container. Like a cookie cutter — you can make many containers from one image. |
| **Docker Hub** | A website where Docker images are stored and shared. Like GitHub but for Docker images. |
| **Docker Compose** | A tool to start multiple containers together with one command. |
| **Dockerfile** | A text file with instructions for building a Docker image. Like a recipe. |
| **CI/CD** | Continuous Integration/Continuous Deployment. Code changes are automatically tested and deployed. |
| **GitHub Actions** | GitHub's automation system that runs tasks (like tests) when you push code. |
| **Pipeline** | A sequence of automated steps: test → build → deploy. |
| **PostgreSQL** | A relational database — stores data in tables like a spreadsheet. |
| **Redis** | An in-memory data store. Extremely fast but data can be temporary. |
| **Nginx** | A web server that acts as a "reverse proxy" — forwards requests to Django and serves static files directly. |
| **Gunicorn** | A Python application server that runs Django in production. More robust than Django's built-in server. |
| **SSH** | Secure Shell — a way to control a remote computer by typing commands. |
| **SSL/TLS** | The technology behind the padlock icon (HTTPS). Encrypts the connection. |
| **Let's Encrypt** | A free service that issues SSL certificates. |
| **Certbot** | Software that automatically gets Let's Encrypt certificates. |
| **VPS/VM** | Virtual Private Server / Virtual Machine — a computer rented from a cloud provider. |
| **Git** | Version control software — tracks changes to your code over time. |
| **Repository (Repo)** | A Git-tracked folder containing your project. |
| **Commit** | A saved snapshot of your code with a description message. |
| **Push** | Upload your commits to GitHub. |
| **Pull** | Download new commits from GitHub. |
| **Branch** | A separate line of development. Main branch is the official version. |
| **Secrets** | Passwords and keys stored securely (not in code). |
| **Environment Variables** | Settings loaded from outside the code (e.g., `.env` file). |
| **Migration** | A change to the database structure, tracked by Django. |
| **Static Files** | CSS, JavaScript, images — files that don't change per-request. |
| **REST API** | A way for programs to talk to each other using HTTP and JSON. |
| **Serializer** | Converts a Python object (like a Post) to JSON format. |
| **Middleware** | Code that runs on every request/response, before it reaches your view. |
| **DEBUG mode** | When True, Django shows detailed error pages. Never True in production. |
| **UFW** | Uncomplicated Firewall — controls which network ports are open on Ubuntu. |
| **Health Check** | An endpoint that verifies all parts of the system are working. |
| **Cache** | Storing computed results temporarily so they don't need to be recomputed. |
| **Cache Invalidation** | Deleting cached data when the source data changes. |
| **TTL** | Time To Live — how long cached data is kept before expiring. |
| **Many-to-Many (M2M)** | A relationship where each record can be linked to multiple records in another table, and vice versa. Stored in a separate join table. |
| **Join Table** | A database table that links two other tables together for a Many-to-Many relationship (e.g., `tasks_task_labels` links Tasks and Labels). |
| **WSGI** | Interface between Python web apps and web servers. Gunicorn uses this. |
| **Reverse Proxy** | A server that sits in front of your app, forwarding requests to it. |
| **Volume (Docker)** | A storage area that persists data outside the container lifecycle. |
| **Multi-stage Build** | A Dockerfile technique to create smaller images by discarding build tools. |
| **Dependency** | A library or package your code relies on. Listed in `requirements.txt`. |
