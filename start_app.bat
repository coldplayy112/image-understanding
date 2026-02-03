@echo off
echo Starting Image Insight App...
echo Building and running containers...

docker-compose up -d

if %ERRORLEVEL% NEQ 0 (
    echo Docker failed to start. Please make sure Docker Desktop is running.
    pause
    exit /b
)

echo.
echo App started successfully!
echo Waiting for server to initialize...
timeout /t 5 >nul

echo Opening application in default browser...
start http://localhost:5000

echo.
echo To stop the app, you can run 'docker-compose down' in this folder.
pause
