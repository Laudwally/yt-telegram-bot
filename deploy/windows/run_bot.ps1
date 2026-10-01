# Supervisor loop: restarts the bot if it ever crashes or exits.
# Logs go to bot.log next to this script's project root.

$ErrorActionPreference = "Continue"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$BotScript = Join-Path $ProjectRoot "bot.py"
$LogFile = Join-Path $ProjectRoot "bot.log"

Set-Location $ProjectRoot

while ($true) {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $LogFile -Value "[$timestamp] Starting bot..."

    & $Python $BotScript *>> $LogFile

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $LogFile -Value "[$timestamp] Bot exited (code $LASTEXITCODE). Restarting in 10s..."
    Start-Sleep -Seconds 10
}
