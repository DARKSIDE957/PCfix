import argparse
import os
from modules import core

def main():
    p = argparse.ArgumentParser(description="PCFIX BSOD Analyzer CLI")
    p.add_argument("inputs", nargs="+", help="Dump files or directories to analyze")
    p.add_argument("--timeout", type=int, default=30, help="Per-file timeout (seconds)")
    p.add_argument("--no-open", action="store_true", help="Do not open HTML report")
    p.add_argument("--no-sanitize", action="store_true", help="Do not sanitize report text")
    args = p.parse_args()

    files = []
    for inp in args.inputs:
        if os.path.isdir(inp):
            for root, _, fs in os.walk(inp):
                for f in fs:
                    if f.lower().endswith(".dmp"):
                        files.append(os.path.join(root, f))
        elif os.path.isfile(inp):
            files.append(inp)

    if not files:
        print("No dump files found.")
        return 1

    for f in files:
        print(f"Analyzing: {f}")
        msg = core.analyze_dump_file(f, timeout=args.timeout, open_report=not args.no_open, sanitize=not args.no_sanitize)
        print(msg)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

