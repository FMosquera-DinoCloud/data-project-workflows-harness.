# Registra en el Programador de tareas de Windows las rutinas del harness.
# Si la PC estaba apagada a esa hora, corren al encenderla.
# Con -Fallback corren como respaldo de otra PC (media hora después, salteando lo que ya corrió hoy).
# Uso: powershell -ExecutionPolicy Bypass -File install-tasks.ps1 [-Fallback] [-Remove]
param([switch]$Remove, [switch]$Fallback)

$bash = 'C:\Program Files\Git\bin\bash.exe'
$runner = '$HOME/claude-workspace/harness/bin/harness-run'
$prefix = if ($Fallback) { 'HARNESS_FALLBACK=1 ' } else { '' }
$at = if ($Fallback) { @{ daily = '09:30'; weekly = '09:30'; friday = '16:30' } } else { @{ daily = '09:00'; weekly = '09:00'; friday = '16:00' } }
$routines = @(
    @{ Name = 'daily';  Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At $at.daily },
    @{ Name = 'weekly'; Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At $at.weekly },
    @{ Name = 'friday'; Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Friday -At $at.friday }
)

foreach ($r in $routines) {
    $task = "DinoCloud Harness $($r.Name)"
    if ($Remove) { Unregister-ScheduledTask -TaskName $task -Confirm:$false -ErrorAction SilentlyContinue; "removida: $task"; continue }
    $action = New-ScheduledTaskAction -Execute $bash -Argument "-lc `"$prefix\`"$runner\`" $($r.Name)`""
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 3)
    Register-ScheduledTask -TaskName $task -Action $action -Trigger $r.Trigger -Settings $settings -Description 'Rutina del harness de contexto. Ver harness/bin/harness-run.' -Force | Out-Null
    "registrada: $task ($($at[$r.Name]))"
}
