@echo off
cd /d "%~dp0..\grist"

echo Docker Desktop:
docker desktop status

echo.
echo TRIADE Grist:
docker compose ps

pause