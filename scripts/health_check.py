"""Smoke-test PCFIX core APIs and log results for debug session."""
import json
import os
import sys
import time
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from modules import core

LOG_PATH = os.path.join(ROOT, "debug-3a9129.log")
SESSION = "3a9129"
RUN_ID = os.environ.get("PCFIX_RUN_ID", "health-pre")


def _log(hypothesis_id, location, message, data=None):
    # #region agent log
    entry = {
        "sessionId": SESSION,
        "runId": RUN_ID,
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data or {},
        "timestamp": int(time.time() * 1000),
    }
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    # #endregion


def _check(name, fn, hypothesis_id):
    try:
        result = fn()
        ok = result is not False
        _log(hypothesis_id, f"health_check:{name}", "ok", {"result_type": type(result).__name__, "preview": str(result)[:200]})
        return ok, None
    except Exception as e:
        _log(hypothesis_id, f"health_check:{name}", "fail", {"error": str(e), "trace": traceback.format_exc()[-500:]})
        return False, str(e)


def main():
    _log("INIT", "health_check:main", "start", {"cwd": os.getcwd(), "root": ROOT, "admin": core.is_admin()})

    checks = [
        ("get_system_status", lambda: core.get_system_status(), "H-stats"),
        ("get_detailed_info", lambda: core.get_detailed_info(), "H-stats"),
        ("load_config", lambda: core.load_config(), "H-config"),
        ("get_bsod_history", lambda: core.get_bsod_history(), "H-bsod"),
        ("get_bsod_insight", lambda: core.get_bsod_insight("0x000000EF"), "H-bsod"),
        ("classify_root_cause", lambda: core.classify_root_cause("0x00000050", None, "", ""), "H-bsod"),
        ("get_startup_apps", lambda: core.get_startup_apps(), "H-startup"),
        ("get_network_info", lambda: core.get_network_info(), "H-network"),
        ("get_installed_bloatware", lambda: core.get_installed_bloatware(), "H-debloat"),
        ("find_application_artifacts", lambda: core.find_application_artifacts("notepad", include_processes=False, max_results=5), "H-force"),
        ("kill_process_alias", lambda: hasattr(core, "kill_process"), "H-kill"),
        ("flush_dns", lambda: core.flush_dns(), "H-dns"),
    ]

    failed = []
    for name, fn, hid in checks:
        ok, err = _check(name, fn, hid)
        if not ok:
            failed.append((name, err))

    # H-ui: verify main entry defaults to full tkinter UI
    try:
        import inspect
        import main as main_mod
        deb_src = inspect.getsource(main_mod.App.show_debloater)
        stub = deb_src.strip() == "pass" or (deb_src.count("\n") <= 3 and "pass" in deb_src)
        tail = open(os.path.join(ROOT, "main.py"), encoding="utf-8").read().split("if __name__")[-1]
        default_tk = "use_webview" in tail and "App()" in tail and "app.mainloop()" in tail
        _log("H-ui", "health_check:ui", "main_entry", {"default_tkinter": default_tk, "debloater_stub": stub})
    except Exception as e:
        _log("H-ui", "health_check:ui", "fail", {"error": str(e)})

    _log("SUMMARY", "health_check:main", "done", {"failed": [f[0] for f in failed], "fail_count": len(failed)})
    print(f"Health check complete. Failed: {len(failed)}")
    for n, e in failed:
        print(f"  - {n}: {e}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
