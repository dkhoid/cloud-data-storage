# ☁Cloud Storage - Full Stack Storage Solution

A full-stack cloud storage application with file upload/download, user authentication, subscription management, and analytics.

## Quick Start

### Prerequisites
- Docker Desktop installed and running
- Git (optional, for cloning)

### Running the Project

1. **Clone the repository** (if needed):
   ```bash
   git clone https://github.com/dkhoid/cloud-data-storage.git
   cd cloud-basic
   ```

2. **Create environment file**:
   Create a `.env` file in the project root with the following variables:
   ```env
   
   ```

3. **Start all services** using Docker Compose:
   ```bash
   docker-compose up -d
   ```

4. **Access the application**:
   - **Frontend**: http://localhost:8080
   - **Backend API**: http://localhost:5000
   - **MinIO Console**: http://localhost:9001 (user: `minioadmin`, password: `minioadmin`)
   - **PostgreSQL**: localhost:5432

### Useful Commands

**Stop all services**:
```bash
docker-compose down
```

**Stop and remove all data** (including volumes):
```bash
docker-compose down -v
```

**View logs**:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f postgres
docker-compose logs -f minio
docker-compose logs -f frontend
```

**Rebuild and restart**:
```bash
docker-compose up -d --build
```

**Check service status**:
```bash
docker-compose ps
```

