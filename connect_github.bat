@echo off
echo Connecting to GitHub...
echo.

REM Add Git to PATH for this session
set PATH=%PATH%;C:\Program Files\Git\bin

REM Get GitHub repository URL from user
echo Please enter your GitHub repository URL
echo (It should look like: https://github.com/yourusername/particle-tycoon.git)
echo.
set /p REPO_URL="GitHub repository URL: "

REM Add remote origin
echo.
echo Adding GitHub as remote origin...
git remote add origin %REPO_URL%

REM Set main branch
echo.
echo Setting up main branch...
git branch -M main

REM Push to GitHub
echo.
echo Pushing to GitHub...
git push -u origin main

echo.
echo Successfully connected to GitHub!
echo Your code is now backed up at: %REPO_URL%
echo.
pause
