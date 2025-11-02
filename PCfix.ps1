<#
.SYNOPSIS
PCfix – Windows Troubleshooting and Repair Console

.DESCRIPTION
Pure PowerShell console with interactive numbered menus and back navigation (0).
Works in both elevated and non-elevated sessions. Supports -WhatIf for dry-run.
Logs all actions to a timestamped log file under %TEMP%\PCfix.

.PARAMETER Help
Shows comprehensive help and exits.

.EXAMPLE
powershell -ExecutionPolicy Bypass -File .\PCfix.ps1

.EXAMPLE
powershell -ExecutionPolicy Bypass -File .\PCfix.ps1 -WhatIf

.NOTES
Compatible with Windows PowerShell 5.1 and later.
#>

[CmdletBinding(SupportsShouldProcess=$true, ConfirmImpact='Medium')]
param(
  [switch]$Help,
  [switch]$NoElevate,
  [switch]$HighContrast,
  [switch]$NoColor,
  [switch]$BasicASCII,
  [switch]$LargeText
)

#requires -version 5.1

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Prefer modular entrypoint if available
try {
  $moduleManifest = Join-Path $PSScriptRoot 'src/VNPCfix.psd1'
  if (Test-Path -LiteralPath $moduleManifest) {
    Import-Module $moduleManifest -Force
    $whatIfSwitch = [bool]$WhatIfPreference
    Start-VNPCfix -WhatIf:$whatIfSwitch -NoElevate:$NoElevate -HighContrast:$HighContrast -NoColor:$NoColor -BasicASCII:$BasicASCII -LargeText:$LargeText
    return
  }
} catch {
  Write-Warning "Modular entrypoint failed: $($_.Exception.Message). Falling back to legacy script."
}

function Test-IsAdmin {
  try {
    return ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
  } catch { return $false }
}

$Script:IsAdmin = Test-IsAdmin
$Script:SessionStamp = (Get-Date).ToString('yyyyMMdd-HHmmss')
$Script:LogDir = Join-Path $env:TEMP 'PCfix'
if (-not (Test-Path $Script:LogDir)) { New-Item -ItemType Directory -Path $Script:LogDir | Out-Null }
$Script:LogFile = Join-Path $Script:LogDir "pcfix-$Script:SessionStamp.log"

# UI helpers
$Script:Colors = @{ Primary='Cyan'; Accent='DarkCyan'; Success='Green'; Warning='Yellow'; Error='Red'; Muted='Gray' }
$Script:Symbols = if ($BasicASCII) { @{ Ok='[OK]'; Warn='[!]'; Err='[X]'; Info='[i]'; Prompt='[>]'; Back='[0] Back' } } else { @{ Ok='✔'; Warn='⚠'; Err='✖'; Info='ℹ'; Prompt='➤'; Back='[0] Back' } }

$Script:UI = @{ HighContrast=$HighContrast; NoColor=$NoColor; BasicASCII=$BasicASCII; LargeText=$LargeText }

function Write-ColorHost {
  param([string]$Text,[string]$Foreground,[string]$Background)
  if ($Script:UI.NoColor) {
    if ($Background) { Write-Host $Text -BackgroundColor $Background }
    else { Write-Host $Text }
  } else {
    if ($Background) { Write-Host $Text -ForegroundColor $Foreground -BackgroundColor $Background }
    else { Write-Host $Text -ForegroundColor $Foreground }
  }
}

function Initialize-Theme {
  if ($Script:UI.HighContrast) {
    $Script:Colors.Primary = 'White'
    $Script:Colors.Accent  = 'White'
    $Script:Colors.Success = 'Green'
    $Script:Colors.Warning = 'Yellow'
    $Script:Colors.Error   = 'Red'
    $Script:Colors.Muted   = 'Gray'
  }
}
Initialize-Theme

# Fallback to ASCII icons if console encoding likely cannot render Unicode
try {
  if (-not $Script:UI.BasicASCII) {
    $cp = [Console]::OutputEncoding.CodePage
    if ($cp -ne 65001) {
      $Script:UI.BasicASCII = $true
      $Script:Symbols = @{ Ok='[OK]'; Warn='[!]'; Err='[X]'; Info='[i]'; Prompt='[>]'; Back='[0] Back' }
    }
  }
} catch { }

