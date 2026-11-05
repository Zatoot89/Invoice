# InvoiceFlow Pro - Deployment Guide

## Table of Contents

1. [Deployment Overview](#deployment-overview)
2. [Production Environment Setup](#production-environment-setup)
3. [Docker Deployment](#docker-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Cloud Deployment](#cloud-deployment)
6. [Environment Configuration](#environment-configuration)
7. [SSL/HTTPS Setup](#sslhttps-setup)
8. [Database Migration](#database-migration)
9. [Monitoring and Logging](#monitoring-and-logging)
10. [Backup and Recovery](#backup-and-recovery)
11. [Security Hardening](#security-hardening)
12. [Performance Optimization](#performance-optimization)
13. [Scaling Strategies](#scaling-strategies)
14. [CI/CD Pipeline](#cicd-pipeline)

## Deployment Overview

InvoiceFlow Pro supports multiple deployment strategies:

- **Docker Compose**: Single-server deployment with Docker containers
- **Kubernetes**: Orchestrated deployment with auto-scaling and load balancing
- **Cloud Services**: AWS, Google Cloud, or Azure with managed services
- **Hybrid**: Mix of cloud and on-premise infrastructure

### Architecture Components

```mermaid
graph TB
    subgraph "Load Balancer"
        LB[Nginx/ALB]
    end
    
    subgraph "Application Layer"
        FE1[Next.js Frontend 1]
        FE2[Next.js Frontend 2]
        API1[FastAPI Backend 1]
        API2[FastAPI Backend 2]
        WS[WebSocket Server]
    end
    
    subgraph "Cache Layer"
        REDIS[(Redis Cluster)]
    end
    
    subgraph "Message Queue"
        RMQ[RabbitMQ Cluster]
        CELERY[Celery Workers]
    end
    
    subgraph "Database Layer"
        PG[(PostgreSQL + TimescaleDB)]
        PG_REPLICA[(Read Replica)]
    end
    
    subgraph "Storage Layer"
        MINIO[(MinIO/S3)]
    end
    
    subgraph "Monitoring"
        PROM[Prometheus]
        GRAF[Grafana]
        ELK[ELK Stack]
    end
    
    LB --> FE1
    LB --> FE2
    LB --> API1
    LB --> API2
    LB --> WS
    
    API1 --> REDIS
    API2 --> REDIS
    API1 --> PG
    API2 --> PG_REPLICA
    
    API1 --> RMQ
    API2 --> RMQ
    RMQ --> CELERY
    
    API1 --> MINIO
    API2 --> MINIO
    
    PROM --> GRAF
    API1 --> ELK
    API2 --> ELK
```

## Production Environment Setup

### System Requirements

#### Minimum Requirements (Single Server)
- **CPU**: 4 cores (2.4 GHz)
- **RAM**: 8 GB
- **Storage**: 100 GB SSD
- **Network**: 1 Gbps
- **OS**: Ubuntu 20.04+ or CentOS 8+

#### Recommended Requirements (Production)
- **CPU**: 8+ cores (3.0 GHz)
- **RAM**: 32 GB
- **Storage**: 500 GB NVMe SSD + separate data storage
- **Network**: 10 Gbps
- **OS**: Ubuntu 22.04 LTS

#### High Availability Setup
- **Load Balancer**: 2x instances (active/passive)
- **Application Servers**: 3+ instances
- **Database**: Primary + 2 replicas
- **Cache**: Redis cluster (3+ nodes)
- **Message Queue**: RabbitMQ cluster (3+ nodes)

### Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install additional tools
sudo apt install -y htop iotop netstat-nat nginx certbot python3-certbot-nginx

# Create application directory
sudo mkdir -p /opt/invoiceflow-pro
sudo chown $USER:$USER /opt/invoiceflow-pro
cd /opt/invoiceflow-pro
```

## Docker Deployment

### Production Docker Compose

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    container_name: invoiceflow-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./logs/nginx:/var/log/nginx
    depends_on:
      - backend
      - frontend
    networks:
      - invoiceflow-network
    restart: unless-stopped

  # Frontend Application
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    container_name: invoiceflow-frontend
    environment:
      - NODE_ENV=production
      - NEXT_PUBLIC_API_URL=${FRONTEND_API_URL}
      - NEXT_PUBLIC_WS_URL=${FRONTEND_WS_URL}
      - NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=${STRIPE_PUBLISHABLE_KEY}
    volumes:
      - ./logs/frontend:/app/logs
    networks:
      - invoiceflow-network
    restart: unless-stopped
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

  # Backend API
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    container_name: invoiceflow-backend
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SECRET_KEY=${SECRET_KEY}
      - STRIPE_SECRET_KEY=${STRIPE_SECRET_KEY}
      - SMTP_HOST=${SMTP_HOST}
      - SMTP_USER=${SMTP_USER}
      - SMTP_PASSWORD=${SMTP_PASSWORD}
      - MINIO_ENDPOINT=${MINIO_ENDPOINT}
      - MINIO_ACCESS_KEY=${MINIO_ACCESS_KEY}
      - MINIO_SECRET_KEY=${MINIO_SECRET_KEY}
    volumes:
      - ./logs/backend:/app/logs
      - ./uploads:/app/uploads
    depends_on:
      - postgres
      - redis
      - rabbitmq
    networks:
      - invoiceflow-network
    restart: unless-stopped
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G

  # Celery Workers
  celery-worker:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    container_name: invoiceflow-celery
    command: celery -A app.core.celery worker --loglevel=info
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - RABBITMQ_URL=${RABBITMQ_URL}
      - SMTP_HOST=${SMTP_HOST}
      - SMTP_USER=${SMTP_USER}
      - SMTP_PASSWORD=${SMTP_PASSWORD}
    volumes:
      - ./logs/celery:/app/logs
    depends_on:
      - postgres
      - redis
      - rabbitmq
    networks:
      - invoiceflow-network
    restart: unless-stopped
    deploy:
      replicas: 2

  # Celery Beat Scheduler
  celery-beat:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    container_name: invoiceflow-celery-beat
    command: celery -A app.core.celery beat --loglevel=info
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - RABBITMQ_URL=${RABBITMQ_URL}
    volumes:
      - ./logs/celery:/app/logs
    depends_on:
      - postgres
      - redis
      - rabbitmq
    networks:
      - invoiceflow-network
    restart: unless-stopped

  # PostgreSQL with TimescaleDB
  postgres:
    image: timescale/timescaledb:latest-pg15
    container_name: invoiceflow-postgres
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
      - ./postgres/init:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"
    networks:
      - invoiceflow-network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
        reservations:
          cpus: '2.0'
          memory: 4G

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: invoiceflow-redis
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
      - ./redis/redis.conf:/usr/local/etc/redis/redis.conf
    ports:
      - "6379:6379"
    networks:
      - invoiceflow-network
    restart: unless-stopped

  # RabbitMQ Message Queue
  rabbitmq:
    image: rabbitmq:3-management-alpine
    container_name: invoiceflow-rabbitmq
    environment:
      - RABBITMQ_DEFAULT_USER=${RABBITMQ_USER}
      - RABBITMQ_DEFAULT_PASS=${RABBITMQ_PASSWORD}
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    ports:
      - "5672:5672"
      - "15672:15672"
    networks:
      - invoiceflow-network
    restart: unless-stopped

  # MinIO Object Storage
  minio:
    image: minio/minio
    container_name: invoiceflow-minio
    command: server /data --console-address ":9001"
    environment:
      - MINIO_ROOT_USER=${MINIO_ACCESS_KEY}
      - MINIO_ROOT_PASSWORD=${MINIO_SECRET_KEY}
    volumes:
      - minio_data:/data
    ports:
      - "9000:9000"
      - "9001:9001"
    networks:
      - invoiceflow-network
    restart: unless-stopped

  # Prometheus Monitoring
  prometheus:
    image: prom/prometheus
    container_name: invoiceflow-prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    networks:
      - invoiceflow-network
    restart: unless-stopped

  # Grafana Dashboard
  grafana:
    image: grafana/grafana
    container_name: invoiceflow-grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/var/lib/grafana/dashboards
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
    ports:
      - "3001:3000"
    networks:
      - invoiceflow-network
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  rabbitmq_data:
  minio_data:
  prometheus_data:
  grafana_data:

networks:
  invoiceflow-network:
    driver: bridge
```

### Production Environment File

```bash
# .env.prod
# Application
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-super-secure-secret-key-here
FRONTEND_URL=https://yourdomain.com
API_V1_STR=/api/v1

# Database
DATABASE_URL=postgresql://invoiceflow:secure_password@postgres:5432/invoiceflow_prod
POSTGRES_DB=invoiceflow_prod
POSTGRES_USER=invoiceflow
POSTGRES_PASSWORD=secure_database_password

# Redis
REDIS_URL=redis://:redis_password@redis:6379/0
REDIS_PASSWORD=secure_redis_password

# RabbitMQ
RABBITMQ_URL=amqp://invoiceflow:rabbit_password@rabbitmq:5672//
RABBITMQ_USER=invoiceflow
RABBITMQ_PASSWORD=secure_rabbit_password

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Stripe
STRIPE_PUBLISHABLE_KEY=pk_live_your_publishable_key
STRIPE_SECRET_KEY=sk_live_your_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# MinIO/S3
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=your_minio_access_key
MINIO_SECRET_KEY=your_minio_secret_key

# Frontend
FRONTEND_API_URL=https://yourdomain.com/api/v1
FRONTEND_WS_URL=wss://yourdomain.com/api/v1/ws

# Monitoring
GRAFANA_PASSWORD=secure_grafana_password

# JWT
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

### Nginx Configuration

```nginx
# nginx/nginx.conf
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';
    access_log /var/log/nginx/access.log main;

    # Performance
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 50M;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied expired no-cache no-store private must-revalidate auth;
    gzip_types text/plain text/css text/xml text/javascript
               application/x-javascript application/xml+rss
               application/javascript application/json;

    # SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;

    # Upstream servers
    upstream frontend {
        least_conn;
        server frontend:3000;
    }

    upstream backend {
        least_conn;
        server backend:8000;
    }

    # HTTP to HTTPS redirect
    server {
        listen 80;
        server_name yourdomain.com www.yourdomain.com;
        return 301 https://$server_name$request_uri;
    }

    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name yourdomain.com www.yourdomain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin";

        # Frontend
        location / {
            proxy_pass http://frontend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_cache_bypass $http_upgrade;
            proxy_read_timeout 86400;
        }

        # API endpoints
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_read_timeout 300;
            proxy_connect_timeout 300;
        }

        # WebSocket connections
        location /api/v1/ws/ {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_read_timeout 86400;
        }

        # Static files
        location /static/ {
            alias /var/www/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # Favicon
        location /favicon.ico {
            access_log off;
            log_not_found off;
            expires 1y;
        }

        # Health check
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
```

### Deployment Script

```bash
#!/bin/bash
# deploy.sh

set -e

echo "Starting InvoiceFlow Pro deployment..."

# Configuration
APP_DIR="/opt/invoiceflow-pro"
BACKUP_DIR="/opt/backups/invoiceflow-$(date +%Y%m%d_%H%M%S)"
DOCKER_COMPOSE_FILE="docker-compose.prod.yml"

# Create backup
echo "Creating backup..."
mkdir -p $BACKUP_DIR
docker-compose -f $DOCKER_COMPOSE_FILE exec postgres pg_dump -U $POSTGRES_USER $POSTGRES_DB > $BACKUP_DIR/database.sql
docker-compose -f $DOCKER_COMPOSE_FILE exec redis redis-cli --rdb $BACKUP_DIR/redis.rdb
cp -r $APP_DIR/logs $BACKUP_DIR/

# Pull latest changes
echo "Pulling latest changes..."
git pull origin main

# Build new images
echo "Building new images..."
docker-compose -f $DOCKER_COMPOSE_FILE build

# Run database migrations
echo "Running database migrations..."
docker-compose -f $DOCKER_COMPOSE_FILE exec backend alembic upgrade head

# Restart services with zero-downtime
echo "Restarting services..."
docker-compose -f $DOCKER_COMPOSE_FILE up -d --no-deps --scale backend=2
sleep 30
docker-compose -f $DOCKER_COMPOSE_FILE up -d --no-deps --scale backend=3

# Health check
echo "Performing health check..."
for i in {1..30}; do
    if curl -f http://localhost/health; then
        echo "Health check passed"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "Health check failed"
        exit 1
    fi
    sleep 2
done

# Cleanup old images
echo "Cleaning up old images..."
docker image prune -f

echo "Deployment completed successfully!"
```

## Kubernetes Deployment

### Namespace and ConfigMap

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: invoiceflow-pro
  labels:
    name: invoiceflow-pro

---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: invoiceflow-config
  namespace: invoiceflow-pro
data:
  ENVIRONMENT: "production"
  API_V1_STR: "/api/v1"
  FRONTEND_URL: "https://yourdomain.com"
  POSTGRES_DB: "invoiceflow_prod"
  POSTGRES_USER: "invoiceflow"
  REDIS_URL: "redis://redis-service:6379/0"
  RABBITMQ_URL: "amqp://rabbitmq-service:5672//"
  MINIO_ENDPOINT: "minio-service:9000"
```

### Secrets

```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: invoiceflow-secrets
  namespace: invoiceflow-pro
type: Opaque
data:
  SECRET_KEY: # base64 encoded secret key
  DATABASE_URL: # base64 encoded database URL
  POSTGRES_PASSWORD: # base64 encoded postgres password
  REDIS_PASSWORD: # base64 encoded redis password
  STRIPE_SECRET_KEY: # base64 encoded stripe secret
  SMTP_PASSWORD: # base64 encoded email password
  MINIO_ACCESS_KEY: # base64 encoded minio access key
  MINIO_SECRET_KEY: # base64 encoded minio secret key
```

### PostgreSQL Deployment

```yaml
# k8s/postgres.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: invoiceflow-pro
spec:
  serviceName: postgres-service
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: timescale/timescaledb:latest-pg15
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_DB
          valueFrom:
            configMapKeyRef:
              name: invoiceflow-config
              key: POSTGRES_DB
        - name: POSTGRES_USER
          valueFrom:
            configMapKeyRef:
              name: invoiceflow-config
              key: POSTGRES_USER
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: invoiceflow-secrets
              key: POSTGRES_PASSWORD
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "8Gi"
            cpu: "4000m"
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 100Gi

---
apiVersion: v1
kind: Service
metadata:
  name: postgres-service
  namespace: invoiceflow-pro
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
  clusterIP: None
```

### Backend Deployment

```yaml
# k8s/backend.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: invoiceflow-pro
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: invoiceflow/backend:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: invoiceflow-config
        - secretRef:
            name: invoiceflow-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: backend-service
  namespace: invoiceflow-pro
spec:
  selector:
    app: backend
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
```

### Frontend Deployment

```yaml
# k8s/frontend.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: invoiceflow-pro
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: frontend
        image: invoiceflow/frontend:latest
        ports:
        - containerPort: 3000
        env:
        - name: NEXT_PUBLIC_API_URL
          value: "https://yourdomain.com/api/v1"
        - name: NEXT_PUBLIC_WS_URL
          value: "wss://yourdomain.com/api/v1/ws"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "1000m"

---
apiVersion: v1
kind: Service
metadata:
  name: frontend-service
  namespace: invoiceflow-pro
spec:
  selector:
    app: frontend
  ports:
  - port: 3000
    targetPort: 3000
  type: ClusterIP
```

### Ingress Configuration

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: invoiceflow-ingress
  namespace: invoiceflow-pro
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "50m"
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  tls:
  - hosts:
    - yourdomain.com
    secretName: invoiceflow-tls
  rules:
  - host: yourdomain.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: backend-service
            port:
              number: 8000
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 3000
```

### Horizontal Pod Autoscaler

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
  namespace: invoiceflow-pro
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: frontend-hpa
  namespace: invoiceflow-pro
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: frontend
  minReplicas: 2
  maxReplicas: 6
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## Cloud Deployment

### AWS Deployment with EKS

```yaml
# aws/cluster.yaml
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig

metadata:
  name: invoiceflow-cluster
  region: us-west-2
  version: "1.28"

nodeGroups:
  - name: worker-nodes
    instanceType: t3.large
    desiredCapacity: 3
    minSize: 1
    maxSize: 6
    volumeSize: 100
    ssh:
      allow: true
    iam:
      withAddonPolicies:
        autoScaler: true
        albIngress: true
        ebs: true
        efs: true
        cloudWatch: true

addons:
  - name: vpc-cni
    version: latest
  - name: coredns
    version: latest
  - name: kube-proxy
    version: latest
  - name: aws-ebs-csi-driver
    version: latest
```

### AWS RDS Configuration

```yaml
# aws/rds.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'PostgreSQL RDS for InvoiceFlow Pro'

Parameters:
  DatabasePassword:
    Type: String
    NoEcho: true
    Description: Database password
    MinLength: 12

Resources:
  DatabaseSubnetGroup:
    Type: AWS::RDS::DBSubnetGroup
    Properties:
      DBSubnetGroupDescription: Subnet group for PostgreSQL database
      SubnetIds:
        - !Ref DatabaseSubnet1
        - !Ref DatabaseSubnet2
      Tags:
        - Key: Name
          Value: invoiceflow-db-subnet-group

  DatabaseSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Security group for PostgreSQL database
      VpcId: !Ref VPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 5432
          ToPort: 5432
          SourceSecurityGroupId: !Ref ApplicationSecurityGroup

  PostgreSQLDatabase:
    Type: AWS::RDS::DBInstance
    Properties:
      DBInstanceIdentifier: invoiceflow-postgres
      DBName: invoiceflow_prod
      DBInstanceClass: db.t3.large
      Engine: postgres
      EngineVersion: '15.4'
      MasterUsername: invoiceflow
      MasterUserPassword: !Ref DatabasePassword
      AllocatedStorage: 100
      StorageType: gp3
      StorageEncrypted: true
      VPCSecurityGroups:
        - !Ref DatabaseSecurityGroup
      DBSubnetGroupName: !Ref DatabaseSubnetGroup
      BackupRetentionPeriod: 7
      MultiAZ: true
      DeletionProtection: true
      Tags:
        - Key: Name
          Value: invoiceflow-database
```

### Google Cloud Platform Deployment

```yaml
# gcp/gke-cluster.yaml
apiVersion: container.v1
kind: Cluster
metadata:
  name: invoiceflow-cluster
spec:
  zone: us-central1-a
  initialNodeCount: 3
  nodeConfig:
    machineType: n1-standard-4
    diskSizeGb: 100
    oauthScopes:
      - https://www.googleapis.com/auth/compute
      - https://www.googleapis.com/auth/devstorage.read_only
      - https://www.googleapis.com/auth/logging.write
      - https://www.googleapis.com/auth/monitoring
  masterAuth:
    username: admin
  network: default
  subnetwork: default
  addonsConfig:
    httpLoadBalancing:
      disabled: false
    horizontalPodAutoscaling:
      disabled: false
  legacyAbac:
    enabled: false
```

### Azure Deployment with AKS

```yaml
# azure/aks-cluster.yaml
apiVersion: v1
kind: Template
metadata:
  name: invoiceflow-aks
parameters:
  - name: clusterName
    value: invoiceflow-cluster
  - name: location
    value: East US
  - name: nodeCount
    value: 3
  - name: vmSize
    value: Standard_D4s_v3

resources:
  - type: Microsoft.ContainerService/managedClusters
    apiVersion: 2021-05-01
    name: ${clusterName}
    location: ${location}
    properties:
      kubernetesVersion: 1.28.0
      dnsPrefix: ${clusterName}
      agentPoolProfiles:
        - name: nodepool1
          count: ${nodeCount}
          vmSize: ${vmSize}
          osType: Linux
          mode: System
      servicePrincipalProfile:
        clientId: ${servicePrincipalClientId}
        secret: ${servicePrincipalClientSecret}
      networkProfile:
        networkPlugin: kubenet
        loadBalancerSku: standard
      enableRBAC: true
```

## Environment Configuration

### Environment Variables Reference

```bash
# Core Application Settings
ENVIRONMENT=production|staging|development
DEBUG=false
SECRET_KEY=your-secret-key-minimum-32-characters
API_V1_STR=/api/v1
FRONTEND_URL=https://yourdomain.com

# Database Configuration
DATABASE_URL=postgresql://user:password@host:5432/database
POSTGRES_DB=invoiceflow_prod
POSTGRES_USER=invoiceflow
POSTGRES_PASSWORD=secure_database_password

# Cache Configuration
REDIS_URL=redis://username:password@host:6379/0
REDIS_PASSWORD=secure_redis_password

# Message Queue Configuration
RABBITMQ_URL=amqp://username:password@host:5672//
RABBITMQ_USER=invoiceflow
RABBITMQ_PASSWORD=secure_rabbit_password

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@domain.com
SMTP_PASSWORD=your-email-app-password
SMTP_TLS=true
SMTP_SSL=false

# Payment Processing
STRIPE_PUBLISHABLE_KEY=pk_live_your_publishable_key
STRIPE_SECRET_KEY=sk_live_your_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# File Storage
MINIO_ENDPOINT=minio.yourdomain.com:9000
MINIO_ACCESS_KEY=your_access_key
MINIO_SECRET_KEY=your_secret_key
MINIO_SECURE=true
MINIO_BUCKET_NAME=invoiceflow-files

# JWT Configuration
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
ALGORITHM=HS256

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=1000
RATE_LIMIT_WINDOW=3600

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
SENTRY_DSN=your_sentry_dsn_for_error_tracking

# Monitoring
PROMETHEUS_ENABLED=true
METRICS_PORT=9090

# Feature Flags
ANALYTICS_ENABLED=true
REAL_TIME_NOTIFICATIONS=true
EMAIL_VERIFICATION_REQUIRED=true
```

### Configuration Validation

```python
# config_validator.py
import os
import sys
from typing import List, Optional

class ConfigValidator:
    """Validate production configuration"""
    
    REQUIRED_VARS = [
        'SECRET_KEY',
        'DATABASE_URL',
        'REDIS_URL',
        'STRIPE_SECRET_KEY',
        'SMTP_HOST',
        'SMTP_USER',
        'SMTP_PASSWORD'
    ]
    
    SENSITIVE_VARS = [
        'SECRET_KEY',
        'DATABASE_URL',
        'REDIS_PASSWORD',
        'STRIPE_SECRET_KEY',
        'SMTP_PASSWORD'
    ]
    
    def validate(self) -> tuple[bool, List[str]]:
        """Validate configuration and return errors"""
        errors = []
        
        # Check required variables
        for var in self.REQUIRED_VARS:
            if not os.getenv(var):
                errors.append(f"Missing required environment variable: {var}")
        
        # Validate SECRET_KEY strength
        secret_key = os.getenv('SECRET_KEY', '')
        if len(secret_key) < 32:
            errors.append("SECRET_KEY must be at least 32 characters long")
        
        # Validate database URL
        db_url = os.getenv('DATABASE_URL', '')
        if not db_url.startswith(('postgresql://', 'postgres://')):
            errors.append("DATABASE_URL must be a valid PostgreSQL connection string")
        
        # Validate Redis URL
        redis_url = os.getenv('REDIS_URL', '')
        if not redis_url.startswith('redis://'):
            errors.append("REDIS_URL must be a valid Redis connection string")
        
        # Validate Stripe keys
        stripe_key = os.getenv('STRIPE_SECRET_KEY', '')
        if not stripe_key.startswith('sk_'):
            errors.append("STRIPE_SECRET_KEY must be a valid Stripe secret key")
        
        # Check for development values in production
        if os.getenv('ENVIRONMENT') == 'production':
            dev_indicators = ['localhost', '127.0.0.1', 'test', 'dev']
            for var in self.SENSITIVE_VARS:
                value = os.getenv(var, '').lower()
                if any(indicator in value for indicator in dev_indicators):
                    errors.append(f"{var} appears to contain development values")
        
        return len(errors) == 0, errors

if __name__ == "__main__":
    validator = ConfigValidator()
    is_valid, errors = validator.validate()
    
    if not is_valid:
        print("❌ Configuration validation failed:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("✅ Configuration validation passed")
```

## SSL/HTTPS Setup

### Let's Encrypt with Certbot

```bash
# install_ssl.sh
#!/bin/bash

# Install Certbot
sudo apt update
sudo apt install -y certbot python3-certbot-nginx

# Stop Nginx temporarily
sudo systemctl stop nginx

# Obtain SSL certificate
sudo certbot certonly --standalone \
    -d yourdomain.com \
    -d www.yourdomain.com \
    --email your-email@domain.com \
    --agree-tos \
    --non-interactive

# Start Nginx
sudo systemctl start nginx

# Set up automatic renewal
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -

# Test renewal
sudo certbot renew --dry-run
```

### SSL Certificate Management

```bash
# ssl_management.sh
#!/bin/bash

# Function to check certificate expiry
check_certificate_expiry() {
    local domain=$1
    local days_until_expiry=$(openssl s_client -servername $domain -connect $domain:443 </dev/null 2>/dev/null | \
        openssl x509 -noout -dates | grep notAfter | cut -d= -f2 | \
        xargs -I {} date -d {} +%s)
    
    local current_date=$(date +%s)
    local days_left=$(( (days_until_expiry - current_date) / 86400 ))
    
    echo "Certificate for $domain expires in $days_left days"
    
    if [ $days_left -lt 30 ]; then
        echo "WARNING: Certificate expires soon!"
        return 1
    fi
    
    return 0
}

# Check all domains
domains=("yourdomain.com" "www.yourdomain.com")
for domain in "${domains[@]}"; do
    check_certificate_expiry $domain
done
```

## Database Migration

### Production Migration Strategy

```python
# migration_manager.py
import asyncio
import subprocess
import sys
from datetime import datetime
from pathlib import Path

class MigrationManager:
    """Manage database migrations in production"""
    
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.backup_dir = Path("/opt/backups")
        self.backup_dir.mkdir(exist_ok=True)
    
    def create_backup(self) -> str:
        """Create database backup before migration"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"pre_migration_{timestamp}.sql"
        
        cmd = [
            "pg_dump",
            self.db_url,
            "-f", str(backup_file),
            "--verbose",
            "--clean",
            "--if-exists"
        ]
        
        try:
            subprocess.run(cmd, check=True)
            print(f"✅ Backup created: {backup_file}")
            return str(backup_file)
        except subprocess.CalledProcessError as e:
            print(f"❌ Backup failed: {e}")
            sys.exit(1)
    
    def run_migrations(self) -> bool:
        """Run Alembic migrations"""
        try:
            # Check current revision
            result = subprocess.run(
                ["alembic", "current"],
                capture_output=True,
                text=True,
                check=True
            )
            print(f"Current revision: {result.stdout.strip()}")
            
            # Run migrations
            subprocess.run(["alembic", "upgrade", "head"], check=True)
            print("✅ Migrations completed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Migration failed: {e}")
            return False
    
    def verify_migration(self) -> bool:
        """Verify migration was successful"""
        try:
            # Check if we can connect to database
            import psycopg2
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            
            # Run basic queries to verify schema
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
            tables = cursor.fetchall()
            
            expected_tables = {'users', 'customers', 'invoices', 'invoice_items', 'payments'}
            actual_tables = {table[0] for table in tables}
            
            if expected_tables.issubset(actual_tables):
                print("✅ Migration verification passed")
                return True
            else:
                missing = expected_tables - actual_tables
                print(f"❌ Missing tables: {missing}")
                return False
                
        except Exception as e:
            print(f"❌ Migration verification failed: {e}")
            return False
    
    def rollback_migration(self, backup_file: str):
        """Rollback migration using backup"""
        try:
            cmd = [
                "psql",
                self.db_url,
                "-f", backup_file,
                "--single-transaction"
            ]
            
            subprocess.run(cmd, check=True)
            print(f"✅ Rollback completed using {backup_file}")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Rollback failed: {e}")
            sys.exit(1)

# Migration script
async def main():
    import os
    
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not set")
        sys.exit(1)
    
    manager = MigrationManager(db_url)
    
    # Create backup
    backup_file = manager.create_backup()
    
    # Run migrations
    if manager.run_migrations():
        # Verify migration
        if manager.verify_migration():
            print("🎉 Migration completed successfully!")
        else:
            print("⚠️  Migration completed but verification failed")
            response = input("Do you want to rollback? (y/N): ")
            if response.lower() == 'y':
                manager.rollback_migration(backup_file)
    else:
        print("❌ Migration failed, rolling back...")
        manager.rollback_migration(backup_file)

if __name__ == "__main__":
    asyncio.run(main())
```

### Zero-Downtime Migration

```python
# zero_downtime_migration.py
"""
Zero-downtime migration strategy for InvoiceFlow Pro
"""
import asyncio
import time
from typing import List, Dict, Any

class ZeroDowntimeMigration:
    """Implement zero-downtime database migrations"""
    
    def __init__(self, primary_db: str, replica_db: str):
        self.primary_db = primary_db
        self.replica_db = replica_db
    
    async def expand_phase(self, migrations: List[str]):
        """Phase 1: Expand - Add new columns/tables without breaking existing code"""
        print("🔄 Starting expand phase...")
        
        for migration in migrations:
            if self.is_additive_migration(migration):
                await self.run_migration(migration)
                await self.verify_replication()
            else:
                raise ValueError(f"Non-additive migration in expand phase: {migration}")
        
        print("✅ Expand phase completed")
    
    async def migrate_phase(self):
        """Phase 2: Migrate - Update application code to use new schema"""
        print("🔄 Starting migrate phase...")
        
        # Deploy new application version
        await self.deploy_application_version()
        
        # Wait for old connections to drain
        await self.wait_for_connection_drain()
        
        print("✅ Migrate phase completed")
    
    async def contract_phase(self, cleanup_migrations: List[str]):
        """Phase 3: Contract - Remove old columns/tables"""
        print("🔄 Starting contract phase...")
        
        # Wait additional time to ensure no rollback needed
        await asyncio.sleep(300)  # 5 minutes
        
        for migration in cleanup_migrations:
            await self.run_migration(migration)
            await self.verify_replication()
        
        print("✅ Contract phase completed")
    
    def is_additive_migration(self, migration: str) -> bool:
        """Check if migration only adds new schema elements"""
        destructive_keywords = ['DROP', 'ALTER', 'DELETE', 'TRUNCATE']
        return not any(keyword in migration.upper() for keyword in destructive_keywords)
    
    async def run_migration(self, migration: str):
        """Run migration on primary database"""
        # Implementation depends on your migration tool
        pass
    
    async def verify_replication(self):
        """Verify that changes have replicated to all replicas"""
        # Check replication lag
        pass
    
    async def deploy_application_version(self):
        """Deploy new application version with rolling update"""
        # Kubernetes rolling update or similar
        pass
    
    async def wait_for_connection_drain(self):
        """Wait for old application connections to drain"""
        # Monitor connection pools
        pass

# Example usage
async def run_zero_downtime_migration():
    migration = ZeroDowntimeMigration(
        primary_db=os.getenv("DATABASE_URL"),
        replica_db=os.getenv("DATABASE_REPLICA_URL")
    )
    
    # Phase 1: Add new columns
    expand_migrations = [
        "ALTER TABLE invoices ADD COLUMN new_field VARCHAR(255);",
        "CREATE INDEX CONCURRENTLY idx_invoices_new_field ON invoices(new_field);"
    ]
    
    # Phase 3: Remove old columns
    contract_migrations = [
        "ALTER TABLE invoices DROP COLUMN old_field;"
    ]
    
    await migration.expand_phase(expand_migrations)
    await migration.migrate_phase()
    await migration.contract_phase(contract_migrations)
```

This comprehensive deployment guide covers all aspects of deploying InvoiceFlow Pro in production environments, from single-server Docker deployments to sophisticated Kubernetes clusters with zero-downtime migration strategies.