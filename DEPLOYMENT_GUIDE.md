# CreativePulse AI - Deployment Guide

## Production Deployment Checklist

### Prerequisites
- PostgreSQL 13+ server
- Python 3.9+ runtime
- Node.js 18+ runtime
- Domain name with SSL certificate
- Cloudinary account (optional)

## Backend Deployment

### 1. Environment Configuration

Create production `.env` file:
```bash
# Database
DATABASE_URL=postgresql://user:password@host:5432/creativepulse_prod

# Security
SECRET_KEY=<generate-secure-random-key-min-32-chars>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Cloudinary (Optional)
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

**Generate SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. Database Setup

```bash
# Create database
createdb creativepulse_prod

# Run migrations
cd backend
alembic upgrade head
```

### 3. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 4. Run with Production Server

**Using Gunicorn (Recommended):**
```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000
```

**Using Uvicorn:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 5. Backend Service (systemd)

Create `/etc/systemd/system/creativepulse-backend.service`:
```ini
[Unit]
Description=CreativePulse AI Backend
After=network.target postgresql.service

[Service]
Type=notify
User=www-data
WorkingDirectory=/var/www/creativepulse/backend
Environment="PATH=/var/www/creativepulse/venv/bin"
EnvironmentFile=/var/www/creativepulse/backend/.env
ExecStart=/var/www/creativepulse/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable creativepulse-backend
sudo systemctl start creativepulse-backend
sudo systemctl status creativepulse-backend
```

## Frontend Deployment

### 1. Environment Configuration

Create `frontend/.env.production`:
```bash
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

### 2. Build for Production

```bash
cd frontend
npm install
npm run build
```

### 3. Deploy Options

**Option A: Static Export (Vercel, Netlify, AWS S3)**
```bash
npm run build
# Deploy the .next folder or export static files
```

**Option B: Node.js Server**
```bash
npm start  # Runs on port 3000
```

**Option C: PM2 Process Manager**
```bash
npm install -g pm2
pm2 start npm --name "creativepulse-frontend" -- start
pm2 save
pm2 startup
```

### 4. Frontend Service (systemd)

Create `/etc/systemd/system/creativepulse-frontend.service`:
```ini
[Unit]
Description=CreativePulse AI Frontend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/creativepulse/frontend
Environment="NODE_ENV=production"
Environment="PORT=3000"
ExecStart=/usr/bin/npm start
Restart=always

[Install]
WantedBy=multi-user.target
```

## Nginx Configuration

### Backend Proxy

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Frontend Proxy

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_cache_bypass $http_upgrade;
    }
}
```

## Docker Deployment (Optional)

### Backend Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Dockerfile

```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

CMD ["npm", "start"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: creativepulse
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://user:password@postgres:5432/creativepulse
      SECRET_KEY: your-secret-key
    depends_on:
      - postgres

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: http://backend:8000
    depends_on:
      - backend

volumes:
  postgres_data:
```

## Health Checks

### Backend Health
```bash
curl https://api.yourdomain.com/health
# Should return: {"status": "healthy"}
```

### Frontend Health
```bash
curl https://yourdomain.com
# Should return 200 status
```

## Monitoring Setup

### 1. Application Logs

**Backend:**
```bash
# journalctl
sudo journalctl -u creativepulse-backend -f

# PM2
pm2 logs creativepulse-backend
```

**Frontend:**
```bash
# journalctl
sudo journalctl -u creativepulse-frontend -f

# PM2
pm2 logs creativepulse-frontend
```

### 2. Database Monitoring

```sql
-- Active connections
SELECT count(*) FROM pg_stat_activity WHERE datname = 'creativepulse_prod';

-- Table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### 3. Performance Metrics

Monitor:
- API response times
- Database query performance
- Memory usage
- CPU usage
- Disk I/O

Tools:
- New Relic
- DataDog
- Prometheus + Grafana

## Backup Strategy

### Database Backups

```bash
# Daily backup script
#!/bin/bash
BACKUP_DIR="/backups/creativepulse"
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump creativepulse_prod > "$BACKUP_DIR/backup_$DATE.sql"

# Keep only last 30 days
find $BACKUP_DIR -name "backup_*.sql" -mtime +30 -delete
```

Add to crontab:
```bash
0 2 * * * /path/to/backup_script.sh
```

### File Backups

Backup directories:
- `/var/www/creativepulse/backend/.env`
- Application logs
- Uploaded files (if storing locally)

## Security Hardening

### 1. Firewall Configuration

```bash
# Allow SSH, HTTP, HTTPS only
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 2. SSL/TLS Configuration

Use Let's Encrypt:
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### 3. Rate Limiting

Add to Nginx:
```nginx
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

location /api/ {
    limit_req zone=api_limit burst=20 nodelay;
    # ... rest of config
}
```

### 4. Database Security

```sql
-- Create restricted user
CREATE USER creativepulse_app WITH PASSWORD 'strong_password';
GRANT CONNECT ON DATABASE creativepulse_prod TO creativepulse_app;
GRANT USAGE ON SCHEMA public TO creativepulse_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO creativepulse_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO creativepulse_app;
```

## Scaling Considerations

### Horizontal Scaling

1. **Backend**: Run multiple instances behind load balancer
2. **Database**: Use read replicas for analytics queries
3. **Frontend**: Deploy to CDN (Vercel, Cloudflare Pages)
4. **Caching**: Add Redis for session storage and caching

### Vertical Scaling

Recommended minimum specs:
- **Small**: 2 vCPU, 4GB RAM, 50GB SSD
- **Medium**: 4 vCPU, 8GB RAM, 100GB SSD
- **Large**: 8 vCPU, 16GB RAM, 200GB SSD

## Troubleshooting

### Backend Won't Start

```bash
# Check logs
sudo journalctl -u creativepulse-backend -n 50

# Common issues:
# - DATABASE_URL incorrect
# - SECRET_KEY missing
# - Port already in use
```

### Frontend Build Fails

```bash
# Clear cache and rebuild
rm -rf .next node_modules
npm install
npm run build
```

### Database Connection Issues

```bash
# Test connection
psql $DATABASE_URL

# Check PostgreSQL status
sudo systemctl status postgresql
```

### High Memory Usage

```bash
# Check process memory
ps aux | grep -E 'python|node'

# Reduce workers if needed
# Backend: gunicorn -w 2 (instead of 4)
# Frontend: NODE_OPTIONS=--max-old-space-size=2048 npm start
```

## Rollback Procedure

### Code Rollback

```bash
# Using git
cd /var/www/creativepulse
git checkout <previous-commit>
sudo systemctl restart creativepulse-backend
sudo systemctl restart creativepulse-frontend
```

### Database Rollback

```bash
# Restore from backup
psql creativepulse_prod < /backups/creativepulse/backup_20261001_020000.sql

# Or use Alembic downgrade
cd backend
alembic downgrade -1  # One revision back
```

## Post-Deployment Verification

1. ✅ Health endpoints respond
2. ✅ User can sign up and log in
3. ✅ Analysis can be created
4. ✅ Performance data can be uploaded
5. ✅ Analysis execution completes
6. ✅ Creative DNA insights generated
7. ✅ All dashboard pages load
8. ✅ API responses within acceptable latency (<500ms)
9. ✅ SSL certificate valid
10. ✅ Logs are being written

## Support Contacts

- Backend Issues: backend@yourdomain.com
- Frontend Issues: frontend@yourdomain.com
- Infrastructure: devops@yourdomain.com
- Security: security@yourdomain.com
