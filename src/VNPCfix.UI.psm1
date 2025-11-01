Set-StrictMode -Version Latest

# Color palette with accessibility toggles
$script:Colors = [ordered]@{
  Accent     = 'Cyan'
  Accent2    = 'Yellow'
  Info       = 'Gray'
  Success    = 'Green'
  Warning    = 'Yellow'
  Error      = 'Red'
}

$script:Symbols = [ordered]@{
  Info    = 'i'
  Success = '+'
  Warning = '!'
  Error   = 'x'
}

$script:UI = [ordered]@{
  HighContrast = $false
  NoColor      = $false
  BasicASCII   = $false
  LargeText    = $false
}

function Initialize-Theme {
  param([switch]$HighContrast,[switch]$NoColor,[switch]$BasicASCII,[switch]$LargeText)
  $script:UI.HighContrast = $HighContrast.IsPresent
  $script:UI.NoColor      = $NoColor.IsPresent
  $script:UI.BasicASCII   = $BasicASCII.IsPresent
  $script:UI.LargeText    = $LargeText.IsPresent

  $enc = try { [Console]::OutputEncoding } catch { [Text.Encoding]::UTF8 }
  if ($enc.WebName -ne 'utf-8') { $script:UI.BasicASCII = $true }

  if ($script:UI.HighContrast) {
    $script:Colors.Accent  = 'White'
    $script:Colors.Accent2 = 'White'
    $script:Colors.Info    = 'White'
    $script:Colors.Success = 'White'
    $script:Colors.Warning = 'White'
    $script:Colors.Error   = 'White'
  }
}

function Write-ColorHost {
  param([string]$Text,[string]$Foreground=$null,[string]$Background=$null)
  if ($script:UI.NoColor) { Write-Host $Text; return }
  if ($Foreground -and $Background) { Write-Host $Text -ForegroundColor $Foreground -BackgroundColor $Background; return }
  if ($Foreground) { Write-Host $Text -ForegroundColor $Foreground; return }
  Write-Host $Text
}

function Get-ConsoleWidth { try { $Host.UI.RawUI.WindowSize.Width } catch { 80 } }
function Center-Text([string]$Text) {
  $width = Get-ConsoleWidth
  $pad = [Math]::Max(0, [Math]::Floor(($width - $Text.Length) / 2))
  return (' ' * $pad) + $Text
}

function Write-Separator { Write-ColorHost ('-' * (Get-ConsoleWidth)) $script:Colors.Info }
function Write-Title([string]$Title) {
  if ($script:UI.LargeText) { Write-Host '' }
  Write-ColorHost (Center-Text $Title) $script:Colors.Accent
  if ($script:UI.LargeText) { Write-Host '' }
}
function Write-Status([ValidateSet('Info','Success','Warning','Error')][string]$Type,[string]$Message) {
  $color = switch ($Type) { 'Info' { $script:Colors.Info } 'Success' { $script:Colors.Success } 'Warning' { $script:Colors.Warning } 'Error' { $script:Colors.Error } }
  $symbol = $script:Symbols[$Type]
  Write-ColorHost ("[{0}] {1}" -f $symbol, $Message) $color
}

function Format-MenuItem([int]$Number,[string]$Label,[string]$Suffix=$null) {
  $label = if ($Suffix) { " {0}) {1} {2}" -f $Number, $Label, $Suffix } else { " {0}) {1}" -f $Number, $Label }
  Write-ColorHost (Center-Text $label) $script:Colors.Info
}

function Write-Command([string]$Text) { Write-ColorHost (Center-Text $Text) $script:Colors.Accent2 }

function Write-HighlightedLine([string]$Text) {
  switch -Regex ($Text) {
    'error|failed|critical' { Write-ColorHost $Text $script:Colors.Error; break }
    'warning|deprecated'   { Write-ColorHost $Text $script:Colors.Warning; break }
    'success|ok|healthy'   { Write-ColorHost $Text $script:Colors.Success; break }
    default                { Write-ColorHost $Text $script:Colors.Info }
  }
}

function Write-Panel([string]$Title,[string[]]$Lines) {
  Write-Title $Title
  foreach ($ln in $Lines) { Write-HighlightedLine $ln }
  Write-Separator
}

function Get-AsciiLogo {
  @(
    ' __     _   ____  ____        ',
    ' \ \   | | |  _ \|  _ \       ',
    '  \ \  | | | |_) | |_) | ___  ',
    '   > > | | |  __/|  _ < / _ \ ',
    '  / /  | | | |   | |_) |  __/ ',
    ' /_/   |_| |_|   |____/ \___| ',
    '            VN PCfix          '
  )
}

function Show-Header([string]$Title,[string]$LogFile,[string]$SessionStamp,[switch]$IsAdmin) {
  Clear-Host
  Write-Title $Title
  foreach ($l in (Get-AsciiLogo)) { Write-ColorHost (Center-Text $l) $script:Colors.Accent }
  Write-Separator
  $adminBadge = if ($IsAdmin) { 'ADMIN' } else { 'STANDARD' }
  Write-Status Info "Session: $SessionStamp   [$adminBadge]"
  Write-Status Info "Log: $LogFile"
  Write-Separator
}

Export-ModuleMember -Function Initialize-Theme, Write-ColorHost, Center-Text, Write-Separator, Write-Title, Write-Status, Format-MenuItem, Write-Command, Write-HighlightedLine, Write-Panel, Show-Header