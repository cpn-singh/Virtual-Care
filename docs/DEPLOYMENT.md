# Production Deployment & Operations Guide

**Platform:** Virtual Care Telemedicine Architecture  
**Author:** Platform Infrastructure & DevOps Team

---

## 1. Environment Configurations

Create a secure `.env` file in `backend/` and `frontend/`.

### Backend Configuration (`backend/.env`)

```env
DJANGO_SECRET_KEY=generate-a-strong-random-50-char-key
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=api.yourtelehealth.com,127.0.0.1
DATABASE_URL=postgresql://telehealth_user:securepassword@db-host:5432/telehealth_db
CORS_ALLOWED_ORIGINS=https://app.yourtelehealth.com,https://yourtelehealth.com

# SMTP Email Configuration
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-sendgrid-api-key
DEFAULT_FROM_EMAIL=no-reply@yourtelehealth.com

# Emergency Phone Configuration
EMERGENCY_PHONE_NUMBER=112
AMBULANCE_PHONE_NUMBER=108

# AI & Media Integrations
AI_PROVIDER=rules_and_simulated
```

### Frontend Configuration (`frontend/.env`)

```env
VITE_API_BASE_URL=https://api.yourtelehealth.com/api/v1
```

---

## 2. Docker & Container Deployment

### Running with Gunicorn / Uvicorn

```bash
cd backend
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4 --threads 2
```

### Static File Collection

```bash
python manage.py collectstatic --noinput
```

### Frontend Production Build

```bash
cd frontend
npm install
npm run build
```
Serve the generated `frontend/dist/` directory via NGINX, Cloudflare Pages, or AWS CloudFront/S3.

---

## 3. NGINX Reverse Proxy Example

```nginx
server {
    listen 443 ssl http2;
    server_name api.yourtelehealth.com;

    ssl_certificate /etc/letsencrypt/live/api.yourtelehealth.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourtelehealth.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
