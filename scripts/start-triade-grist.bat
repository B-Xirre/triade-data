@echo off
REM Resolve script and grist directories
set "SCRIPT_DIR=%~dp0"
set "GRIST_DIR=%SCRIPT_DIR%..\grist"

if not exist "%GRIST_DIR%" (
    echo Error: grist directory not found at "%GRIST_DIR%"
    echo Ensure this script is located in the repository's "scripts" folder.
    pause
    exit /b 1
)

cd /d "%GRIST_DIR%"

echo Starting Docker Desktop if necessary...

REM If docker CLI missing, inform user
where docker >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Docker CLI not found in PATH. Please install Docker Desktop and try again.
    pause
    exit /b 1
)

REM If docker daemon already available, skip starting Desktop
docker info >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Docker daemon already running.
)
if %ERRORLEVEL% NEQ 0 (
    REM Try new "docker desktop start" CLI if available
    docker desktop version >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo Using 'docker desktop start' to launch Docker Desktop...
        docker desktop start
    ) else (
        REM Fallback: try common Docker Desktop executable locations
        if exist "%ProgramFiles%\Docker\Docker\Docker Desktop.exe" (
            echo Launching Docker Desktop from Program Files...
            start "" "%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
        ) else if exist "%LocalAppData%\Programs\Docker\Docker\Docker Desktop.exe" (
            echo Launching Docker Desktop from LocalAppData...
            start "" "%LocalAppData%\Programs\Docker\Docker\Docker Desktop.exe"
        ) else (
            echo Could not find Docker Desktop executable. Please start Docker Desktop manually.
        )
    )
)

echo Waiting for Docker daemon to become available...
set "RETRY=0"
set "MAX_RETRIES=60"
:waitdocker
docker info >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    goto docker_ready
)
set /a RETRY+=1
if %RETRY% GEQ %MAX_RETRIES% (
    echo Timed out waiting for Docker to start after %MAX_RETRIES% attempts.
    pause
    exit /b 1
)
timeout /t 2 /nobreak >nul
goto waitdocker

:docker_ready
echo Docker is ready.

echo Starting TRIADE Grist (docker compose)...
REM Prefer modern 'docker compose', fallback to 'docker-compose'
docker compose version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    docker compose up -d
    echo.
    docker compose ps
    goto done
)
docker-compose version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    docker-compose up -d
    echo.
    docker-compose ps
    goto done
)

echo Neither 'docker compose' nor 'docker-compose' is available. Cannot start services.
pause
exit /b 1

:done
echo.
echo TRIADE Grist should be available at:
echo http://localhost:8484

pause