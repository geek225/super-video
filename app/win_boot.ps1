# ==============================================================================
# Super Video AI — Autonomous Windows Desktop Bootstrapper (Méthode A)
# Installe automatiquement un moteur Python 3.11 portable dans .runtime\python
# si l'utilisateur n'a pas Python sur son PC Windows. Zéro action requise.
# ==============================================================================
$ErrorActionPreference = "Stop"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$AppDir = Split-Path -Parent $PSScriptRoot
Set-Location $AppDir
New-Item -ItemType Directory -Path (Join-Path $AppDir "uploads") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $AppDir "outputs") -Force | Out-Null

# Si l'utilisateur a lancé Super Video AI.exe depuis Téléchargements, en garder une copie dans AppDir
$LauncherExeArg = if ($args.Count -gt 0) { $args[0] } else { $null }
$ExePath = Join-Path $AppDir "Super Video AI.exe"
if ($LauncherExeArg -and (Test-Path $LauncherExeArg) -and ($LauncherExeArg -ne $ExePath)) {
    try { Copy-Item $LauncherExeArg $ExePath -Force } catch {}
}

# 1. Créer le fichier .env s'il n'existe pas
if ((-not (Test-Path ".env")) -and (Test-Path ".env.example")) {
    Copy-Item ".env.example" ".env" -Force
}

# 2. Créer automatiquement le raccourci sur le Bureau Windows (avec l'icône officielle)
try {
    $DesktopDir = [Environment]::GetFolderPath("Desktop")
    $ShortcutPath = Join-Path $DesktopDir "Super Video AI.lnk"
    $IcoPath = Join-Path $AppDir "app_icon.ico"
    if ((-not (Test-Path $ShortcutPath)) -and (Test-Path $ExePath)) {
        $WshShell = New-Object -ComObject WScript.Shell
        $Shortcut = $WshShell.CreateShortcut($ShortcutPath)
        $Shortcut.TargetPath = $ExePath
        $Shortcut.WorkingDirectory = $AppDir
        if (Test-Path $IcoPath) {
            $Shortcut.IconLocation = "$IcoPath,0"
        }
        $Shortcut.Description = "Super Video AI — Studio Motion & Vidéo"
        $Shortcut.Save()
    }
} catch {}

# 3. Vérifier si un moteur Python prêt existe déjà (.runtime\python ou .venv)
$PortablePy = Join-Path $AppDir ".runtime\python\python.exe"
$PortablePyw = Join-Path $AppDir ".runtime\python\pythonw.exe"
$VenvPy = Join-Path $AppDir ".venv\Scripts\python.exe"
$VenvPyw = Join-Path $AppDir ".venv\Scripts\pythonw.exe"

