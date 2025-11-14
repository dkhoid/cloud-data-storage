# ☁Cloud Storage - Full Stack Storage Solution

A full-stack cloud storage application with file upload/download, user authentication, subscription management, and analytics.

## 🚀 Quick Start

### Prerequisites
- Docker Desktop installed and running
- Git (optional, for cloning)

### Running the Project

1. **Clone the repository** (if needed):
   ```bash
   git clone <repository-url>
   cd cloud-basic
   ```

2. **Create environment file**:
   Create a `.env` file in the project root with the following variables:
   ```env
   JWT_SECRET=your-secret-key-here
   STRIPE_SECRET_KEY=your-stripe-secret-key
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

### Running Without Docker (Development)

1. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables** in `.env` file

3. **Start PostgreSQL and MinIO** (manually or via Docker)

4. **Run the Flask application**:
   ```bash
   python app.py
   ```

5. **Serve the frontend** using a local server or open `index.html` directly

## 📋 Configuration


### Database Schema

**Tables:**
- `users` - User accounts and subscriptions
- `files` - File metadata
- `transactions` - Payment history
- `usage_history` - Daily storage tracking
- `pricing_plans` - Subscription tiers

## 🔐 API Endpoints

### Authentication
- `POST /api/register` - Register new user
- `POST /api/login` - User login

### Files
- `POST /api/upload` - Upload file
- `GET /api/files` - List user files
- `GET /api/download/<file_id>` - Download file
- `DELETE /api/delete/<file_id>` - Delete file

### User & Billing
- `GET /api/user/info` - Get user info
- `GET /api/pricing` - List pricing plans
- `POST /api/upgrade` - Upgrade subscription
- `GET /api/transactions` - Transaction history
- `GET /api/usage/history` - Usage analytics

### Admin
- `GET /api/admin/stats` - System statistics

