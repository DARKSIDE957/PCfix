Set-StrictMode -Version Latest

# Core system info summary
function Get-SystemInfo {
  $os = try { Get-CimInstance Win32_OperatingSystem } catch { $null }
  $cpu = try { Get-CimInstance Win32_Processor | Select-Object -First 1 } catch { $null }
  $mem = try { Get-CimInstance Win32_PhysicalMemory | Measure-Object -Property Capacity -Sum } catch { $null }
  $disk = try { Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" } catch { $null }
  [ordered]@{
    OS      = if ($os) { "{0} {1} (Build {2})" -f $os.Caption, $os.Version, $os.BuildNumber } else { 'Unknown OS' }
    CPU     = if ($cpu) { $cpu.Name } else { 'Unknown CPU' }
    Memory  = if ($mem) { '{0:N2} GB' -f ($mem.Sum / 1GB) } else { 'Unknown Memory' }
    Disks   = if ($disk) { ($disk | ForEach-Object { "{0} {1:N0}GB free/{2:N0}GB" -f $_.DeviceID, ($_.FreeSpace/1GB), ($_.Size/1GB) }) } else { @('Unknown Disks') }
  }
}

# Windows Update and related service status
function Get-ServiceStatusSummary {
  $names = 'wuauserv','bits','cryptsvc','msiserver'
  $statuses = @()
  foreach ($n in $names) {
    $svc = try { Get-Service -Name $n -ErrorAction Stop } catch { $null }
    if ($svc) { $statuses += "{0}: {1}" -f $svc.Name, $svc.Status } else { $statuses += "${n}: Not found" }
  }
  return $statuses
}

# Network connectivity quick checks
function Test-NetworkConnectivitySummary {
  $results = @()
  $targets = @(
    @{ Label='DNS/Google'; Host='8.8.8.8'; Port=53 },
    @{ Label='Microsoft HTTPS'; Host='www.microsoft.com'; Port=443 }
  )
  foreach ($t in $targets) {
    try {
      $r = Test-NetConnection -ComputerName $t.Host -Port $t.Port -InformationLevel Quiet
      $results += ("{0}: {1}" -f $t.Label, ($(if ($r) { 'Reachable' } else { 'Unreachable' })))
    } catch {
      $results += ("{0}: Unsupported or error" -f $t.Label)
    }
  }
  return $results
}

# Storage health overview using modern cmdlets if available
function Get-StorageHealthSummary {
  $lines = @()
  try {
    $vols = Get-Volume -ErrorAction Stop
    foreach ($v in $vols) {
      $lines += ("{0} ({1}): {2:N0}GB free / {3:N0}GB" -f $v.DriveLetter, $v.FileSystemLabel, ($v.SizeRemaining/1GB), ($v.Size/1GB))
    }
  } catch {
    # Fallback to CIM logical disks
    try {
      $disk = Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3"
      foreach ($d in $disk) {
        $lines += ("{0}: {1:N0}GB free / {2:N0}GB" -f $d.DeviceID, ($d.FreeSpace/1GB), ($d.Size/1GB))
      }
    } catch {
      $lines += 'Unable to query storage'
    }
  }
  return $lines
}

function Get-RecentCriticalEvents {
  try {
    Get-WinEvent -MaxEvents 10 -FilterHashtable @{ LogName='System'; Level=1 } |
      ForEach-Object { $_.Message } |
      ForEach-Object { $_ -replace '\r?\n',' ' }
  } catch {
    @('Unable to query events')
  }
}

function Invoke-VNPCfixDiagnostics {
  [CmdletBinding()] param(
    [switch]$FullChecks
  )
  try {
    $info = Get-SystemInfo
    $services = Get-ServiceStatusSummary
    $network = Test-NetworkConnectivitySummary
    $storage = Get-StorageHealthSummary
    $events = Get-RecentCriticalEvents

    $sysLines = @(
      "OS: $($info.OS)",
      "CPU: $($info.CPU)",
      "Memory: $($info.Memory)"
    ) + $info.Disks
    Write-Panel -Title 'System Information' -Lines $sysLines
    Write-Panel -Title 'Service Status' -Lines $services
    Write-Panel -Title 'Network Connectivity' -Lines $network
    Write-Panel -Title 'Storage' -Lines $storage
    Write-Panel -Title 'Recent Critical Events' -Lines $events

    $dismCheck = $null
    if ($FullChecks) {
      try {
        Write-Title 'DISM CheckHealth'
        $dismOut = & DISM /Online /Cleanup-Image /CheckHealth 2>&1
        $dismCheck = ($dismOut | Select-String -Pattern 'No component store corruption detected|The component store is repairable|The component store is corrupted').Line
        Write-Separator
      } catch {
        $dismCheck = 'DISM CheckHealth failed'
      }
    }

    $result = [ordered]@{
      SystemInfo = $info
      Services   = $services
      Network    = $network
      Storage    = $storage
      Events     = $events
      DismCheckHealth = $dismCheck
      FullChecks = $FullChecks.IsPresent
    }

    Write-Status Success 'Diagnostics completed.'
    Write-Log -Message 'Diagnostics completed' -Level INFO
    return $result
  } catch {
    Write-Status Error "Diagnostics failed: $($_.Exception.Message)"
    Write-Log -Message "Diagnostics failed: $($_.Exception.Message)" -Level ERROR
    throw
  }
}

Export-ModuleMember -Function Invoke-VNPCfixDiagnostics