function Test-EngineReady($PyExe) {
    if (-not (Test-Path $PyExe)) { return $false }
    try {
        $p = Start-Process -FilePath $PyExe -ArgumentList "-c `"import webview, uvicorn, fastapi`"" -WindowStyle Hidden -Wait -PassThru
        return ($p.ExitCode -eq 0)
    } catch {
        return $false
    }
}

if (Test-EngineReady $PortablePy) {
    Start-Process -FilePath $PortablePyw -ArgumentList "`"$AppDir\desktop.py`"" -WorkingDirectory $AppDir -WindowStyle Hidden
    exit 0
}

if (Test-EngineReady $VenvPy) {
    Start-Process -FilePath $VenvPyw -ArgumentList "`"$AppDir\desktop.py`"" -WorkingDirectory $AppDir -WindowStyle Hidden
    exit 0
}

# 4. Première ouverture : Affichage de la fenêtre graphique d'initialisation signée
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$Form = New-Object System.Windows.Forms.Form
$Form.Text = "Super Video AI — Studio Desktop"
$Form.Size = New-Object System.Drawing.Size(480, 340)
$Form.StartPosition = "CenterScreen"
$Form.FormBorderStyle = "FixedDialog"
$Form.MaximizeBox = $false
$Form.MinimizeBox = $false
$Form.BackColor = [System.Drawing.Color]::FromArgb(7, 7, 12)

$IcoFile = Join-Path $AppDir "app_icon.ico"
if (Test-Path $IcoFile) {
    try { $Form.Icon = New-Object System.Drawing.Icon($IcoFile) } catch {}
}

# Photo de Stéphane Kevin Assamoi
$PhotoPath = Join-Path $AppDir "public\asset\kevin.png"
if (Test-Path $PhotoPath) {
    try {
        $PicBox = New-Object System.Windows.Forms.PictureBox
        $PicBox.Size = New-Object System.Drawing.Size(96, 96)
        $PicBox.Location = New-Object System.Drawing.Point(185, 18)
        $PicBox.SizeMode = "StretchImage"
        $PicBox.Image = [System.Drawing.Image]::FromFile($PhotoPath)
        $Form.Controls.Add($PicBox)
    } catch {}
}

$LblTitle = New-Object System.Windows.Forms.Label
$LblTitle.Text = "SUPER VIDEO AI • STUDIO DESKTOP"
$LblTitle.ForeColor = [System.Drawing.Color]::FromArgb(168, 85, 247)
$LblTitle.Font = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)
$LblTitle.AutoSize = $false
$LblTitle.Size = New-Object System.Drawing.Size(440, 22)
$LblTitle.Location = New-Object System.Drawing.Point(12, 122)
$LblTitle.TextAlign = "MiddleCenter"
$Form.Controls.Add($LblTitle)

$LblAuthor = New-Object System.Windows.Forms.Label
$LblAuthor.Text = "Vibe coder par Stéphane Kevin Assamoi"
$LblAuthor.ForeColor = [System.Drawing.Color]::White
$LblAuthor.Font = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)
$LblAuthor.AutoSize = $false
$LblAuthor.Size = New-Object System.Drawing.Size(440, 22)
$LblAuthor.Location = New-Object System.Drawing.Point(12, 146)
$LblAuthor.TextAlign = "MiddleCenter"
$Form.Controls.Add($LblAuthor)

$LblRole = New-Object System.Windows.Forms.Label
$LblRole.Text = "Référent Digital & AI Product Builder"
$LblRole.ForeColor = [System.Drawing.Color]::FromArgb(6, 182, 212)
$LblRole.Font = New-Object System.Drawing.Font("Segoe UI", 9, [System.Drawing.FontStyle]::Bold)
$LblRole.AutoSize = $false
$LblRole.Size = New-Object System.Drawing.Size(440, 20)
$LblRole.Location = New-Object System.Drawing.Point(12, 168)
$LblRole.TextAlign = "MiddleCenter"
$Form.Controls.Add($LblRole)

$ProgressBar = New-Object System.Windows.Forms.ProgressBar
$ProgressBar.Style = "Marquee"
$ProgressBar.MarqueeAnimationSpeed = 25
$ProgressBar.Size = New-Object System.Drawing.Size(380, 14)
$ProgressBar.Location = New-Object System.Drawing.Point(42, 210)
$Form.Controls.Add($ProgressBar)

$LblStatus = New-Object System.Windows.Forms.Label
$LblStatus.Text = "Bienvenue ! Préparation automatique du Studio (1ère ouverture)..."
$LblStatus.ForeColor = [System.Drawing.Color]::FromArgb(203, 213, 225)
$LblStatus.Font = New-Object System.Drawing.Font("Segoe UI", 8.5)
$LblStatus.AutoSize = $false
$LblStatus.Size = New-Object System.Drawing.Size(440, 42)
$LblStatus.Location = New-Object System.Drawing.Point(12, 234)
$LblStatus.TextAlign = "TopCenter"
$Form.Controls.Add($LblStatus)

# Exécution de l'installation autonome dans un Runspace en arrière-plan
$SyncHash = [hashtable]::Synchronized(@{
    Status = "Téléchargement du moteur Studio intégré (16 Mo)..."
    Done = $false
    Error = $null
})

$Runspace = [runspacefactory]::CreateRunspace()
$Runspace.Open()
$Runspace.SessionStateProxy.SetVariable("AppDir", $AppDir)
$Runspace.SessionStateProxy.SetVariable("SyncHash", $SyncHash)

$PSInstance = [powershell]::Create().AddScript({
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Set-Location $AppDir

        $RuntimeDir = Join-Path $AppDir ".runtime"
        $PyDir = Join-Path $RuntimeDir "python"
        $PyExe = Join-Path $PyDir "python.exe"

        if (-not (Test-Path $PyExe)) {
            $SyncHash.Status = "Téléchargement automatique du moteur Studio (1/2)..."
            New-Item -ItemType Directory -Path $RuntimeDir -Force | Out-Null
            $NupkgZip = Join-Path $RuntimeDir "python311.zip"
            $ExtractTmp = Join-Path $RuntimeDir "extracted"

            $NugetUrl = "https://api.nuget.org/v3-flatcontainer/python/3.11.9/python.3.11.9.nupkg"
            Invoke-WebRequest -Uri $NugetUrl -OutFile $NupkgZip -UseBasicParsing

            $SyncHash.Status = "Extraction du moteur portable dans le dossier..."
            if (Test-Path $ExtractTmp) { Remove-Item $ExtractTmp -Recurse -Force }
            Expand-Archive -Path $NupkgZip -DestinationPath $ExtractTmp -Force

            $ToolsDir = Join-Path $ExtractTmp "tools"
            if (Test-Path $PyDir) { Remove-Item $PyDir -Recurse -Force }
            Move-Item -Path $ToolsDir -Destination $PyDir -Force
            Remove-Item $ExtractTmp -Recurse -Force -ErrorAction SilentlyContinue
            Remove-Item $NupkgZip -Force -ErrorAction SilentlyContinue
        }

        $SyncHash.Status = "Activation de l'interface Desktop native (2/2)...`n(Cela ne prend qu'une minute lors de la 1ère ouverture)"
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = $PyExe
        $psi.Arguments = "-m pip install --upgrade pip --no-warn-script-location"
        $psi.WorkingDirectory = $AppDir
        $psi.CreateNoWindow = $true
        $psi.UseShellExecute = $false
        $p1 = [System.Diagnostics.Process]::Start($psi)
        $p1.WaitForExit()

        $psi2 = New-Object System.Diagnostics.ProcessStartInfo
        $psi2.FileName = $PyExe
        $psi2.Arguments = "-m pip install -r `"$AppDir\requirements.txt`" --no-warn-script-location"
        $psi2.WorkingDirectory = $AppDir
        $psi2.CreateNoWindow = $true
        $psi2.UseShellExecute = $false
        $p2 = [System.Diagnostics.Process]::Start($psi2)
        $p2.WaitForExit()

        $SyncHash.Status = "Prêt ! Ouverture de Super Video AI..."
    } catch {
        $SyncHash.Error = $_.Exception.Message
    } finally {
        $SyncHash.Done = $true
    }
})
$PSInstance.Runspace = $Runspace
$AsyncHandle = $PSInstance.BeginInvoke()

$Timer = New-Object System.Windows.Forms.Timer
$Timer.Interval = 250
$Timer.Add_Tick({
    $LblStatus.Text = $SyncHash.Status
    if ($SyncHash.Done) {
        $Timer.Stop()
        $Form.Close()
    }
})
$Form.Add_Shown({ $Timer.Start() })
[void]$Form.ShowDialog()

$PSInstance.Dispose()
$Runspace.Close()

if ($SyncHash.Error) {
    [System.Windows.Forms.MessageBox]::Show(
        "Une erreur est survenue lors de la préparation initiale :`n" + $SyncHash.Error + "`n`nVérifiez votre connexion Internet et réessayez.",
        "Super Video AI",
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Warning
    )
    exit 1
}

if (Test-Path $PortablePyw) {
    Start-Process -FilePath $PortablePyw -ArgumentList "`"$AppDir\desktop.py`"" -WorkingDirectory $AppDir -WindowStyle Hidden
} elseif (Test-Path $PortablePy) {
    Start-Process -FilePath $PortablePy -ArgumentList "`"$AppDir\desktop.py`"" -WorkingDirectory $AppDir -WindowStyle Hidden
}
