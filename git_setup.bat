@echo off
echo Setting up Git repository for Particle Tycoon...
echo.

REM Add Git to PATH for this session
set PATH=%PATH%;C:\Program Files\Git\bin

REM Initialize repository
echo Initializing Git repository...
git init

REM Configure Git (you'll need to replace these with your info)
echo.
echo Please enter your information for Git commits:
set /p USERNAME="Enter your name: "
set /p EMAIL="Enter your email: "

git config user.name "%USERNAME%"
git config user.email "%EMAIL%"

REM Add all files
echo.
echo Adding files to repository...
git add .

REM Create initial commit
echo.
echo Creating initial commit...
git commit -m "Initial commit - Particle Tycoon modular version"

echo.
echo Git repository initialized successfully!
echo.
echo Next steps:
echo 1. Create a GitHub account at https://github.com if you don't have one
echo 2. Create a new repository on GitHub
echo 3. Run the connect_github.bat script
echo.
pause
