# Changelog

All notable changes to this project are documented here.

## [1.0.0] - 2025-11-01
- Modular rewrite: `src/VNPCfix` PowerShell module with manifest
- Core: centralized state, logging, and JSON config support
- UI: color-aware writer, theme initialization, ASCII fallback, centered logo
- Diagnostics: system info and recent critical events panels
- Repairs: SFC, DISM, CHKDSK with `SupportsShouldProcess` and logging
- Entry script refactor to import module and drive the UI
- Documentation: README, CHANGELOG, SECURITY guidance
- Tests: initial Pester unit tests for core and UI behaviors