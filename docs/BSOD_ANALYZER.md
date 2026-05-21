PCFIX BSOD Analyzer (Advanced)

Overview
- Supports Windows dump formats (minidump, kernel, complete, active, live)
- Uses Microsoft Debugging Tools (cdb/kd) with symbol server integration
- Heuristic engine classifies root cause (driver, memory, storage, hardware) with high confidence
- Generates HTML reports with executive summary, technical details, and trends

Requirements
- Windows 10/11, Server 2016–2022 (x64/ARM64)
- Windows SDK Debugging Tools installed (cdb/kd)

Symbol Configuration
- Local cache: %LOCALAPPDATA%\PCFIX\Symbols
- Symbol path: srv*%LOCALAPPDATA%\PCFIX\Symbols*https://msdl.microsoft.com/download/symbols

Usage (GUI)
- Open PCFIX → BSOD ANALYZER
- ANALYZE DUMP FILE (ADVANCED) to select a .dmp
- REAL‑TIME ANALYZE LATEST DUMP to automatically analyze the most recent dump
- Report auto‑opens after analysis

Usage (CLI)
- python bsod_cli.py <dump or folder> [--timeout 30] [--no-open] [--no-sanitize]

Privacy
- Reports sanitize emails, IPs, domain\\user, and user paths by default

Report Contents
- Executive summary with bugcheck, root cause, confidence, suspects
- Remediation steps (driver links, SFC/DISM, hardware checks)
- Technical section with full debugging output (sanitized)
- Trends from previous ~200 analyses

Performance
- Targets ≤30s for standard 4GB dumps with symbol caching

