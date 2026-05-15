@echo off
echo 🐳 Building Legal AI Docker Images...
echo.

echo Step 1: Cleaning old builds...
docker-compose down
docker system prune -f

echo.
echo Step 2: Building images (this may take 5-10 minutes)...
docker-compose build --no-cache

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Build successful!
    echo.
    echo Step 3: Starting services...
    docker-compose up -d
    
    echo.
    echo ✅ Deployment complete!
    echo.
    echo 📍 Access your application:
    echo    Frontend: http://localhost:3000
    echo    Backend:  http://localhost:8000
    echo    API Docs: http://localhost:8000/docs
    echo.
    echo 📊 View logs:
    echo    docker-compose logs -f
    echo.
) else (
    echo.
    echo ❌ Build failed!
    echo.
    echo Try these solutions:
    echo 1. Check your internet connection
    echo 2. Restart Docker Desktop
    echo 3. Run: docker system prune -a
    echo 4. Try again
    echo.
)

pause
