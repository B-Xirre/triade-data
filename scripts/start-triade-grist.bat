@echo off
cd /d "%~dp0..\grist"

echo Starting Docker Desktop...
docker desktop start

echo Waiting for Docker...
:waitdocker
docker info >nul 2>&1
if errorlevel 1 (
    timeout /t 2 /nobreak >nul
    goto waitdocker
)

echo Starting TRIADE Grist...
docker compose up -d

echo.
docker compose ps

echo.
echo TRIADE Grist should be available at:
echo http://localhost:8484

pause