function Get-ConsoleWidth { try { [int]$Host.UI.RawUI.WindowSize.Width } catch { 80 } }
function Center-Text {
  param([string]$Text)
  $w = Get-ConsoleWidth
  $pad = [Math]::Max(0, ($w - $Text.Length) / 2)
  return (' ' * [int]$pad) + $Text
}
function Write-Separator { param([string]$Color = $Script:Colors.Accent) Write-ColorHost ('-' * (Get-ConsoleWidth)) $Color $null }
function Write-Title {
  param([string]$Title)
  Write-Separator
  Write-ColorHost (Center-Text $Title) $Script:Colors.Primary $null
  Write-Separator
}
function Write-Status {
  param([ValidateSet('Info','Success','Warning','Error')] [string]$Type, [string]$Message)
  switch ($Type) {
    'Info'    { Write-ColorHost ("$($Script:Symbols.Info) $Message") $Script:Colors.Muted $null }
    'Success' { Write-ColorHost ("$($Script:Symbols.Ok)  $Message") $Script:Colors.Success $null }
    'Warning' { Write-ColorHost ("$($Script:Symbols.Warn) $Message") $Script:Colors.Warning $null }
    'Error'   { Write-ColorHost ("$($Script:Symbols.Err)  $Message") $Script:Colors.Error $null }
  }
}
function Format-MenuItem {
  param([string]$Key,[string]$Text,[switch]$Accent)
  $color = if ($Accent) { $Script:Colors.Primary } else { $Script:Colors.Muted }
  Write-ColorHost (" $Key) $Text") $color $null
}

function Write-Command { param([string]$Text) Write-ColorHost ("$($Script:Symbols.Prompt) $Text") $Script:Colors.Primary $null }
function Write-HighlightedLine {
  param([string]$Line)
  $lc = $Line.ToLower()
  if ($lc -match 'error|failed|denied|not found') { Write-ColorHost $Line $Script:Colors.Error $null; return }
  if ($lc -match 'warning|deprecated') { Write-ColorHost $Line $Script:Colors.Warning $null; return }
  if ($lc -match 'success|completed|ok|done') { Write-ColorHost $Line $Script:Colors.Success $null; return }
  if ($lc -match '\\b(sfc|dism|chkdsk|defrag|netsh|ipconfig|bcdedit|msiexec|reg\\.exe)\\b') { Write-ColorHost $Line $Script:Colors.Primary $null; return }
  Write-ColorHost $Line $Script:Colors.Muted $null
}
function Write-Panel {
  param([string]$Title,[string[]]$Lines)
  Write-Title $Title
  foreach ($ln in $Lines) { Write-HighlightedLine $ln }
  Write-Separator
}

function Get-AsciiLogo {
  $logo = @(
    ' __     _   ____  ____        ',
    ' \ \   | | |  _ \|  _ \       ',
    '  \ \  | | | |_) | |_) | ___  ',
    '   > > | | |  __/|  _ < / _ \ ',
    '  / /  | | | |   | |_) |  __/ ',
    ' /_/   |_| |_|   |____/ \___| ',
    '            VN PCfix          '
  )
  return $logo
}

