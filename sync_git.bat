@echo off
echo ==========================================
echo      AgriIntel GitHub Sync Script
echo ==========================================

:: 1. Add all changes
echo [1/3] Adding changes...
git add .
if %ERRORLEVEL% NEQ 0 (
    echo Error adding files!
    pause
    exit /b %ERRORLEVEL%
)

:: 2. Commit changes
set /p msg="Enter commit message (default: 'update'): "
if "%msg%"=="" set msg="update"
echo [2/3] Committing with message: "%msg%"...
git commit -m "%msg%"
if %ERRORLEVEL% NEQ 0 (
    echo Nothing to commit or error committing!
)

:: 3. Push to remote
echo [3/3] Pushing to GitHub...
:: Check if remote 'origin' exists
git remote get-url origin >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] No remote 'origin' found!
    echo Please add your repository URL first:
    echo git remote add origin https://github.com/YOUR_USER/YOUR_REPO.git
    pause
    exit /b 1
)

git push
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Push failed! Check your internet or credentials.
    pause
    exit /b %ERRORLEVEL%
)

echo ==========================================
echo        Sync Complete! 🚀
echo ==========================================
pause
