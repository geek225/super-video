@echo off
title Installation du Raccourci - Super Video AI
cd /d "%~dp0"

echo ==========================================================
echo Creation du raccourci avec icone sur votre Bureau...
echo ==========================================================

powershell -NoProfile -ExecutionPolicy Bypass -Command "$ws = New-Object -ComObject WScript.Shell; $desktop = [System.Environment]::GetFolderPath('Desktop'); $s = $ws.CreateShortcut((Join-Path $desktop 'Super Video AI.lnk')); $s.TargetPath = 'wscript.exe'; $s.Arguments = '\"' + (Get-Location).Path + '\Super Video AI.vbs\"'; $s.WorkingDirectory = (Get-Location).Path; $s.IconLocation = (Get-Location).Path + '\app_icon.ico,0'; $s.Description = 'Super Video AI Studio'; $s.Save()"

if %errorlevel% equ 0 (
    echo.
    echo [SUCCES] Le raccourci "Super Video AI" a ete cree sur votre Bureau !
    echo Vous pouvez desormais double-cliquer directement dessus avec sa belle icone.
) else (
    echo [INFO] Impossible de creer le raccourci automatiquement.
)

echo.
pause