# Auto-elevate if not running as Administrator
if (-not $Script:IsAdmin -and -not $NoElevate) {
  Write-Host 'PCfix requires Administrator privileges. Attempting to elevate...' -ForegroundColor Yellow
  $argList = @('-ExecutionPolicy','Bypass','-File',"`"$PSCommandPath`"")
  if ($Help) { $argList += '-Help' }
  if ($WhatIfPreference) { $argList += '-WhatIf' }
  try {
    Start-Process -FilePath powershell -ArgumentList $argList -Verb RunAs | Out-Null
    Write-Host 'A UAC prompt should appear. Proceed in the elevated window.' -ForegroundColor Green
    exit
  } catch {
    Write-Host 'Unable to obtain Administrator privileges. Please right-click PowerShell and choose "Run as administrator".' -ForegroundColor Red
    exit 1
  }
}

function Write-Log {
  param([string]$Message, [string]$Level = 'INFO')
  $ts = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
  $line = "$ts [$Level] $Message"
  Add-Content -Path $Script:LogFile -Value $line
}

function Show-Header {
  Clear-Host
  Write-Title 'VN PCfix – Windows Troubleshooting & Repair'
  foreach ($l in (Get-AsciiLogo)) { Write-ColorHost (Center-Text $l) $Script:Colors.Accent $null }
  Write-Separator
  $adminBadge = if ($Script:IsAdmin) { 'ADMIN' } else { 'STANDARD' }
  Write-Status Info "Session: $Script:SessionStamp   [$adminBadge]"
  Write-Status Info "Log: $Script:LogFile"
  if ($Script:UI.LargeText) { Write-Host '' }
}

function Pause-PCfix { Write-Host ''; Read-Host 'Press Enter to continue [↵]' | Out-Null }

function Request-Elevation {
  if ($Script:IsAdmin) { return }
  $confirm = Read-Host 'This action may require Administrator rights. Elevate now? (Y/N)'
  if ($confirm -match '^(y|yes)$') {
    Write-Log 'Elevation requested by user'
    Start-Process -FilePath powershell -ArgumentList "-ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    Write-Host 'Launched elevated session. Close this window if desired.' -ForegroundColor Yellow
  }
}

function Ensure-Admin {
  if ($Script:IsAdmin) { return $true }
  Write-Host 'Administrator privileges are required to proceed with repairs.' -ForegroundColor Yellow
  $confirm = Read-Host 'Attempt elevation now? (Y/N)'
  if ($confirm -match '^(y|yes)$') {
    try {
      Start-Process -FilePath powershell -ArgumentList "-ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs | Out-Null
      Write-Log 'Elevation attempt launched'
      Write-Host 'A UAC prompt should appear. Please re-run operations in the elevated window.' -ForegroundColor Green
      return $false
    } catch {
      Write-Log "Elevation failed: $($_.Exception.Message)" 'ERROR'
      Write-Host 'Unable to obtain Administrator privileges. Repairs cannot continue.' -ForegroundColor Red
      return $false
    }
  } else {
    Write-Host 'Repairs cancelled without elevation.' -ForegroundColor DarkYellow
    return $false
  }
}

function Test-SystemRequirements {
  $req = @()
  try { $os = Get-CimInstance Win32_OperatingSystem; $req += @{ name='Windows Version'; value=$os.Caption; ok=$true } } catch { $req += @{ name='Windows Version'; ok=$false; error=$_.Exception.Message } }
  try { $req += @{ name='BITS service'; ok=$null -ne (Get-Service bits -ErrorAction Stop) } } catch { $req += @{ name='BITS service'; ok=$false; error=$_.Exception.Message } }
  try { $req += @{ name='Windows Update service'; ok=$null -ne (Get-Service wuauserv -ErrorAction Stop) } } catch { $req += @{ name='Windows Update service'; ok=$false; error=$_.Exception.Message } }
  try { $req += @{ name='Defender Cmdlets'; ok=$null -ne (Get-Command Start-MpScan -ErrorAction Stop) } } catch { $req += @{ name='Defender Cmdlets'; ok=$false; error=$_.Exception.Message } }
  return $req
}

function Show-ProgressLoop {
  param([string]$Activity, [System.Diagnostics.Process]$Proc)
  $i = 0
  while (-not $Proc.HasExited) {
    Write-Progress -Activity $Activity -Status 'Working...' -PercentComplete (($i % 100))
    Start-Sleep -Milliseconds 500
    $i += 7
  }
  Write-Progress -Activity $Activity -Completed
}

function Test-SystemState {
  [CmdletBinding()] param()
  $state = @{}
  try { $state.os = Get-CimInstance Win32_OperatingSystem | Select-Object Caption, Version, BuildNumber, LastBootUpTime } catch {}
  try { $state.disks = Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" | Select-Object DeviceID, Size, FreeSpace } catch {}
  try { $state.services = @(
    @{ name='wuauserv'; status=(Get-Service wuauserv -ErrorAction SilentlyContinue).Status },
    @{ name='bits';     status=(Get-Service bits -ErrorAction SilentlyContinue).Status },
    @{ name='Dnscache'; status=(Get-Service Dnscache -ErrorAction SilentlyContinue).Status }
  ) } catch {}
  return $state
}

function Compare-State {
  param($Before,$After)
  Write-Host 'State changes:' -ForegroundColor Cyan
  try {
    foreach ($d in $After.disks) {
      $prev = $Before.disks | Where-Object DeviceID -eq $d.DeviceID
      if ($prev) {
        $delta = [math]::Round(($d.FreeSpace - $prev.FreeSpace) / 1GB, 2)
        Write-Host " - $($d.DeviceID): FreeSpace delta = ${delta} GB" -ForegroundColor Gray
      }
    }
  } catch {}
}

function New-SystemRestorePoint {
  [CmdletBinding()] param([string]$Description = "PCfix Restore Point $Script:SessionStamp")
  if (-not $Script:IsAdmin) { Write-Host 'Restore point requires Admin.' -ForegroundColor Yellow; return }
  Write-Host "Creating system restore point: $Description" -ForegroundColor Yellow
  Write-Log "Restore point requested: $Description"
  try {
    Checkpoint-Computer -Description $Description -RestorePointType 'MODIFY_SETTINGS'
    Write-Host 'Restore point created.' -ForegroundColor Green
    Write-Log 'Restore point created'
  } catch {
    Write-Log "Restore point failed: $($_.Exception.Message)" 'ERROR'
    Write-Host 'Restore point creation failed or disabled.' -ForegroundColor Red
  }
}

# Diagnostics
function Invoke-PCfixDiagnostics {
  [CmdletBinding(SupportsShouldProcess=$true)] param()
  Write-Status Info 'Running diagnostics...'
  Write-Log 'Diagnostics started'
  try {
    $os = Get-CimInstance Win32_OperatingSystem | Select-Object Caption, Version, BuildNumber, LastBootUpTime
    $disk = Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" | Select-Object DeviceID, Size, FreeSpace
    $mem = Get-CimInstance Win32_ComputerSystem | Select-Object TotalPhysicalMemory
    $cpu = Get-CimInstance Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors, MaxClockSpeed

    $checks = @()
    try { $checks += @{ name='Windows Update service'; ok=(Get-Service wuauserv).Status -eq 'Running' } } catch { $checks += @{ name='Windows Update service'; ok=$false; error=$_.Exception.Message } }
    try { $checks += @{ name='BITS service'; ok=(Get-Service bits).Status -eq 'Running' } } catch { $checks += @{ name='BITS service'; ok=$false; error=$_.Exception.Message } }
    try { $checks += @{ name='DNS Client'; ok=(Get-Service Dnscache).Status -eq 'Running' } } catch { $checks += @{ name='DNS Client'; ok=$false; error=$_.Exception.Message } }

    $events = Get-WinEvent -FilterHashtable @{LogName='System'; Level=1; StartTime=(Get-Date).AddDays(-3)} -MaxEvents 20 | Select-Object TimeCreated, ProviderName, Id, LevelDisplayName, Message

    Write-Title 'Diagnostics'
    $osLines = @("OS: $($os.Caption)", "Version: $($os.Version) Build $($os.BuildNumber)", "Last Boot: $([datetime]$os.LastBootUpTime)")
    Write-Panel 'System' $osLines

    $diskLines = @()
    foreach ($d in $disk) { $diskLines += ("{0}: Free {1:N1} GB / Size {2:N1} GB" -f $d.DeviceID, ($d.FreeSpace/1GB), ($d.Size/1GB)) }
    Write-Panel 'Disks' $diskLines

    $cpuLines = @("CPU: $($cpu.Name)", "Cores: $($cpu.NumberOfCores) Threads: $($cpu.NumberOfLogicalProcessors)", "Max Clock: $($cpu.MaxClockSpeed) MHz")
    Write-Panel 'CPU' $cpuLines

    $memLines = @(("RAM: {0:N1} GB total" -f ($mem.TotalPhysicalMemory/1GB)))
    Write-Panel 'Memory' $memLines

    $svcLines = @()
    foreach ($c in $checks) { $svcLines += ("{0}: {1}" -f $c.name, ($(if ($c.ok) { 'Running' } else { 'Stopped/Failed' }))) }
    Write-Panel 'Services' $svcLines

    $evtLines = @()
    foreach ($e in $events | Select-Object -First 5) { $evtLines += ("{0:yyyy-MM-dd HH:mm} [{1} {2}] {3}" -f $e.TimeCreated, $e.ProviderName, $e.Id, $e.LevelDisplayName) }
    Write-Panel 'Recent Critical Events' $evtLines

    $result = @{ os=$os; disk=$disk; mem=$mem; cpu=$cpu; checks=$checks; criticalEvents=$events }
    $jsonPath = Join-Path $Script:LogDir "diagnostics-$Script:SessionStamp.json"
    $result | ConvertTo-Json -Depth 6 | Tee-Object -FilePath $jsonPath | Out-Host
    Write-Log "Diagnostics completed; saved to $jsonPath"
  } catch {
    Write-Log "Diagnostics error: $($_.Exception.Message)" 'ERROR'
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
  }
}

# Repairs
function Invoke-PCfixSfcRepair {
  [CmdletBinding(SupportsShouldProcess=$true)] param()
  if ($PSCmdlet.ShouldProcess('System files','Run sfc /scannow')) {
    Write-Host 'Running SFC scan...' -ForegroundColor Yellow
    Write-Log 'SFC started'
    try {
      $proc = Start-Process -FilePath sfc -ArgumentList '/scannow' -NoNewWindow -PassThru
      Show-ProgressLoop -Activity 'SFC /scannow' -Proc $proc
      $proc.WaitForExit()
      Write-Log "SFC exited with code $($proc.ExitCode)"
      Write-Host "SFC completed (ExitCode: $($proc.ExitCode))" -ForegroundColor Green
    } catch {
      Write-Log "SFC error: $($_.Exception.Message)" 'ERROR'
      Write-Host $_ -ForegroundColor Red
    }
  }
}

function Invoke-PCfixDismRepair {
  [CmdletBinding(SupportsShouldProcess=$true)] param()
  if ($PSCmdlet.ShouldProcess('Component store','Run DISM RestoreHealth')) {
    Write-Status Info 'Running DISM /Online /Cleanup-Image /RestoreHealth...'
    Write-Log 'DISM RestoreHealth started'
    try {
      $args = '/Online','/Cleanup-Image','/RestoreHealth'
      $proc = Start-Process -FilePath dism.exe -ArgumentList $args -NoNewWindow -PassThru
      Show-ProgressLoop -Activity 'DISM RestoreHealth' -Proc $proc
      $proc.WaitForExit()
      Write-Log "DISM exited with code $($proc.ExitCode)"
      if ($proc.ExitCode -eq 0) { Write-Status Success 'DISM RestoreHealth completed.' }
      else { Write-Status Warning "DISM completed with exit code $($proc.ExitCode)." }
    } catch {
      Write-Log "DISM error: $($_.Exception.Message)" 'ERROR'
      Write-Status Error "DISM failed: $($_.Exception.Message)"
    }
  }
}

function Invoke-PCfixChkdskScan {
  [CmdletBinding(SupportsShouldProcess=$true)] param([string]$Drive='C:')
  if ($PSCmdlet.ShouldProcess($Drive,'Run chkdsk /scan')) {
    Write-Host "Running chkdsk /scan on $Drive..." -ForegroundColor Yellow
    Write-Log "Chkdsk scan started on $Drive"
    try {
      $proc = Start-Process -FilePath chkdsk -ArgumentList "$Drive /scan" -NoNewWindow -PassThru
      Show-ProgressLoop -Activity "chkdsk /scan ($Drive)" -Proc $proc
      $proc.WaitForExit()
      Write-Log "Chkdsk scan exit code $($proc.ExitCode)"
      Write-Host "Chkdsk scan completed (ExitCode: $($proc.ExitCode))" -ForegroundColor Green
    } catch { Write-Log "Chkdsk scan error: $($_.Exception.Message)" 'ERROR'; Write-Host $_ -ForegroundColor Red }
  }
}

function Invoke-PCfixChkdskFix {
  [CmdletBinding(SupportsShouldProcess=$true)] param([string]$Drive='C:')
  Write-Host 'Warning: /f may schedule repair at next reboot.' -ForegroundColor Yellow
  $ok = Read-Host ('Proceed to schedule chkdsk /f on {0}? (Y/N)' -f $Drive)
  if ($ok -notmatch '^(y|yes)$') { Write-Host 'Cancelled.' -ForegroundColor DarkYellow; return }
  if ($PSCmdlet.ShouldProcess($Drive,'Run chkdsk /f')) {
    Write-Log "Chkdsk /f requested on $Drive"
    try {
      $proc = Start-Process -FilePath chkdsk -ArgumentList "$Drive /f" -NoNewWindow -PassThru
      Show-ProgressLoop -Activity "chkdsk /f ($Drive)" -Proc $proc
      $proc.WaitForExit()
      Write-Log "Chkdsk /f exit code $($proc.ExitCode)"
      Write-Host 'If prompted, repair is scheduled for next reboot.' -ForegroundColor Green
    } catch { Write-Log "Chkdsk /f error: $($_.Exception.Message)" 'ERROR'; Write-Host $_ -ForegroundColor Red }
  }
}

function Invoke-PCfixWURepair {
  [CmdletBinding(SupportsShouldProcess=$true)] param()
  if (-not $Script:IsAdmin) { Write-Host 'Windows Update repair requires Admin.' -ForegroundColor Yellow; Request-Elevation }
  Write-Log 'Windows Update repair started'
  $folder = Join-Path $env:SystemRoot 'SoftwareDistribution'
  if ($PSCmdlet.ShouldProcess('Windows Update components','Stop services and clear cache')) {
    try { Stop-Service wuauserv -Force -ErrorAction SilentlyContinue; Write-Log 'Stopped wuauserv' } catch { Write-Log "Stop wuauserv failed: $($_.Exception.Message)" 'WARN' }
    try { Stop-Service bits -Force -ErrorAction SilentlyContinue; Write-Log 'Stopped BITS' } catch { Write-Log "Stop BITS failed: $($_.Exception.Message)" 'WARN' }
    try { Rename-Item -Path $folder -NewName ('SoftwareDistribution.bak.' + $Script:SessionStamp) -ErrorAction SilentlyContinue; Write-Log 'Renamed SoftwareDistribution' } catch { Write-Log "Rename SoftwareDistribution failed: $($_.Exception.Message)" 'WARN' }
    try { Start-Service wuauserv -ErrorAction SilentlyContinue; Write-Log 'Started wuauserv' } catch { Write-Log "Start wuauserv failed: $($_.Exception.Message)" 'WARN' }
    try { Start-Service bits -ErrorAction SilentlyContinue; Write-Log 'Started BITS' } catch { Write-Log "Start BITS failed: $($_.Exception.Message)" 'WARN' }
    Write-Host 'Windows Update repair completed.' -ForegroundColor Green
  }
}

function Invoke-PCfixDiskCleanup {
  [CmdletBinding(SupportsShouldProcess=$true)] param()
  if ($PSCmdlet.ShouldProcess('Disk','Cleanup temporary data')) {
    Write-Host 'Cleaning TEMP, Prefetch, Recycle Bin...' -ForegroundColor Yellow
    Write-Log 'Disk cleanup started'
    $steps = @()
    try { $temp = $env:TEMP; Get-ChildItem $temp -Force -Recurse -ErrorAction SilentlyContinue | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue; $steps += "Cleared TEMP: $temp" } catch { $steps += "TEMP cleanup failed: $($_.Exception.Message)" }
    try { $prefetch = "$env:SystemRoot\Prefetch"; Get-ChildItem $prefetch -Force -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue; $steps += 'Cleared Prefetch' } catch { $steps += "Prefetch cleanup failed: $($_.Exception.Message)" }
    try { $recycle = "$env:SystemDrive\`$Recycle.Bin"; Get-ChildItem $recycle -Force -Recurse -ErrorAction SilentlyContinue | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue; $steps += 'Emptied Recycle Bin' } catch { $steps += "Recycle Bin cleanup failed: $($_.Exception.Message)" }
    $steps | ForEach-Object { Write-Host " - $_" }
    Write-Log "Disk cleanup steps: $(($steps -join '; '))"
  }
}

function Invoke-PCfixDefrag {
  [CmdletBinding(SupportsShouldProcess=$true)] param([string]$Drive='C:')
  if ($PSCmdlet.ShouldProcess($Drive,'Defragment/Optimize')) {
    Write-Host "Optimizing drive $Drive (defrag /O)..." -ForegroundColor Yellow
    Write-Log "Defrag started for $Drive"
    try {
      $proc = Start-Process -FilePath defrag.exe -ArgumentList "$Drive /O" -NoNewWindow -PassThru
      Show-ProgressLoop -Activity "Defrag $Drive" -Proc $proc
      $proc.WaitForExit()
      Write-Log "Defrag exit code $($proc.ExitCode)"
      Write-Host 'Defrag/Optimize completed.' -ForegroundColor Green
    } catch { Write-Log "Defrag error: $($_.Exception.Message)" 'ERROR'; Write-Host $_ -ForegroundColor Red }
  }
}

function Invoke-PCfixRegistryRepair {
  [CmdletBinding(SupportsShouldProcess=$true)] param()
  if (-not $Script:IsAdmin) { Write-Host 'Registry repair requires Admin.' -ForegroundColor Yellow; Request-Elevation; return }
  $backupPath = Join-Path $Script:LogDir ("registry-backup-Installer-$Script:SessionStamp.reg")
  Write-Host 'Backing up Windows Installer registry key...' -ForegroundColor Yellow
  try { & reg.exe export "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Installer" "$backupPath" /y | Out-Null; Write-Log "Exported Installer key to $backupPath" } catch { Write-Log "Registry export failed: $($_.Exception.Message)" 'ERROR' }
  if ($PSCmdlet.ShouldProcess('Windows Installer','Re-register MSI service')) {
    try {
      Write-Host 'Re-registering Windows Installer...' -ForegroundColor Yellow
      & msiexec /unregister | Out-Null
      & msiexec /regserver | Out-Null
      Write-Log 'Windows Installer re-registered'
      Write-Host 'Registry repair completed.' -ForegroundColor Green
    } catch { Write-Log "MSI re-register failed: $($_.Exception.Message)" 'ERROR'; Write-Host 'Registry repair failed.' -ForegroundColor Red }
  }
}

function Invoke-PCfixRegistryRollback {
  [CmdletBinding()] param()
  $backup = Get-ChildItem $Script:LogDir -Filter "registry-backup-Installer-*.reg" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
  if (-not $backup) { Write-Host 'No registry backup found.' -ForegroundColor Yellow; return }
  if (-not $Script:IsAdmin) { Write-Host 'Registry rollback requires Admin.' -ForegroundColor Yellow; return }
  $ok = Read-Host "Restore registry from backup '$($backup.Name)'? (Y/N)"
  if ($ok -notmatch '^(y|yes)$') { Write-Host 'Cancelled.' -ForegroundColor DarkYellow; return }
  try { & reg.exe import $backup.FullName | Out-Null; Write-Log "Imported registry backup $($backup.FullName)"; Write-Host 'Registry rollback completed.' -ForegroundColor Green } catch { Write-Log "Registry import failed: $($_.Exception.Message)" 'ERROR'; Write-Host 'Registry rollback failed.' -ForegroundColor Red }
}

function Invoke-PCfixNetAdapterReset {
  [CmdletBinding(SupportsShouldProcess=$true)] param()
  if (-not $Script:IsAdmin) { Write-Host 'Adapter reset requires Admin.' -ForegroundColor Yellow; Request-Elevation }
  try {
    $adapters = Get-NetAdapter -Physical -ErrorAction Stop | Where-Object {$_.Status -eq 'Up'}
  } catch { Write-Host 'NetAdapter cmdlets unavailable.' -ForegroundColor Red; Write-Log 'NetAdapter cmdlets unavailable' 'ERROR'; return }
  Write-Host "Adapters to reset: $($adapters.Name -join ', ')" -ForegroundColor Gray
  foreach ($a in $adapters) {
    if ($PSCmdlet.ShouldProcess($a.Name,'Disable then Enable')) {
      try { Disable-NetAdapter -Name $a.Name -Confirm:$false -ErrorAction Stop; Start-Sleep -Seconds 2; Enable-NetAdapter -Name $a.Name -Confirm:$false -ErrorAction Stop; Write-Log "Reset adapter $($a.Name)" } catch { Write-Log "Adapter reset error ($($a.Name)): $($_.Exception.Message)" 'ERROR' }
    }
  }
  Write-Host 'Adapter reset completed.' -ForegroundColor Green
}

function Invoke-PCfixDNSFlush {
  [CmdletBinding(SupportsShouldProcess=$true)] param()
  if ($PSCmdlet.ShouldProcess('DNS Client','Flush cache')) {
    Write-Log 'DNS flush requested'
    try { Clear-DnsClientCache -ErrorAction Stop; Write-Host 'Flushed DNS client cache.' -ForegroundColor Green } catch { Write-Log "Clear-DnsClientCache failed: $($_.Exception.Message)" 'WARN'; try { cmd /c 'ipconfig /flushdns' | Out-Null; Write-Host 'Flushed DNS via ipconfig.' -ForegroundColor Green } catch { Write-Host 'DNS flush failed.' -ForegroundColor Red } }
  }
}

function Invoke-PCfixDefenderQuickScan {
  [CmdletBinding(SupportsShouldProcess=$true)] param()
  if ($PSCmdlet.ShouldProcess('Windows Defender','Quick scan')) {
    try { Start-MpScan -ScanType QuickScan; Write-Log 'Defender QuickScan started'; Write-Host 'Defender Quick Scan started.' -ForegroundColor Green } catch { Write-Log "Defender scan error: $($_.Exception.Message)" 'ERROR'; Write-Host 'Defender scan unavailable.' -ForegroundColor Red }
  }
}

# Menus
function Show-RepairsMenu {
  while ($true) {
    Show-Header
    Write-Title 'Repairs'
    Format-MenuItem '1' 'System File Checker (sfc /scannow)' -Accent
    Format-MenuItem '2' 'DISM RestoreHealth' -Accent
    Format-MenuItem '3' 'Disk Check (chkdsk /scan)'
    Format-MenuItem '4' 'Disk Repair (chkdsk /f) [confirm]'
    Format-MenuItem '5' 'Disk cleanup (TEMP/Prefetch/RecycleBin)'
    Format-MenuItem '6' 'Defragment/Optimize drive'
    Format-MenuItem '7' 'Windows Update repair'
    Format-MenuItem '8' 'Network fixes (reset adapters, winsock, IP, DNS)'
    Format-MenuItem '9' 'Registry repair (Windows Installer re-register)'
    Format-MenuItem '10' 'Create a system restore point'
    Format-MenuItem '11' 'Rollback (registry, WU cache rename)'
    Format-MenuItem '0' 'Back'
    if (-not (Ensure-Admin)) { Write-Host 'Note: Elevate and re-run repairs in the admin window.' -ForegroundColor Yellow; break }
    $sel = Read-Host 'Select an option'
    switch ($sel) {
      '1' { $b=Test-SystemState; Invoke-PCfixSfcRepair; $a=Test-SystemState; Compare-State $b $a; Pause-PCfix }
      '2' { $b=Test-SystemState; Invoke-PCfixDismRepair; $a=Test-SystemState; Compare-State $b $a; Pause-PCfix }
      '3' { Invoke-PCfixChkdskScan; Pause-PCfix }
      '4' { Invoke-PCfixChkdskFix; Pause-PCfix }
      '5' { $b=Test-SystemState; Invoke-PCfixDiskCleanup -WhatIf:$WhatIfPreference; $a=Test-SystemState; Compare-State $b $a; Pause-PCfix }
      '6' { Invoke-PCfixDefrag; Pause-PCfix }
      '7' { Invoke-PCfixWURepair; Pause-PCfix }
      '8' {
        Write-Host 'Network fixes:' -ForegroundColor Cyan
        Write-Host ' a) Reset adapters (disable/enable)'
        Write-Host ' b) Winsock reset'
        Write-Host ' c) IP reset'
        Write-Host ' d) DNS flush'
        $n = Read-Host 'Select (a/b/c/d)'
        switch ($n) {
          'a' { Invoke-PCfixNetAdapterReset }
          'b' { cmd /c 'netsh winsock reset' | Out-Host }
          'c' { cmd /c 'netsh int ip reset' | Out-Host }
          'd' { Invoke-PCfixDNSFlush }
          default { Write-Host 'Invalid selection' -ForegroundColor Red }
        }
        Pause-PCfix
      }
      '9'  { Invoke-PCfixRegistryRepair; Pause-PCfix }
      '10' { New-SystemRestorePoint; Pause-PCfix }
      '11' {
        Write-Host 'Rollback options:' -ForegroundColor Cyan
        Write-Host ' a) Restore registry backup (Installer key)'
        Write-Host ' b) Undo Windows Update cache rename'
        $r = Read-Host 'Select (a/b)'
        switch ($r) {
          'a' { Invoke-PCfixRegistryRollback }
          'b' {
            if (-not $Script:IsAdmin) { Write-Host 'Admin required.' -ForegroundColor Yellow }
            else {
              $bak = Get-ChildItem (Join-Path $env:SystemRoot '.') -Filter 'SoftwareDistribution.bak.*' -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
              if ($bak) {
                try { Rename-Item -Path $bak.FullName -NewName 'SoftwareDistribution' -Force; Write-Log "Restored WU cache from $($bak.Name)"; Write-Host 'WU cache restored.' -ForegroundColor Green } catch { Write-Log "WU cache restore failed: $($_.Exception.Message)" 'ERROR'; Write-Host 'WU cache restore failed.' -ForegroundColor Red }
              } else { Write-Host 'No WU cache backup found.' -ForegroundColor Yellow }
            }
          }
          default { Write-Host 'Invalid selection' -ForegroundColor Red }
        }
        Pause-PCfix
      }
      '0' { break }
      default { Write-Host 'Invalid selection' -ForegroundColor Red; Pause-PCfix }
    }
  }
}

function Show-MainMenu {
  while ($true) {
    Show-Header
    Write-Title 'Main Menu'
    Format-MenuItem '1' 'Diagnostics' -Accent
    Format-MenuItem '2' 'Repairs (requires Admin)'
    Format-MenuItem '0' 'Exit'
    Write-Host ''
    Write-Status Info 'Tip: Use -WhatIf to dry-run most actions.'
    if (-not $Script:IsAdmin) { Write-Status Warning 'Some actions require Administrator privileges.' }
    $sel = Read-Host 'Select an option'
    switch ($sel) {
      '1' { Invoke-PCfixDiagnostics; Pause-PCfix }
      '2' { Show-RepairsMenu }
      '0' { Write-Host 'Goodbye!' -ForegroundColor Green; return }
      default { Write-Host 'Invalid selection' -ForegroundColor Red; Pause-PCfix }
    }
  }
}

if ($Help) { Get-Help -Detailed -ErrorAction SilentlyContinue; Write-Host 'Run .\\PCfix.ps1 -WhatIf to simulate actions.' -ForegroundColor DarkGray; return }

Write-Log 'PCfix session started'
Show-MainMenu
Write-Log 'PCfix session ended'