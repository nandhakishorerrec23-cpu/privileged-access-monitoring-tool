@echo off
title Push Project to GitHub
echo ========================================================
echo   Push Privileged Access Monitoring Tool to GitHub
echo ========================================================
echo.

cd /d "%~dp0"

:: Check if git remote origin already exists
git remote get-url origin >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Remote repository is already linked.
    echo Pushing latest updates to GitHub...
    git add .
    git commit -m "Update project files"
    git push -u origin main
    goto done
)

echo Please enter your GitHub repository link.
echo (Example: https://github.com/kavinraja-kh/my-project.git)
echo.
set /p REPO_URL="Paste GitHub Repository URL here: "

if "%REPO_URL%"=="" (
    echo.
    echo [ERROR] No URL entered. Exiting.
    pause
    exit /b 1
)

echo.
echo Linking repository to: %REPO_URL% ...
git remote add origin %REPO_URL%
git branch -M main

echo Pushing code to GitHub...
git add .
git commit -m "Initial commit: Privileged Access Monitoring Tool"
git push -u origin main

:done
echo.
echo ========================================================
echo   Finished! Your project is now on GitHub.
echo ========================================================
echo.
pause
