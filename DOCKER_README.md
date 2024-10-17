# AI Alpha Server v2 - Docker Environment Guide

Welcome to the AI Alpha v2 project! This guide will help you set up and manage the Docker environment for both development and production.

## Getting Started

Ensure Docker and Docker Compose are installed on your system.

### Development Environment

Start the development environment:

```bash
docker compose -f docker-compose-dev.yml up -d
```

### Production Environment

Start the production environment:

```bash
docker compose -f docker-compose.yml up -d
```

## Accessing Data

### Redis

Connect to the Redis container:

```bash
docker compose exec redis-dev redis-cli -a ${REDIS_PASSWORD}
```

Example Redis commands:
```
KEYS *
GET key_name
```

### PostgreSQL

Connect to the PostgreSQL container:

```bash
docker compose exec postgres-dev psql -U ${DB_USER} -d ${DB_NAME}_dev
```

Example SQL query:
```sql
SELECT * FROM your_table_name;
```

#### Connecting to PostgreSQL from Another Machine

1. Find the host machine's IP address:
   ```bash
   ip addr show
   ```

2. From another machine, use a PostgreSQL client with these details:
   - Host: <host_machine_ip>
   - Port: 5432
   - User: ${DB_USER}
   - Password: ${DB_PASSWORD}
   - Database: ${DB_NAME}_dev

## Container Management

### View Running Containers
```bash
docker compose ps
```

### View Running Containers Formatted
```bash
docker ps --format "table {{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Status}}"
```

### Clean Up Resources
```bash
docker-compose -f docker-compose-dev.yml down -v --rmi all --remove-orphans
```

### View Container Logs
```bash
docker compose logs -f service_name
```

### Start Specific Service Group
```bash
docker-compose -f docker-compose.dev.yml -p ai-alpha-dev up -d
```

## Volume Management

### List Volumes
```bash
docker volume ls
```

### Inspect a Volume
```bash
docker volume inspect volume_name
```

### Remove a Volume
```bash
docker volume rm volume_name
```

### To remove all unused volumes (including those from other projects)
```bash
docker volume prune
```

### Backup a Volume
```bash
docker run --rm -v volume_name:/source -v $(pwd):/backup alpine tar -czvf /backup/volume_backup.tar.gz -C /source .
```

### Restore a Volume
```bash
docker run --rm -v volume_name:/target -v $(pwd):/backup alpine sh -c "rm -rf /target/* /target/..?* /target/.[!.]* ; tar -xzvf /backup/volume_backup.tar.gz -C /target"
```

## Network Management

### List Networks
```bash
docker network ls
```

### Inspect a Network
```bash
docker network inspect network_name
```

### Remove a Network
```bash
docker network rm network_name
```

## Helpful Tips

- Development environment: PostgreSQL on port 5432, Redis on 6379
- Production environment: PostgreSQL on port 5433, Redis on 6380
- Use environment variables for sensitive information
- Check `docker-compose-dev.yml` and `docker-compose.yml` for detailed configurations

## Troubleshooting

1. Ensure all required environment variables are set
2. Check container logs: `docker compose logs -f service_name`
3. Rebuild containers: `docker compose -f docker-compose-dev.yml up --build -d`
4. Check Docker daemon logs: `sudo journalctl -fu docker.service`
5. Verify network connectivity: `docker network inspect network_name`

## Advanced Commands

### Execute a Command in a Running Container
```bash
docker compose exec service_name command
```

### View Resource Usage
```bash
docker stats
```

### Update a Single Service
```bash
docker compose up -d --no-deps service_name
```

Remember to replace placeholders like `${DB_USER}`, `${DB_PASSWORD}`, `${DB_NAME}`, `volume_name`, `network_name`, and `service_name` with actual values from your setup.


## Database Operations with Docker Volumes

### Importing Data into Docker Volumes

#### For Plain SQL Dumps (.sql files)

Use the `psql` command:

```bash
docker exec -i <container_name> psql -U <username> -d <database_name> -f /path/to/dump.sql
```

Example:
```bash
docker exec -i ai-alpha-dev-postgres-dev-1 psql -U postgres -d ai-alpha-database-replica-dev -f /backups/ai-alpha-database-10-10-2024.sql
```

#### For Custom Format Dumps

Use the `pg_restore` command:

```bash
docker exec -i <container_name> pg_restore -U <username> -d <database_name> -v /path/to/dump
```

Example:
```bash
docker exec -i ai-alpha-dev-postgres-dev-1 pg_restore -U postgres -d ai-alpha-database-replica-dev -v /backups/ai-alpha-database-custom.dump
```

### Exporting Data from Docker Volumes

#### To Plain SQL Format

```bash
docker exec -i <container_name> pg_dump -U <username> -d <database_name> > /path/on/host/dump.sql
```

Example:
```bash
docker exec -i ai-alpha-dev-postgres-dev-1 pg_dump -U postgres -d ai-alpha-database-replica-dev > ./backups/exported_data.sql
```

#### To Custom Format

```bash
docker exec -i <container_name> pg_dump -U <username> -Fc -d <database_name> > /path/on/host/dump.custom
```

Example:
```bash
docker exec -i ai-alpha-dev-postgres-dev-1 pg_dump -U postgres -Fc -d ai-alpha-database-replica-dev > ./backups/exported_data.custom
```

### Notes

- Replace `<container_name>`, `<username>`, `<database_name>`, and file paths with your specific values.
- Ensure the target database exists before importing.
- For large databases, consider adding the `-v` flag for verbose output to monitor progress.
- When exporting, the `>` operator redirects the output to a file on your host machine.
- The `-Fc` flag in the export command creates a custom-format archive suitable for input into pg_restore.

Remember to adjust file permissions if needed, and always backup your data before performing import or export operations.