# Deployment Guide for Personal Calendar Assistant

This guide provides instructions for deploying the Personal Calendar Assistant application to a production environment using Docker and Docker Compose.

## Prerequisites

- Docker and Docker Compose installed on your server
- Domain name (optional but recommended for production)
- SSL certificates (optional for production, self-signed certificates will be generated otherwise)
- Google OAuth2 credentials
- Microsoft OAuth2 credentials
- Gemini API key
- 2GB+ RAM, 1+ CPU cores

## Deployment Steps

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/personal-calendar-assistant.git
cd personal-calendar-assistant
```

### 2. Configure Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# Copy the example file
cp .env.example .env

# Edit the .env file with your credentials
nano .env
```

Fill in your actual credentials and configuration values in the `.env` file.

### 3. Run the Deployment Script

The project includes a deployment script that will:
- Create necessary directories
- Generate self-signed SSL certificates (if not provided)
- Create basic HTML files
- Build and start Docker services

```bash
# Make the script executable
chmod +x scripts/deploy.sh

# Run the deployment script
./scripts/deploy.sh
```

### 4. SSL Certificates for Production

For a production environment, replace the self-signed certificates with proper SSL certificates:

1. Place your SSL certificate and key files in the `nginx/ssl/` directory:
   - `server.crt` (certificate file)
   - `server.key` (private key file)

2. Restart the NGINX container:
   ```bash
   docker-compose restart nginx
   ```

### 5. Custom Domain Configuration

To use your own domain with the application:

1. Update the NGINX configuration in `nginx/conf/default.conf`:
   ```nginx
   server_name yourdomain.com;
   ```

2. Update the `CORS_ORIGINS` in your `.env` file to include your domain:
   ```
   CORS_ORIGINS=["https://yourdomain.com"]
   ```

3. Restart the containers:
   ```bash
   docker-compose restart
   ```

### 6. Monitoring and Maintenance

#### Health Check

The application includes a health check endpoint at `/healthz` that provides basic system status information.

#### Logs

View application logs:
```bash
docker-compose logs app
```

View MongoDB logs:
```bash
docker-compose logs mongodb
```

View NGINX logs:
```bash
docker-compose logs nginx
```

Follow logs in real-time:
```bash
docker-compose logs -f
```

#### Backups

Create a MongoDB backup:
```bash
docker exec calendar-mongodb mongodump --out /data/db/backup/$(date +%Y-%m-%d)
```

Copy the backup to the host:
```bash
docker cp calendar-mongodb:/data/db/backup ./backup
```

#### Updates

Update to the latest version:
```bash
git pull
docker-compose down
docker-compose build
docker-compose up -d
```

### 7. Scaling and High Availability

For a production environment with higher traffic and availability requirements:

1. Use a proper MongoDB replica set
2. Deploy multiple application instances behind a load balancer
3. Use a container orchestration system like Kubernetes
4. Set up monitoring with Prometheus and Grafana
5. Implement automated backups

## Troubleshooting

### Common Issues

#### Application Not Starting

Check the application logs:
```bash
docker-compose logs app
```

#### Database Connection Issues

Verify MongoDB is running:
```bash
docker-compose ps mongodb
```

Check MongoDB logs:
```bash
docker-compose logs mongodb
```

#### SSL Certificate Issues

Verify your SSL certificates are correctly placed in `nginx/ssl/` directory and have proper permissions.

### Getting Help

If you encounter issues not covered in this guide:

1. Check the project's GitHub issues page
2. Review the application logs for specific error messages
3. Contact the development team 