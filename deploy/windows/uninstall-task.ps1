# Removes the scheduled task installed by install-task.ps1. Run as Administrator.

$TaskName = "YouTubeTelegramBot"
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
Write-Host "Task '$TaskName' removed."
