@echo off
cd /d "%~dp0"

echo Starting database...
docker compose up -d --wait db

echo.
echo Running pipeline once...
docker compose run --rm pipeline python run_once.py

echo.
pause