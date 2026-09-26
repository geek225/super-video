@echo off
title Installation du Raccourci - Super Video AI
cd /d "%~dp0"

echo ==========================================================
echo Creation du raccourci avec icone sur votre Bureau...
echo ==========================================================

powershell -NoProfile -ExecutionPolicy Bypass -Command "$ws = New-Object -ComObject WScript.Shell; $desktop = [System.Environment]::GetFolderPath('Desktop'); $s1 = $ws.CreateShortcut((Join-Path $desktop 'Super Video AI.lnk')); $s1.TargetPath = 'wscript.exe'; $s1.Arguments = '\"' + (Get-Location).Path + '\Super Video AI.vbs\"'; $s1.WorkingDirectory = (Get-Location).Path; $s1.IconLocation = (Get-Location).Path + '\app_icon.ico,0'; $s1.Description = 'Super Video AI Studio'; $s1.Save(); $s2 = $ws.CreateShortcut((Join-Path (Get-Location).Path 'Super Video AI.lnk')); $s2.TargetPath = 'wscript.exe'; $s2.Arguments = '\"' + (Get-Location).Path + '\Super Video AI.vbs\"'; $s2.WorkingDirectory = (Get-Location).Path; $s2.IconLocation = (Get-Location).Path + '\app_icon.ico,0'; $s2.Description = 'Super Video AI Studio'; $s2.Save()"

if %errorlevel% equ 0 (
    echo.
    echo [SUCCES] Le raccourci avec icone "Super Video AI" a ete cree :
    echo - Sur votre Bureau
    echo - Dans ce dossier
    echo Vous pouvez desormais double-cliquer directement dessus !
) else (
    echo [INFO] Impossible de creer le raccourci automatiquement.
)

echo.
pause
