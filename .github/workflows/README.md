# AI Alpha

Full REST API for AI Alpha

## Deployment Workflows

This project uses GitHub Actions workflows for deploying to development and production environments using a self-hosted runner.

### Workflows

1. `deploy-dev.yml`: Deploys to the development environment
2. `deploy-prod.yml`: Deploys to the production environment

### Prerequisites

Before using these workflows, ensure the following are set up:

1. A macOS machine (Sonoma 14.2) with Docker Desktop installed
2. GitHub Actions self-hosted runner installed and configured
3. Necessary environment variables set on the host machine

### Workflow Details

#### Development Deployment (`deploy-dev.yml`)

- Triggered on pushes to the `develop` branch
- Uses `docker-compose.dev.yml` for container orchestration
- Health check on `http://localhost:9002/health`

#### Production Deployment (`deploy-prod.yml`)

- Triggered on pushes to the `main` branch
- Uses `docker-compose.prod.yml` for container orchestration
- Health check on `http://localhost:5000/health`

### Deployment Process

Both workflows follow these steps:

1. Check out the code
2. Navigate to the project directory
3. Pull the latest changes
4. Build and start Docker containers
5. Perform a health check
6. Rollback if the health check fails

## GitHub Actions Self-Hosted Runner Management

### Starting the Runner
```bash
cd /Users/YOU/actions-runner
./run.sh
```

### Installing the Runner as a Service
```bash
sudo ./svc.sh install
sudo ./svc.sh start
```

### Stopping the Runner Service
```bash
sudo ./svc.sh stop
```

### Uninstalling the Runner Service
```bash
sudo ./svc.sh uninstall
```

### Checking Runner Status
```bash
sudo ./svc.sh status
```

Example output:
```
status actions.runner.aialphanovatide-news-bots-v2.news-bot-dev-runner:

/Users/YOU/Library/LaunchAgents/actions.runner.aialphanovatide-news-bots-v2.news-bot-dev-runner.plist

Started:
78695 0 actions.runner.aialphanovatide-news-bots-v2.news-bot-dev-runner
```

### Viewing Runner Logs
```bash
tail -f /var/log/syslog | grep runner
```

### Updating the Runner
```bash
cd /Users/YOU/actions-runner
./run.sh
```

## Docker Installation

To set up the development environment:

```bash
docker compose -f docker-compose.dev.yml up --build
```

## Manual Installation

1. Clone the repository.
2. Create and activate a virtual environment:

   - macOS:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install project dependencies:
```bash
pip install -r requirements.txt
```

## Database Migrations

- Create a new migration:
```bash
alembic revision --autogenerate -m "Description of changes"
```

- Apply upgrades:
```bash
alembic upgrade head
```

- Perform downgrades:
```bash
alembic downgrade -1
```

## Database Migration Workflow

```bash
# Before starting work
git pull
alembic upgrade head

# After making model changes
alembic revision --autogenerate -m "description of changes"

# Before committing
git pull
alembic heads  # Check for multiple heads
```

## Troubleshooting

If deployments fail:

1. Check the GitHub Actions logs in the GitHub repository
2. Verify that the self-hosted runner is online and connected
3. Ensure Docker and docker-compose are properly installed and running
4. Check the project path in the workflow files matches the actual path on the runner machine

## Security Notes

- Regularly update the runner application
- Keep the runner machine's operating system and Docker up to date
- Limit access to the runner machine
- Use repository restrictions for self-hosted runners to limit which repositories can use the runner

For any questions or issues, please contact the DevOps team.