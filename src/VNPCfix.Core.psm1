Set-StrictMode -Version Latest

$script:State = [ordered]@{
  IsAdmin     = $false
  SessionStamp= (Get-Date -Format 'yyyyMMdd-HHmmss')
  LogDir      = Join-Path $env:LOCALAPPDATA 'PCfix'
  LogFile     = $null
  UI          = [ordered]@{
    HighContrast = $false
    NoColor      = $false
    BasicASCII   = $false
    LargeText    = $false
  }
  ConfigPath  = $null
}

function Initialize-Logging {
  try {
    if (-not (Test-Path -LiteralPath $script:State.LogDir)) {
      New-Item -ItemType Directory -Path $script:State.LogDir -Force | Out-Null
    }
    $script:State.LogFile = Join-Path $script:State.LogDir ("pcfix-" + $script:State.SessionStamp + '.log')
  } catch {
    Write-Warning "Failed to initialize logging directory: $($_.Exception.Message)"
  }
}

function Write-Log {
  param(
    [Parameter(Mandatory)][string]$Message,
    [ValidateSet('INFO','WARN','ERROR','DEBUG')][string]$Level = 'INFO'
  )
  try {
    if (-not $script:State.LogFile) { Initialize-Logging }
    $entry = "[{0}] [{1}] {2}" -f (Get-Date).ToString('s'), $Level, $Message
    Add-Content -LiteralPath $script:State.LogFile -Value $entry
  } catch {
    Write-Warning "Log write failed: $($_.Exception.Message)"
  }
}

function Get-ConsoleEncoding {
  try {
    $enc = [Console]::OutputEncoding
    return $enc
  } catch {
    return [Text.Encoding]::UTF8
  }
}

function Set-VNPCfixOptions {
  param(
    [switch]$HighContrast,
    [switch]$NoColor,
    [switch]$BasicASCII,
    [switch]$LargeText
  )
  $script:State.UI.HighContrast = $HighContrast.IsPresent
  $script:State.UI.NoColor      = $NoColor.IsPresent
  $script:State.UI.BasicASCII   = $BasicASCII.IsPresent
  $script:State.UI.LargeText    = $LargeText.IsPresent
}

function Get-VNPCfixConfig {
  param([string]$Path)
  try {
    if (-not $Path) { $Path = Join-Path (Split-Path -Parent $PSScriptRoot) 'config\vnpcfix.json' }
    if (Test-Path -LiteralPath $Path) {
      $script:State.ConfigPath = $Path
      $json = Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
      return $json
    }
    return $null
  } catch {
    Write-Warning "Failed to load config: $($_.Exception.Message)"; return $null
  }
}

function Apply-VNPCfixConfig {
  param([psobject]$Config)
  if (-not $Config) { return }
  try {
    if ($null -ne $Config.UI) {
      foreach ($k in @('HighContrast','NoColor','BasicASCII','LargeText')) {
        if ($Config.UI.PSObject.Properties.Name -contains $k) {
          $script:State.UI[$k] = [bool]$Config.UI.$k
        }
      }
    }
  } catch {
    Write-Warning "Failed to apply config: $($_.Exception.Message)"
  }
}

Export-ModuleMember -Function Write-Log, Set-VNPCfixOptions, Get-VNPCfixConfig, Apply-VNPCfixConfig