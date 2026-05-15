# 🚀 Docker Deployment Guide

Complete guide for deploying Legal AI application using Docker.

---

## 📋 Prerequisites

- Docker Desktop installed and running
- Docker Compose installed (comes with Docker Desktop)
- API Keys (Groq or OpenAI)

---

## 🎯 Quick Start

### 1. Configure Environment

Create `.env` file in project root (if not exists):

```bash
# Copy from example
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
# API Keys
GROQ_API_KEY=your_groq_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Model Selection
LLM_PROVIDER=groq
GROQ_MODEL=llama-3.3-70b-versatile
OPENAI_MODEL=gpt-4o

# Database (SQLite - no setup needed)
DATABASE_URL=sqlite:///./data/legal_ai.db

# Paths
CHROMA_DB_PATH=./data/chroma_db
OUTPUTS_PATH=./data/outputs

# Server
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000
```

### 2. Build and Run

```bash
# Build and start all services
docker-compose up --build

# Or run in background (detached mode)
docker-compose up -d --build
```

### 3. Access Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

---

## 🛠️ Docker Commands

### Start Services

```bash
# Start all services
docker-compose up

# Start in background
docker-compose up -d

# Start specific service
docker-compose up api
docker-compose up frontend
```

### Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

### View Logs

```bash
# View all logs
docker-compose logs

# Follow logs (live)
docker-compose logs -f

# View specific service logs
docker-compose logs api
docker-compose logs frontend

# Follow specific service
docker-compose logs -f api
```

### Rebuild Services

```bash
# Rebuild all services
docker-compose build

# Rebuild specific service
docker-compose build api
docker-compose build frontend

# Rebuild and restart
docker-compose up --build
```

### Check Status

```bash
# List running containers
docker-compose ps

# View resource usage
docker stats
```

---

## 🔧 Troubleshooting

### Issue: Port Already in Use

**Error:** `Bind for 0.0.0.0:8000 failed: port is already allocated`

**Solution:**
```bash
# Stop conflicting services
docker-compose down

# Or change port in docker-compose.yml
ports:
  - "8001:8000"  # Use 8001 instead
```

### Issue: Build Fails

**Solution:**
```bash
# Clean build cache
docker-compose build --no-cache

# Remove old images
docker system prune -a
```

### Issue: Database Not Initialized

**Solution:**
```bash
# Stop services
docker-compose down

# Remove volumes
docker-compose down -v

# Restart (will reinitialize)
docker-compose up --build
```

### Issue: Frontend Can't Connect to Backend

**Solution:**

Check `frontend/.env`:
```env
VITE_API_URL=http://localhost:8000
```

Or in `docker-compose.yml`:
```yaml
frontend:
  environment:
    - VITE_API_URL=http://localhost:8000
```

### Issue: OCR Not Working

**Solution:**

Bengali language support is included in Dockerfile:
```dockerfile
RUN apt-get install -y tesseract-ocr tesseract-ocr-ben
```

Rebuild if needed:
```bash
docker-compose build api
```

---

## 📦 Data Persistence

Data is stored in `./data` folder which is mounted as a volume:

```
data/
├── legal_ai.db          # SQLite database
├── chroma_db/           # Vector embeddings
└── outputs/             # Generated documents
```

**Backup Data:**
```bash
# Create backup
tar -czf backup-$(date +%Y%m%d).tar.gz data/

# Restore backup
tar -xzf backup-20260515.tar.gz
```

---

## 🔒 Production Deployment

### 1. Use Production Dockerfile

Create `Dockerfile.prod`:

```dockerfile
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-ben \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create data directories
RUN mkdir -p data/chroma_db data/outputs

# Non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Production server
CMD ["gunicorn", "src.api:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

### 2. Production docker-compose.yml

Create `docker-compose.prod.yml`:

```yaml
services:
  api:
    build:
      context: .
      dockerfile: Dockerfile.prod
    ports:
      - "8000:8000"
    environment:
      - LLM_PROVIDER=${LLM_PROVIDER}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - GROQ_API_KEY=${GROQ_API_KEY}
      - DATABASE_URL=sqlite:///./data/legal_ai.db
      - LOG_LEVEL=WARNING
    volumes:
      - ./data:/app/data
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    ports:
      - "80:80"
    depends_on:
      - api
    restart: always
```

### 3. Deploy

```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Start production services
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

---

## 🌐 Deploy to Cloud

### AWS EC2

```bash
# SSH to EC2 instance
ssh -i key.pem ubuntu@your-ec2-ip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Clone repository
git clone your-repo-url
cd legal_ai

# Configure environment
nano .env

# Deploy
docker-compose up -d --build
```

### DigitalOcean Droplet

```bash
# Create droplet with Docker pre-installed
# SSH to droplet
ssh root@your-droplet-ip

# Clone and deploy
git clone your-repo-url
cd legal_ai
nano .env
docker-compose up -d --build
```

### Google Cloud Run

```bash
# Build and push image
gcloud builds submit --tag gcr.io/PROJECT-ID/legal-ai

# Deploy
gcloud run deploy legal-ai \
  --image gcr.io/PROJECT-ID/legal-ai \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

---

## 📊 Monitoring

### View Resource Usage

```bash
# Real-time stats
docker stats

# Container details
docker-compose ps
docker inspect legal_ai-api-1
```

### Health Checks

```bash
# Check API health
curl http://localhost:8000/health

# Check frontend
curl http://localhost:3000
```

---

## 🔄 Updates

### Update Application

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose down
docker-compose up --build -d
```

### Update Dependencies

```bash
# Update requirements.txt
# Then rebuild
docker-compose build --no-cache api
docker-compose up -d
```

---

## 🧹 Cleanup

```bash
# Stop and remove containers
docker-compose down

# Remove volumes (WARNING: deletes data)
docker-compose down -v

# Remove images
docker rmi legal_ai-api legal_ai-frontend

# Clean everything
docker system prune -a --volumes
```

---

## 📝 Environment Variables Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `LLM_PROVIDER` | LLM provider (openai/groq) | groq | Yes |
| `OPENAI_API_KEY` | OpenAI API key | - | If using OpenAI |
| `GROQ_API_KEY` | Groq API key | - | If using Groq |
| `OPENAI_MODEL` | OpenAI model name | gpt-4o | No |
| `GROQ_MODEL` | Groq model name | llama-3.3-70b-versatile | No |
| `DATABASE_URL` | Database connection | sqlite:///./data/legal_ai.db | No |
| `LOG_LEVEL` | Logging level | INFO | No |
| `API_HOST` | API host | 0.0.0.0 | No |
| `API_PORT` | API port | 8000 | No |

---

## 🆘 Support

For issues or questions:
1. Check logs: `docker-compose logs -f`
2. Verify environment: `docker-compose config`
3. Check health: `curl http://localhost:8000/health`
4. Rebuild: `docker-compose up --build`

---

## ✅ Checklist

Before deployment:
- [ ] Docker Desktop running
- [ ] `.env` file configured with API keys
- [ ] Ports 3000 and 8000 available
- [ ] Sufficient disk space (2GB+)
- [ ] Internet connection for pulling images

After deployment:
- [ ] Backend accessible at http://localhost:8000
- [ ] Frontend accessible at http://localhost:3000
- [ ] API docs at http://localhost:8000/docs
- [ ] Can upload documents
- [ ] Can generate drafts
- [ ] OCR working for images

---

**Happy Deploying! 🚀**
