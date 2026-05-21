Migration Guide: BSOD Analyzer Upgrade

Scope
- Previous BSOD analyzer used Event Log summaries only.
- New analyzer integrates cdb/kd for full dump parsing and reports.

What Changed
- UI: Added buttons for Advanced Dump Analysis and Real‑Time Latest Dump.
- Core: New functions (analyze_dump_file, analyze_latest_dump_realtime, classify_root_cause).
- Reports: HTML report generation with symbol‑driven insights and trends.
- CLI: New bsod_cli.py for batch/PowerShell usage.

Actions for Existing Users
- Install Windows SDK Debugging Tools (cdb/kd) if not present.
- Symbol cache builds on first run; subsequent analyses are faster.
- Optional: review %LOCALAPPDATA%\PCFIX\bsod_history.json for trends.

Compatibility
- Works on Windows 10/11 and Server 2016–2022 (x64/ARM64).
- Falls back with guidance if cdb/kd is not found.

