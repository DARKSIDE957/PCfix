API Reference: BSOD Analyzer

Python (modules.core)
- analyze_dump_file(dump_path, timeout=30, open_report=True, sanitize=True) -> str
  - Runs cdb/kd on the dump, generates an HTML report, returns status string with path.
- analyze_latest_dump_realtime(timeout=30) -> str
  - Finds the latest dump in %SystemRoot%\Minidump or MEMORY.DMP and analyzes it.
- classify_root_cause(bugcheck_code, probable_driver=None, stacks_text=\"\", modules_text=\"\") -> dict
  - Runs the heuristic classifier on provided signals; returns {category, confidence, suspects, hardware}.

CLI (bsod_cli.py)
- python bsod_cli.py <dump | folder> [--timeout N] [--no-open] [--no-sanitize]

Return Categories
- driver, memory, storage, hardware, unknown

Data Paths
- Reports: %LOCALAPPDATA%\PCFIX\reports
- Symbol cache: %LOCALAPPDATA%\PCFIX\Symbols
- History: %LOCALAPPDATA%\PCFIX\bsod_history.json

