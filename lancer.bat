@echo off
title Super Video - Local Studio
cd /d "%~dp0"

echo ==========================================================
echo Demarrage de SUPER VIDEO AI - Local Studio...
echo Dossier de travail : %CD%
echo ==========================================================

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERREUR] Python n'est pas installe ou n'est pas present dans le PATH.
    echo Veuillez installer Python 3.10+ depuis https://www.python.org/ (cochez "Add Python to PATH")
    pause
    exit /b 1
)

if not exist ".venv" (
    echo [INFO] Creation de l'environnement virtuel local...
    python -m venv .venv
    echo [INFO] Installation des dependances...
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)

if exist ".git" (
    echo [INFO] Recherche de mises a jour sur GitHub...
    git pull origin main --quiet 2>nul
)

if not exist ".env" (
    copy .env.example .env
)

REM Creation automatique des raccourcis avec la belle icone violette
if not exist "%USERPROFILE%\Desktop\Super Video AI.lnk" (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ws = New-Object -ComObject WScript.Shell; $desktop = [System.Environment]::GetFolderPath('Desktop'); $s = $ws.CreateShortcut((Join-Path $desktop 'Super Video AI.lnk')); $s.TargetPath = 'wscript.exe'; $s.Arguments = '\"' + (Get-Location).Path + '\Super Video AI.vbs\"'; $s.WorkingDirectory = (Get-Location).Path; $s.IconLocation = (Get-Location).Path + '\app_icon.ico,0'; $s.Description = 'Super Video AI Studio'; $s.Save()" >nul 2>nul
)
if not exist "Super Video AI.lnk" (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut((Join-Path (Get-Location).Path 'Super Video AI.lnk')); $s.TargetPath = 'wscript.exe'; $s.Arguments = '\"' + (Get-Location).Path + '\Super Video AI.vbs\"'; $s.WorkingDirectory = (Get-Location).Path; $s.IconLocation = (Get-Location).Path + '\app_icon.ico,0'; $s.Description = 'Super Video AI Studio'; $s.Save()" >nul 2>nul
)

start "" http://127.0.0.1:7860

echo ==========================================================
echo Lancement du serveur local sur http://127.0.0.1:7860...
echo Votre navigateur va s'ouvrir automatiquement.
echo Pour arreter le serveur, fermez cette fenetre ou faites Ctrl+C.
echo ==========================================================

python -m uvicorn app.main:app --host 127.0.0.1 --port 7860
pause
