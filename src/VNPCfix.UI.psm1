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
  Theme        = 'Default'
  BoxStyle     = 'single'
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

function Set-ThemePreset {
  param([string]$Name)
  $n = if ($Name) { $Name.ToLower() } else { 'default' }
  switch ($n) {
    'vndark' {
      $script:UI.Theme = 'VNDark'
      $script:Colors.Accent  = 'White'
      $script:Colors.Accent2 = 'DarkCyan'
      $script:Colors.Info    = 'DarkGray'
      $script:Colors.Success = 'Green'
      $script:Colors.Warning = 'Yellow'
      $script:Colors.Error   = 'Red'
      $script:UI.BoxStyle    = 'double'
    }
    'vn' {
      $script:UI.Theme = 'VN'
      $script:Colors.Accent  = 'Cyan'
      $script:Colors.Accent2 = 'DarkCyan'
      $script:Colors.Info    = 'Gray'
      $script:Colors.Success = 'Green'
      $script:Colors.Warning = 'Yellow'
      $script:Colors.Error   = 'Red'
      $script:UI.BoxStyle    = 'single'
    }
    default {
      $script:UI.Theme = 'Default'
      $script:UI.BoxStyle = 'single'
    }
}
}

function Show-StatusBar {
  param([string]$Left,[string]$Right)
  $w = Get-ConsoleWidth
  $innerW = [Math]::Max(10, $w - 2)
  $l = if ($Left) { $Left } else { '' }
  $r = if ($Right) { $Right } else { '' }
  $space = [Math]::Max(0, $innerW - $l.Length - $r.Length)
  $line = $l + (' ' * $space) + $r
  Write-ColorHost $line $script:Colors.Info
}

function Start-Spinner {
  param([string]$Text,[int]$DurationSeconds=3)
  $frames = @('|','/','-','<')
  $t = [Math]::Max(1,$DurationSeconds)
  $end = (Get-Date).AddSeconds($t)
  $i = 0
  while ((Get-Date) -lt $end) {
    $f = $frames[$i % $frames.Count]
    Write-Host ("{0} {1}" -f $f, $Text)
    Start-Sleep -Milliseconds 200
    $i++
  }
}

function Write-Table {
  param([object[]]$Rows,[string[]]$Columns)
  if (-not $Rows -or -not $Columns) { return }
  $w = Get-ConsoleWidth
  $innerW = [Math]::Max(20, $w - 2)
  $widths = @()
  foreach ($c in $Columns) {
    $vals = @()
    foreach ($row in $Rows) {
      $prop = $row.PSObject.Properties[$c]
      $val = if ($prop) { "" + $prop.Value } else { "" }
      $vals += $val
    }
    $maxData = if ($vals.Count -gt 0) { ($vals | ForEach-Object { $_.Length } | Measure-Object -Maximum).Maximum } else { 0 }
    $maxLen = [Math]::Min(40, [Math]::Max($c.Length, $maxData))
    $widths += $maxLen
  }
  $total = ($widths | Measure-Object -Sum).Sum
  if ($total -gt $innerW) {
    $scale = $innerW / $total
    for ($i=0; $i -lt $widths.Count; $i++) { $widths[$i] = [Math]::Max(5, [Math]::Floor($widths[$i] * $scale)) }
  }
  $b = Get-BoxChars
  $line = $b.TL + ($b.H * $innerW) + $b.TR
  Write-ColorHost $line $script:Colors.Info
  $hdr = ''
  for ($i=0; $i -lt $Columns.Count; $i++) { $hdr += (' ' + $Columns[$i].PadRight($widths[$i]) + ' ') }
  $hdr = $hdr.TrimEnd()
  $pad = [Math]::Max(0, $innerW - $hdr.Length)
  Write-ColorHost ($b.V + $hdr + (' ' * $pad) + $b.V) $script:Colors.Accent
  Write-ColorHost ($b.V + ($b.H * $innerW) + $b.V) $script:Colors.Info
  foreach ($row in $Rows) {
    $ln = ''
    for ($i=0; $i -lt $Columns.Count; $i++) { $val = "" + $row.$($Columns[$i]); $ln += (' ' + $val.PadRight($widths[$i]) + ' ') }
    $ln = $ln.TrimEnd()
    $pad2 = [Math]::Max(0, $innerW - $ln.Length)
    Write-ColorHost ($b.V + $ln + (' ' * $pad2) + $b.V) $script:Colors.Info
  }
  Write-ColorHost ($b.BL + ($b.H * $innerW) + $b.BR) $script:Colors.Info
}

function Prompt-Input {
  param([string]$Label,[scriptblock]$Validate)
  while ($true) {
    $in = Read-Host $Label
    if (-not $Validate) { return $in }
    try { $ok = & $Validate $in } catch { $ok = $false }
    if ($ok) { return $in }
    Write-ColorHost 'Invalid input' $script:Colors.Warning
  }
}

function Show-Header([string]$Title,[string]$LogFile,[string]$SessionStamp,[bool]$IsAdmin=$false) {
  Clear-Host
  Write-Title $Title
  foreach ($l in (Get-AsciiLogo)) { Write-ColorHost (Center-Text $l) $script:Colors.Accent }
  Write-Separator
  $adminBadge = if ($IsAdmin) { 'ADMIN' } else { 'STANDARD' }
  Write-Status Info "Session: $SessionStamp   [$adminBadge]"
  Write-Status Info "Log: $LogFile"
  Write-Separator
}

Export-ModuleMember -Function Initialize-Theme, Write-ColorHost, Center-Text, Write-Separator, Write-Title, Write-Status, Format-MenuItem, Write-Command, Write-HighlightedLine, Write-Panel, Show-Header, Set-ThemePreset, Show-StatusBar, Start-Spinner, Write-Table, Prompt-Input
