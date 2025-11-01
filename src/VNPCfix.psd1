@{
  RootModule        = 'VNPCfix.psm1'
  ModuleVersion     = '1.0.0'
  GUID              = '1d5b63ab-bc7e-4f50-9553-3cf7d2f7f888'
  Author            = 'VN PCfix Team'
  CompanyName       = 'VN PCfix'
  Copyright         = '(c) 2025 VN PCfix'
  Description       = 'VN PCfix: Windows Troubleshooting & Repair toolkit with modular structure, theming, diagnostics, and safe repairs.'
  PowerShellVersion = '5.1'
  CompatiblePSEditions = @('Desktop','Core')
  FunctionsToExport = @(
    'Start-VNPCfix',
    'Set-VNPCfixOptions',
    'Write-Log',
    'Invoke-VNPCfixDiagnostics',
    'Invoke-VNPCfixSfcRepair',
    'Invoke-VNPCfixDismRepair',
    'Invoke-VNPCfixChkdskScan',
    'Invoke-VNPCfixChkdskFix'
  )
  NestedModules     = @(
    'VNPCfix.Core.psm1',
    'VNPCfix.UI.psm1',
    'VNPCfix.Security.psm1',
    'VNPCfix.Diagnostics.psm1',
    'VNPCfix.Repairs.psm1'
  )
  PrivateData       = @{
    PSData = @{
      Tags       = @('Windows','Diagnostics','Repair','SFC','DISM','CHKDSK','UI','Pester')
      ReleaseNotes = 'Initial modular release with docs, tests, and improved UI.'
    }
  }
}