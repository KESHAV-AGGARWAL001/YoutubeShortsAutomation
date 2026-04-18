@echo off
echo ============================================
echo   YT Shorts Dashboard — Starting Servers
echo ============================================
echo.
echo   Backend  : http://127.0.0.1:8000
echo   Frontend : http://localhost:5173
echo.
echo   Open http://localhost:5173 in your browser
echo ============================================

start "YT-Backend" cmd /k "cd /d %~dp0 && python -m server.run"
timeout /t 2 /nobreak >nul
start "YT-Frontend" cmd /k "cd /d %~dp0\frontend && npm run dev"
