#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting deployment of Personal Calendar Assistant...${NC}"

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo "Please create a .env file with the required environment variables:"
    echo "GOOGLE_CLIENT_ID=your_google_client_id"
    echo "GOOGLE_CLIENT_SECRET=your_google_client_secret"
    echo "MICROSOFT_CLIENT_ID=your_microsoft_client_id"
    echo "MICROSOFT_CLIENT_SECRET=your_microsoft_client_secret"
    echo "ENCRYPTION_KEY=your_encryption_key"
    echo "GEMINI_API_KEY=your_gemini_api_key"
    echo "JWT_SECRET=your_jwt_secret"
    exit 1
fi

# Create necessary directories if they don't exist
echo -e "${YELLOW}Creating required directories...${NC}"
mkdir -p nginx/conf
mkdir -p nginx/ssl
mkdir -p nginx/www
mkdir -p data/app
mkdir -p data/mongodb

# Check if SSL certificates exist, otherwise generate self-signed certificates
if [ ! -f nginx/ssl/server.crt ] || [ ! -f nginx/ssl/server.key ]; then
    echo -e "${YELLOW}Generating self-signed SSL certificates...${NC}"
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout nginx/ssl/server.key -out nginx/ssl/server.crt \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
fi

# Create basic static HTML files
echo -e "${YELLOW}Creating basic HTML files...${NC}"

# Create index.html
cat > nginx/www/index.html << EOF
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Personal Calendar Assistant</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 0; display: flex; justify-content: center; align-items: center; min-height: 100vh; background-color: #f5f5f5; }
        .container { max-width: 800px; padding: 20px; background-color: white; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        h1 { color: #3498db; }
        .button { display: inline-block; background-color: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; margin-top: 20px; }
        .button:hover { background-color: #2980b9; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Personal Calendar Assistant</h1>
        <p>Your AI-powered calendar management solution. Connect your Google and Microsoft calendars to get started.</p>
        <a href="/api/docs" class="button">API Documentation</a>
        <a href="/auth/google/login" class="button">Connect Google Calendar</a>
        <a href="/auth/microsoft/login" class="button">Connect Microsoft Calendar</a>
    </div>
</body>
</html>
EOF

# Create 404.html
cat > nginx/www/404.html << EOF
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>404 - Page Not Found</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 0; display: flex; justify-content: center; align-items: center; min-height: 100vh; background-color: #f5f5f5; }
        .container { max-width: 800px; padding: 20px; background-color: white; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; }
        h1 { color: #e74c3c; }
        .button { display: inline-block; background-color: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; margin-top: 20px; }
        .button:hover { background-color: #2980b9; }
    </style>
</head>
<body>
    <div class="container">
        <h1>404 - Page Not Found</h1>
        <p>The page you are looking for might have been removed, had its name changed, or is temporarily unavailable.</p>
        <a href="/" class="button">Go to Homepage</a>
    </div>
</body>
</html>
EOF

# Create 50x.html
cat > nginx/www/50x.html << EOF
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Server Error</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 0; display: flex; justify-content: center; align-items: center; min-height: 100vh; background-color: #f5f5f5; }
        .container { max-width: 800px; padding: 20px; background-color: white; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; }
        h1 { color: #e74c3c; }
        .button { display: inline-block; background-color: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; margin-top: 20px; }
        .button:hover { background-color: #2980b9; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Server Error</h1>
        <p>The server encountered an internal error and was unable to complete your request.</p>
        <a href="/" class="button">Go to Homepage</a>
    </div>
</body>
</html>
EOF

# Build and start the Docker Compose services
echo -e "${YELLOW}Building and starting Docker services...${NC}"
docker-compose down
docker-compose build
docker-compose up -d

# Wait for services to start
echo -e "${YELLOW}Waiting for services to initialize...${NC}"
sleep 15

# Check if services are healthy
echo -e "${YELLOW}Checking service health...${NC}"
APP_HEALTH=$(docker inspect --format='{{.State.Health.Status}}' calendar-assistant-app)
MONGODB_HEALTH=$(docker inspect --format='{{.State.Health.Status}}' calendar-mongodb)
NGINX_HEALTH=$(docker ps --filter "name=calendar-nginx" --format "{{.Status}}" | grep -q "Up" && echo "running" || echo "unhealthy")

if [ "$APP_HEALTH" == "healthy" ] && [ "$MONGODB_HEALTH" == "healthy" ] && [ "$NGINX_HEALTH" == "running" ]; then
    echo -e "${GREEN}All services are healthy and running!${NC}"
    echo -e "${GREEN}Personal Calendar Assistant is now available at:${NC}"
    echo -e "${GREEN}https://localhost${NC}"
    echo -e "${GREEN}API Documentation: https://localhost/api/docs${NC}"
else
    echo -e "${RED}Some services are not healthy:${NC}"
    echo -e "App service: ${APP_HEALTH}"
    echo -e "MongoDB service: ${MONGODB_HEALTH}"
    echo -e "Nginx service: ${NGINX_HEALTH}"
    echo -e "${YELLOW}Check the logs with:${NC} docker-compose logs"
fi

echo -e "${YELLOW}Deployment complete.${NC}" 