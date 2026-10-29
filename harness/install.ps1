# Instala el harness en Windows. Es idempotente.
# Uso: powershell -ExecutionPolicy Bypass -File harness\install.ps1 [-Status] [-SA] [-NoHook] [-NoPython] [-Diagrams] [-Tasks]
#   (sin flags)  junctions de las skills en ~/.claude/skills, venv con harness/requirements.txt,
#                hooks de sesión y guardas en ~/.claude/settings.json (con backup) y config.toml desde el ejemplo
#   -SA          además las skills del perfil SA/TL (harness\skills-sa)
#   -Diagrams    además prepara aws-diagram (graphviz con winget + venv propio)
#   -Tasks       además registra las rutinas en el Programador de tareas
#   -Status      solo muestra qué está instalado
param([switch]$Status, [switch]$SA, [switch]$NoHook, [switch]$NoPython, [switch]$Diagrams, [switch]$Tasks)

$ErrorActionPreference = 'Stop'
$WS = Split-Path -Parent $PSScriptRoot
$SkillsDst = Join-Path $HOME '.claude\skills'
$Settings = Join-Path $HOME '.claude\settings.json'
$VenvPy = Join-Path $WS 'harness\.venv\Scripts\python.exe'
$Bash = 'C:\Program Files\Git\bin\bash.exe'
$HookCmd = 'bash "' + ($WS -replace '\\', '/') + '/harness/hooks/session-start.sh"'

function Ok($m) { Write-Host "  ok   $m" -ForegroundColor Green }
function Warn($m) { Write-Host "  !!   $m" -ForegroundColor Yellow }
function IsJunction($p) { (Test-Path $p) -and ((Get-Item $p -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) }

function Install-Skills {
    Write-Host "Skills -> $SkillsDst"
    New-Item -ItemType Directory -Force $SkillsDst | Out-Null
    $dirs = @(Get-ChildItem (Join-Path $WS 'harness\skills') -Directory)
    if ($SA) { $dirs += Get-ChildItem (Join-Path $WS 'harness\skills-sa') -Directory }
    foreach ($src in $dirs) {
        $dst = Join-Path $SkillsDst $src.Name
        if (IsJunction $dst) { (Get-Item $dst -Force).Delete(); New-Item -ItemType Junction -Path $dst -Target $src.FullName | Out-Null; Ok "$($src.Name) (actualizada)" }
        elseif (Test-Path $dst) { Warn "$($src.Name): ya existe una skill con ese nombre que no es del harness, no se toca" }
        else { New-Item -ItemType Junction -Path $dst -Target $src.FullName | Out-Null; Ok $src.Name }
    }
}

function Install-Python {
    Write-Host "Python -> $WS\harness\.venv"
    if (-not (Get-Command py -ErrorAction SilentlyContinue)) { Warn 'falta Python: winget install Python.Python.3.12'; return }
    if (-not (Test-Path $VenvPy)) { & py -3 -m venv (Join-Path $WS 'harness\.venv') }
    & $VenvPy -m pip install -q --upgrade pip
    & $VenvPy -m pip install -q -r (Join-Path $WS 'harness\requirements.txt')
    Ok 'dependencias desde PyPI'
}

# Los hooks de sesión y las guardas los registra un solo script (idempotente, con backup al lado de settings.json).
function Install-Hook {
    Write-Host "Hooks -> $Settings"
    if (-not (Test-Path $Settings)) { Set-Content -Path $Settings -Value '{}' -Encoding ascii }
    $out = & py -3 (Join-Path $WS 'harness\scripts\install_hooks.py')
    Ok $out
}

function Install-Config {
    $cfg = Join-Path $WS 'harness\config.toml'
    if (Test-Path $cfg) { Ok 'config.toml ya existe'; return }
    Copy-Item (Join-Path $WS 'harness\config.example.toml') $cfg
    Warn "config.toml creado desde el ejemplo: completá [user] (name, email, role, slack_user_id) en $cfg"
}

function Show-Status {
    Write-Host 'Skills:'
    foreach ($s in Get-ChildItem (Join-Path $WS 'harness\skills') -Directory) {
        if (IsJunction (Join-Path $SkillsDst $s.Name)) { Ok $s.Name } else { Warn "$($s.Name) no instalada" }
    }
    foreach ($s in Get-ChildItem (Join-Path $WS 'harness\skills-sa') -Directory) {
        if (IsJunction (Join-Path $SkillsDst $s.Name)) { Ok "$($s.Name) (perfil SA)" }
    }
    Write-Host 'Python:'; if (Test-Path $VenvPy) { Ok 'harness\.venv' } else { Warn 'sin venv' }
    Write-Host 'Hooks:'; if ((Test-Path $Settings) -and (Select-String -Path $Settings -SimpleMatch 'session-start.sh' -Quiet)) { Ok 'SessionStart' } else { Warn 'no instalado' }
    if ((Test-Path $Settings) -and (Select-String -Path $Settings -SimpleMatch 'guard.sh' -Quiet)) { Ok 'guardas' } else { Warn 'guardas no registradas' }
    Write-Host 'Config:'; if (Test-Path (Join-Path $WS 'harness\config.toml')) { Ok 'config.toml' } else { Warn 'falta config.toml' }
    Write-Host 'Diagramas:'; if (Test-Path (Join-Path $HOME '.dino\aws-diagram\aws-nodes.txt')) { Ok 'aws-diagram listo' } else { Warn 'falta correr -Diagrams' }
    Write-Host 'Google:'; if (Test-Path (Join-Path $HOME '.config\claude-harness\google-client.json')) { Ok 'cliente OAuth' } else { Warn 'sin cliente OAuth (ver la guía, sección API de Google)' }
    Write-Host 'Rutinas:'
    foreach ($r in 'daily', 'weekly', 'friday') {
        if (Get-ScheduledTask -TaskName "DinoCloud Harness $r" -ErrorAction SilentlyContinue) { Ok $r } else { Warn "$r no registrada" }
    }
}

if ($Status) { Show-Status; exit 0 }
Install-Skills
if (-not $NoPython) { Install-Python }
if (-not $NoHook) { Install-Hook }
Install-Config
if ($Diagrams) { & $Bash -lc ('bash "' + ($WS -replace '\\', '/') + '/harness/skills/aws-diagram/setup.sh"') }
if ($Tasks) { & (Join-Path $WS 'harness\windows\install-tasks.ps1') }
Write-Host ''
Write-Host 'Listo. Abrí una sesión nueva de Claude Code y corré /skills para ver las skills del harness.'
