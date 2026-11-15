$ErrorActionPreference = "Stop"

$ProjectRoot = $PSScriptRoot
$PyInstaller = Join-Path $ProjectRoot ".venv\Scripts\pyinstaller.exe"
$SpecFile = Join-Path $ProjectRoot "ScreenMirror.spec"
$OutputRoot = Join-Path $ProjectRoot "dist-easy-run"
$Executable = Join-Path $OutputRoot "ScreenMirror\ScreenMirror.exe"

if (-not (Test-Path $PyInstaller -PathType Leaf)) {
    throw "PyInstaller was not found at $PyInstaller. Set up the project virtual environment first."
}

if (-not (Test-Path $SpecFile -PathType Leaf)) {
    throw "The PyInstaller spec was not found at $SpecFile."
}

Push-Location $ProjectRoot
try {
    & $PyInstaller --noconfirm --distpath $OutputRoot $SpecFile
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller failed with exit code $LASTEXITCODE."
    }
}
finally {
    Pop-Location
}

if (-not (Test-Path $Executable -PathType Leaf)) {
    throw "The build completed without producing $Executable."
}

$Desktop = [Environment]::GetFolderPath("DesktopDirectory")
$ShortcutPath = Join-Path $Desktop "ScreenMirror.lnk"
$Shell = New-Object -ComObject WScript.Shell
$Shortcut = $Shell.CreateShortcut($ShortcutPath)

if ((Test-Path $ShortcutPath -PathType Leaf) -and $Shortcut.TargetPath) {
    $ExistingTarget = [System.IO.Path]::GetFullPath($Shortcut.TargetPath)
    $NewTarget = [System.IO.Path]::GetFullPath($Executable)
    if (-not [string]::Equals($ExistingTarget, $NewTarget, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "A different ScreenMirror shortcut already exists at $ShortcutPath; it was not overwritten."
    }
}

$Shortcut.TargetPath = $Executable
$Shortcut.WorkingDirectory = Split-Path -Parent $Executable
$Shortcut.IconLocation = "$Executable,0"
$Shortcut.Description = "Launch ScreenMirror"
$Shortcut.Save()

Write-Host "Built: $Executable"
Write-Host "Desktop shortcut: $ShortcutPath"
