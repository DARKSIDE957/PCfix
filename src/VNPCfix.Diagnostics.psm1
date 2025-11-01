Set-StrictMode -Version Latest

function Get-SystemInfo {
  $os = try { Get-CimInstance Win32_OperatingSystem } catch { $null }
  $cpu = try { Get-CimInstance Win32_Processor | Select-Object -First 1 } catch { $null }
  $mem = try { Get-CimInstance Win32_PhysicalMemory | Measure-Object -Property Capacity -Sum } catch { $null }
  $disk = try { Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" } catch { $null }
  [ordered]@{
    OS    = if ($os) { "{0} {1} (Build {2})" -f $os.Caption, $os.Version, $os.BuildNumber } else { 'Unknown OS' }
    CPU   = if ($cpu) { $cpu.Name } else { 'Unknown CPU' }
    Memory= if ($mem) { '{0:N2} GB' -f ($mem.Sum / 1GB) } else { 'Unknown Memory' }
    Disks = if ($disk) { ($disk | ForEach-Object { "{0} {1:N0}GB free/{2:N0}GB" -f $_.DeviceID, ($_.FreeSpace/1GB), ($_.Size/1GB) }) } else { @('Unknown Disks') }
  }
}

function Get-RecentCriticalEvents {
  try {
    Get-WinEvent -MaxEvents 10 -FilterHashtable @{ LogName='System'; Level=1 } | ForEach-Object { $_.Message } | ForEach-Object { $_ -replace '\r?\n',' ' }
  } catch {
    @('Unable to query events')
  }
}

function Invoke-VNPCfixDiagnostics {
  [CmdletBinding()] param()
  try {
    $info = Get-SystemInfo
    $lines = @(
      "OS: $($info.OS)",
      "CPU: $($info.CPU)",
      "Memory: $($info.Memory)"
    ) + $info.Disks
    Write-Panel -Title 'System Information' -Lines $lines
    $events = Get-RecentCriticalEvents
    Write-Panel -Title 'Recent Critical Events' -Lines $events
    Write-Status Success 'Diagnostics completed.'
    Write-Log -Message 'Diagnostics completed' -Level INFO
  } catch {
    Write-Status Error "Diagnostics failed: $($_.Exception.Message)"
    Write-Log -Message "Diagnostics failed: $($_.Exception.Message)" -Level ERROR
    throw
  }
}

Export-ModuleMember -Function Invoke-VNPCfixDiagnostics