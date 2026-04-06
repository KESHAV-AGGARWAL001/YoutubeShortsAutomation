@echo off
echo ============================================
echo   YouTube AI Bot — Installing dependencies
echo ============================================
echo.
echo Installing Python libraries...
pip install google-generativeai requests pillow python-dotenv google-auth google-auth-oauthlib google-api-python-client yt-dlp
echo.
echo All libraries installed successfully!
echo.
echo ============================================
echo   Your setup checklist:
echo   [OK] FFmpeg installed
echo   [OK] credentials.json in this folder
echo   [OK] .env file with GEMINI_API_KEY
echo   [OK] music\background.mp3 added
echo ============================================
echo.
echo Run the bot with:
echo   python main.py
echo.
pause
