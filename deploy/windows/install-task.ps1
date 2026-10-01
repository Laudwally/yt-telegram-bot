# Registers the bot as a Scheduled Task that starts automatically on boot
# and keeps running in the background — no NSSM or third-party service
# wrapper needed. Run this once, as Administrator, from the project root:
#
#   powershell -ExecutionPolicy Bypass -File deploy\windows\install-task.ps1

$TaskName = "YouTubeTelegramBot"
$ScriptPath = Join-Path $PSScriptRoot "run_bot.ps1"

$Action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$ScriptPath`""

$Trigger = New-ScheduledTaskTrigger -AtStartup

$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -StartWhenAvailable -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit (New-TimeSpan -Days 0) # no time limit — this runs forever

$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger `
    -Settings $Settings -Principal $Principal -Force

Write-Host "Task '$TaskName' registered. It will start on next boot."
Write-Host "To start it right now without rebooting: Start-ScheduledTask -TaskName '$TaskName'"
Write-Host "To check on it: Get-ScheduledTask -TaskName '$TaskName' | Get-ScheduledTaskInfo"
Write-Host "Logs: " (Join-Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)) "bot.log")
