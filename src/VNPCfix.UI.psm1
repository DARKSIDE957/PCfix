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

  if ($script:UI.NoColor) {
    $script:Colors.Accent  = 'Gray'
    $script:Colors.Accent2 = 'Gray'
    $script:Colors.Info    = 'Gray'
    $script:Colors.Success = 'Gray'
    $script:Colors.Warning = 'Gray'
    $script:Colors.Error   = 'Gray'
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
function Get-ConsoleHeight { try { $Host.UI.RawUI.WindowSize.Height } catch { 25 } }
function Wrap-Text([string]$Text,[int]$Width=$null) {
  if (-not $Width) { $Width = Get-ConsoleWidth }
  $max = [Math]::Max(10, $Width - 2)
  $words = $Text -split '\s+'
  $lines = @('')
  foreach ($w in $words) {
    if (($lines[-1].Length + $w.Length + 1) -gt $max) { $lines += $w }
    else { if ($lines[-1].Length -eq 0) { $lines[-1] = $w } else { $lines[-1] += (' ' + $w) } }
  }
  return $lines
}
function Center-Text([string]$Text) {
  $width = Get-ConsoleWidth
  $pad = [Math]::Max(0, [Math]::Floor(($width - $Text.Length) / 2))
  return (' ' * $pad) + $Text
}

function Get-BoxChars {
  if ($script:UI.BasicASCII) { return @{ H='-'; V='|'; TL='+'; TR='+'; BL='+'; BR='+' } }
  return @{ H=[string]([char]0x2500); V=[string]([char]0x2502); TL=[string]([char]0x250C); TR=[string]([char]0x2510); BL=[string]([char]0x2514); BR=[string]([char]0x2518) }
}
function Write-Separator {
  $b = Get-BoxChars
  Write-ColorHost (($b.H) * (Get-ConsoleWidth)) $script:Colors.Info
}
function Write-Title([string]$Title) {
  $w = Get-ConsoleWidth
  $b = Get-BoxChars
  $innerW = [Math]::Max(10, $w - 2)
  $text = ' ' + $Title + ' '
  $pad = [Math]::Max(0, $innerW - $text.Length)
  $lp = [Math]::Floor($pad/2)
  $rp = $pad - $lp
  Write-ColorHost ($b.TL + ($b.H * $innerW) + $b.TR) $script:Colors.Accent
  Write-ColorHost ($b.V + (' ' * $lp) + $text + (' ' * $rp) + $b.V) $script:Colors.Accent
  Write-ColorHost ($b.BL + ($b.H * $innerW) + $b.BR) $script:Colors.Accent
}
function Write-Status([ValidateSet('Info','Success','Warning','Error')][string]$Type,[string]$Message) {
  $color = switch ($Type) { 'Info' { $script:Colors.Info } 'Success' { $script:Colors.Success } 'Warning' { $script:Colors.Warning } 'Error' { $script:Colors.Error } }
  $symbol = $script:Symbols[$Type]
  Write-ColorHost ("[{0}] {1}" -f $symbol, $Message) $color
}

function Format-MenuItem([int]$Number,[string]$Label,[string]$Suffix=$null) {
  $txt = if ($Suffix) { "[{0}] {1} {2}" -f $Number, $Label, $Suffix } else { "[{0}] {1}" -f $Number, $Label }
  Write-ColorHost (Center-Text $txt) $script:Colors.Info
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
  $b = Get-BoxChars
  $w = Get-ConsoleWidth
  $innerW = [Math]::Max(20, $w - 2)
  $titleTxt = ' ' + $Title + ' '
  $tp = [Math]::Max(0, $innerW - $titleTxt.Length)
  $tlp = [Math]::Floor($tp/2)
  $trp = $tp - $tlp
  Write-ColorHost ($b.TL + ($b.H * $innerW) + $b.TR) $script:Colors.Info
  Write-ColorHost ($b.V + (' ' * $tlp) + $titleTxt + (' ' * $trp) + $b.V) $script:Colors.Accent
  Write-ColorHost ($b.V + ($b.H * $innerW) + $b.V) $script:Colors.Info
  foreach ($ln in $Lines) {
    foreach ($seg in (Wrap-Text $ln $innerW)) {
      $lc = $seg.ToLower()
      $color = $script:Colors.Info
      if ($lc -match 'error|failed|critical') { $color = $script:Colors.Error }
      elseif ($lc -match 'warning|deprecated') { $color = $script:Colors.Warning }
      elseif ($lc -match 'success|ok|healthy|completed|done') { $color = $script:Colors.Success }
      $pad = [Math]::Max(0, $innerW - $seg.Length)
      Write-ColorHost ($b.V + $seg + (' ' * $pad) + $b.V) $color
    }
  }
  Write-ColorHost ($b.BL + ($b.H * $innerW) + $b.BR) $script:Colors.Info
}

function Get-AsciiLogo {
  @(
    ' \\        /        |\\   | ',
    '  \\      /         | \\  | ',
    '   \\    /          |  \\ | ',
    '    \\  /           |   \\| ',
    '     \\/            |    | ',
    '           VN              ',
    '          PCfix            '
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