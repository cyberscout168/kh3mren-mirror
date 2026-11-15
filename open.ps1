
# Run-ScreenMirror.ps1

$ProjectPath = "D:\myaitool\kh3mrenmirroring"

Set-Location $ProjectPath

# Allow script execution for this PowerShell process only
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned -Force

# Activate virtual environment
& "$ProjectPath\.venv\Scripts\Activate.ps1"

# Launch ScreenMirror
python -m screenmirror.main
