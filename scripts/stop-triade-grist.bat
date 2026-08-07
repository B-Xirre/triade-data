@echo off
cd /d "%~dp0..\grist"

docker compose stop

echo TRIADE Grist stopped.
pause