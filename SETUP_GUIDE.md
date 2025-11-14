# 🚀 Cloud Storage System - Complete Setup Guide

## 📋 Table of Contents
1. [Prerequisites](#prerequisites)
2. [Quick Start with Docker](#quick-start-with-docker)
3. [Manual Setup](#manual-setup)
4. [Testing the System](#testing-the-system)
5. [Deploy to Production](#deploy-to-production)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software
- Python 3.9+
- PostgreSQL 13+
- Docker & Docker Compose (recommended)
- Git

### Optional (for manual setup)
- MinIO Server
- virtualenv

---

## 🐳 Quick Start with Docker (RECOMMENDED)

### Step 1: Clone and Setup

```bash
# Create project directory
mkdir cloud-storage-pro
cd cloud-storage-pro

# Create all files
# Copy all artifacts into respective files:
# - app.py
# - index.html
# - docker-compose.yml
# - Dockerfile
# - requirements.txt
# - database.sql
# - .env
```

### Step 2: Configure Environment

```bash
# Edit .env file
nano .env

# Update these values:
JWT_SECRET=your-random-secret-key-here
STRIPE_SECRET_KEY=sk_test_your_stripe_key
```

### Step 3: Start All Services

```bash
# Start all containers
docker-compose up -d

# Check if all services are running
docker-compose ps

# View logs
docker-compose logs -f backend
```

### Step 4: Access the Application

- **Frontend**: Open `index.html` in browser
- **Backend API**: http://localhost:5000
- **MinIO Console**: http://localhost:9001 (admin/minioadmin)
- **PostgreSQL**: localhost:5432

### Step 5: Verify Setup

```bash
# Test backend API
curl http://localhost:5000

# Check database
docker exec -it cloud_storage_db psql -U postgres -d cloud_storage -c "SELECT * FROM users;"

# Check MinIO
docker exec -it cloud_storage_minio mc ls local/user-files
```

---

## 🔧 Manual Setup (Without Docker)

### Step 1: Install PostgreSQL

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

**macOS:**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Windows:**
Download from https://www.postgresql.org/download/windows/

### Step 2: Setup Database

```bash
# Login to PostgreSQL
sudo -u postgres psql

# Run SQL commands
CREATE DATABASE cloud_storage;
\c cloud_storage
\i database.sql
\q
```

### Step 3: Install MinIO

**Linux:**
```bash
wget https://dl.min.io/server/minio/release/linux-amd64/minio
chmod +x minio
./minio server ./minio-data --console-address ":9001"
```

**macOS:**
```bash
brew install minio/stable/minio
minio server ./minio-data --console-address ":9001"
```

**Windows:**
Download from https://min.io/download

### Step 4: Setup Python Backend

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your configurations

# Run backend
python app.py
```

### Step 5: Setup Frontend

```bash
# Option 1: Direct file access
# Open index.html in browser

# Option 2: Use Python HTTP server
python -m http.server 8000
# Access: http://localhost:8000

# Option 3: Use Node.js http-server
npx http-server -p 8000
```

---

## 🧪 Testing the System

### 1. Create Test User

```bash
curl -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123"
  }'
```

### 2. Login

```bash
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'
```

Save the returned token!

### 3. Upload File

```bash
curl -X POST http://localhost:5000/api/upload \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -F "file=@/path/to/your/file.jpg"
```

### 4. Test via Browser

1. Open `index.html`
2. Register new account
3. Login
4. Upload a file
5. Check dashboard
6. Try upgrade plan

---

## 🌐 Deploy to Production

### Option 1: Railway (Easiest)

```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login
railway login

# 3. Initialize project
railway init

# 4. Add PostgreSQL
railway add --service postgresql

# 5. Add MinIO (use external service like Backblaze B2)

# 6. Deploy
railway up

# 7. Set environment variables
railway variables set JWT_SECRET=your-secret
railway variables set DATABASE_URL=postgresql://...
```

### Option 2: DigitalOcean App Platform

1. Push code to GitHub
2. Connect GitHub repo to DigitalOcean
3. Add PostgreSQL managed database
4. Configure environment variables
5. Deploy!

### Option 3: AWS (Most scalable)

**Architecture:**
- EC2: Backend
- RDS: PostgreSQL
- S3: File storage (instead of MinIO)
- CloudFront: CDN

```bash
# 1. Create EC2 instance
# 2. SSH into instance
ssh -i key.pem ubuntu@your-ec2-ip

# 3. Install dependencies
sudo apt update
sudo apt install python3-pip postgresql-client

# 4. Clone repository
git clone https://github.com/your-repo/cloud-storage.git
cd cloud-storage

# 5. Install Python packages
pip3 install -r requirements.txt

# 6. Setup environment
nano .env
# Update DATABASE_URL with RDS endpoint
# Update MINIO settings to use S3

# 7. Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# 8. Setup Nginx
sudo apt install nginx
# Configure Nginx as reverse proxy
```

**Nginx Config:** `/etc/nginx/sites-available/cloud-storage`
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Option 4: Heroku

```bash
# 1. Install Heroku CLI
# 2. Login
heroku login

# 3. Create app
heroku create cloud-storage-app

# 4. Add PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev

# 5. Set environment variables
heroku config:set JWT_SECRET=your-secret

# 6. Deploy
git push heroku main
```

---

## 🔐 Production Checklist

- [ ] Change all default passwords
- [ ] Use strong JWT_SECRET
- [ ] Enable HTTPS (SSL/TLS)
- [ ] Setup Stripe production keys
- [ ] Configure CORS properly
- [ ] Enable database backups
- [ ] Setup monitoring (Sentry, NewRelic)
- [ ] Configure rate limiting
- [ ] Enable file virus scanning
- [ ] Setup CDN for static files
- [ ] Configure automatic backups
- [ ] Add logging (ELK stack)

---

## 🐛 Troubleshooting

### Backend won't start

```bash
# Check logs
docker-compose logs backend

# Check if port 5000 is available
lsof -i :5000
# Kill process if needed
kill -9 PID
```

### Database connection error

```bash
# Test PostgreSQL connection
docker exec -it cloud_storage_db psql -U postgres

# Check DATABASE_URL in .env
echo $DATABASE_URL
```

### MinIO connection error

```bash
# Check if MinIO is running
docker ps | grep minio

# Access MinIO console
# http://localhost:9001
# Login: minioadmin / minioadmin

# Create bucket manually
docker exec -it cloud_storage_minio mc mb local/user-files
```

### CORS errors

```python
# In app.py, ensure CORS is configured:
from flask_cors import CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})
```

### File upload fails

```bash
# Check MinIO bucket exists
docker exec -it cloud_storage_minio mc ls local/

# Check user storage limit
# Login to psql and check users table
```

### JWT token expired

```python
# Increase token expiration in app.py:
'exp': datetime.utcnow() + timedelta(days=30)
```

---

## 📊 Monitoring & Logs

### View Docker logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f postgres
docker-compose logs -f minio
```

### Database queries

```bash
# Connect to database
docker exec -it cloud_storage_db psql -U postgres -d cloud_storage

# Useful queries
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM files;
SELECT SUM(storage_used) FROM users;
SELECT * FROM transactions ORDER BY created_at DESC LIMIT 10;
```

---

## 🎓 Next Steps

1. **Add Email Notifications**
   - User registration confirmation
   - Storage limit warnings
   - Payment receipts

2. **Implement Real Stripe Integration**
   - Replace mock payment with actual Stripe checkout
   - Add webhooks for subscription management

3. **Add File Sharing**
   - Generate public links
   - Set expiration dates
   - Password protection

4. **Advanced Features**
   - File versioning
   - Team collaboration
   - Mobile app (React Native)
   - Desktop sync client

---

## 📞 Support

If you encounter issues:
1. Check logs: `docker-compose logs`
2. Review troubleshooting section
3. Check GitHub issues
4. Ask on Stack Overflow

---

## 📄 License

MIT License - Feel free to use for your project!