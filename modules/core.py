import subprocess
import ctypes
import sys
import os
import psutil
import shutil
import glob
import platform
import datetime
import winreg
import socket
import re
import time
import json
import winsound
import threading
import concurrent.futures

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def elevate():
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()

def run_command(cmd, shell=True):
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        result = subprocess.run(cmd, capture_output=True, text=True, shell=shell, startupinfo=startupinfo)
        return result.stdout.strip()
    except Exception as e:
        return str(e)

def run_powershell(cmd):
    return run_command(f'powershell -Command "{cmd}"')

# --- SYSTEM MONITORING ---

def get_system_status():
    try:
        # interval=None is non-blocking (returns immediately)
        # First call returns 0.0, subsequent calls return avg since last call
        cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage('C:\\').percent
        
        status = {"cpu": cpu, "ram": ram, "disk": disk}
        
        # Battery Check (Laptop Compatibility)
        try:
            battery = psutil.sensors_battery()
            if battery:
                status["battery"] = battery.percent
                status["plugged"] = battery.power_plugged
        except:
            pass
            
        return status
    except:
        return {"cpu": 0, "ram": 0, "disk": 0}

def get_detailed_info():
    try:
        # GPU (Registry Method - Most Reliable)
        gpu = "N/A"
        try:
            gpus = []
            # Class GUID for Display Adapters
            guid = "{4d36e968-e325-11ce-bfc1-08002be10318}"
            base_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, fr"SYSTEM\CurrentControlSet\Control\Class\{guid}")
            
            i = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(base_key, i)
                    subkey = winreg.OpenKey(base_key, subkey_name)
                    try:
                        # DriverDesc is the user-friendly name
                        name = winreg.QueryValueEx(subkey, "DriverDesc")[0]
                        if name:
                            gpus.append(name)
                    except:
                        pass
                    winreg.CloseKey(subkey)
                    i += 1
                except OSError:
                    break
            winreg.CloseKey(base_key)
            
            if gpus:
                gpu = " | ".join(gpus)
        except:
            # Fallback to PowerShell if Registry fails
            try:
                r = run_powershell("Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name")
                lines = [l.strip() for l in r.split("\n") if l.strip()]
                if lines:
                    gpu = " | ".join(lines)
            except:
                pass

        # OS
        os_info = "Unknown"
        try:
            # Try to get detailed build info from Registry
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
            product_name = winreg.QueryValueEx(key, "ProductName")[0]
            display_version = winreg.QueryValueEx(key, "DisplayVersion")[0]
            current_build = winreg.QueryValueEx(key, "CurrentBuild")[0]
            try:
                ubr = winreg.QueryValueEx(key, "UBR")[0]
                current_build = f"{current_build}.{ubr}"
            except:
                pass
            winreg.CloseKey(key)

            # Fix Windows 11 Detection (Build >= 22000)
            if "Windows 10" in product_name:
                try:
                    build_num = int(current_build.split('.')[0])
                    if build_num >= 22000:
                        product_name = product_name.replace("Windows 10", "Windows 11")
                except:
                    pass

            os_info = f"{product_name} {display_version} (Build {current_build})"
        except:
            # Fallback
            os_info = f"{platform.system()} {platform.release()} ({platform.version()})"

        # Uptime
        uptime = "N/A"
        try:
            delta = datetime.datetime.now() - datetime.datetime.fromtimestamp(psutil.boot_time())
            uptime = str(delta).split('.')[0]
        except:
            pass

        # CPU (Registry Method)
        cpu_name = platform.processor()
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
            cpu_name = winreg.QueryValueEx(key, "ProcessorNameString")[0]
            winreg.CloseKey(key)
        except:
            pass

        info = {
            "os": os_info,
            "cpu": cpu_name,
            "gpu": gpu,
            "ram": f"{round(psutil.virtual_memory().total / (1024**3), 2)} GB",
            "uptime": uptime,
            # Extras for export
            "Architecture": platform.machine(),
            "Disk Total": f"{round(psutil.disk_usage('C:').total / (1024**3), 2)} GB"
        }
        
        try:
            bat = psutil.sensors_battery()
            if bat:
                info["battery"] = f"{bat.percent}% ({'Plugged In' if bat.power_plugged else 'On Battery'})"
        except:
            pass

        return info
    except:
        return {}

# --- OPTIMIZATION TOOLS ---

def flush_dns():
    return run_command("ipconfig /flushdns")

def clean_temp_files():
    temp_folders = [
        os.environ.get('TEMP'),
        os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Temp')
    ]
    deleted_size = 0
    count = 0
    
    for folder in temp_folders:
        if folder and os.path.exists(folder):
            for root, dirs, files in os.walk(folder):
                for f in files:
                    try:
                        file_path = os.path.join(root, f)
                        size = os.path.getsize(file_path)
                        os.remove(file_path)
                        deleted_size += size
                        count += 1
                    except:
                        pass
                for d in dirs:
                    try:
                        shutil.rmtree(os.path.join(root, d))
                    except:
                        pass
                        
    mb = round(deleted_size / (1024 * 1024), 2)
    return f"Cleaned {count} files ({mb} MB)"

def optimize_ram():
    try:
        psapi = ctypes.windll.psapi
        kernel32 = ctypes.windll.kernel32
        for proc in psutil.process_iter():
            try:
                handle = kernel32.OpenProcess(0x001F0FFF, False, proc.pid)
                if handle:
                    psapi.EmptyWorkingSet(handle)
                    kernel32.CloseHandle(handle)
            except:
                pass
        return "RAM Optimized: Working sets emptied."
    except Exception as e:
        return f"RAM Error: {e}"

def optimize_visual_fx():
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects"
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
        winreg.SetValueEx(key, "VisualFXSetting", 0, winreg.REG_DWORD, 2)
        winreg.CloseKey(key)
        return "Visual FX: Set to Performance Mode."
    except Exception as e:
        return f"Visual FX Error: {e}"

def reset_visual_fx():
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects"
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
        winreg.SetValueEx(key, "VisualFXSetting", 0, winreg.REG_DWORD, 0)
        winreg.CloseKey(key)
        return "Visual FX: Reset."
    except Exception as e:
        return f"Visual FX Error: {e}"

def empty_recycle_bin():
    try:
        # SHERB_NOCONFIRMATION = 0x00000001
        # SHERB_NOPROGRESSUI = 0x00000002
        # SHERB_NOSOUND = 0x00000004
        ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 7)
        return "Recycle Bin Emptied."
    except:
        return "Recycle Bin Empty or Error."

def kill_process_by_name(name):
    count = 0
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] and name.lower() in proc.info['name'].lower():
            try:
                p = psutil.Process(proc.info['pid'])
                p.terminate()
                count += 1
            except:
                pass
    return f"Terminated {count} processes matching '{name}'"

kill_process = kill_process_by_name

# --- REPAIR TOOLS ---

def run_sfc():
    return run_command("sfc /scannow")

def run_dism():
    return run_command("DISM /Online /Cleanup-Image /RestoreHealth")

def check_disk_schedule():
    return run_command("echo y | chkdsk /f /r")

def reset_network():
    log = []
    log.append(run_command("netsh winsock reset"))
    log.append(run_command("netsh int ip reset"))
    log.append(run_command("ipconfig /release"))
    log.append(run_command("ipconfig /renew"))
    log.append(run_command("ipconfig /flushdns"))
    return "\n".join(log)

def get_bsod_history():
    crashes = []
    try:
        cmd = "Get-EventLog -LogName System -EventId 1001 -Newest 5 | Format-List TimeGenerated, Message"
        res = run_powershell(cmd)
        
        if not res or "No matches found" in res:
            return []

        raw_entries = res.split("TimeGenerated :")
        
        for entry in raw_entries:
            if not entry.strip():
                continue
                
            lines = entry.strip().split("\n")
            time_val = lines[0].strip()
            
            # Find message
            message_val = "Unknown Error"
            for line in lines:
                if line.strip().startswith("Message :"):
                    message_val = line.replace("Message :", "").strip()
                    break
            
            code_val = "CRITICAL"
            match = re.search(r'0x[0-9A-Fa-f]{8}', message_val)
            if match:
                code_val = match.group(0)
            
            crashes.append({
                "time": time_val,
                "code": code_val,
                "message": message_val
            })
            
        return crashes
    except Exception:
        return []

def _normalize_bugcheck_code(code):
    try:
        if not code:
            return None
        code = code.strip()
        if not code.lower().startswith("0x"):
            return None
        value = int(code, 16)
        return "0x%08X" % value
    except Exception:
        return None

_BSOD_KB = {
    "0x000000EF": {
        "name": "CRITICAL_PROCESS_DIED",
        "summary": "A critical Windows process unexpectedly exited.",
        "actions": [
            "Remove or roll back recently installed drivers or software.",
            "Run SFC and DISM to repair system files.",
            "Scan for malware and verify disk health."
        ]
    },
    "0x0000009F": {
        "name": "DRIVER_POWER_STATE_FAILURE",
        "summary": "A driver did not handle power state transitions correctly.",
        "actions": [
            "Update chipset, storage, and GPU drivers to the latest versions.",
            "Disable or remove problematic USB and external devices.",
            "Check advanced power settings for aggressive sleep states."
        ]
    },
    "0x0000007E": {
        "name": "SYSTEM_THREAD_EXCEPTION_NOT_HANDLED",
        "summary": "A system thread generated an exception that was not caught.",
        "actions": [
            "Update display and storage drivers.",
            "Remove overclocking or unstable tuning utilities.",
            "Inspect recent changes in antivirus or low-level tools."
        ]
    },
    "0x0000003B": {
        "name": "SYSTEM_SERVICE_EXCEPTION",
        "summary": "An exception occurred while executing a system service.",
        "actions": [
            "Update graphics and chipset drivers.",
            "Run SFC and DISM to verify system integrity.",
            "Review recently installed system utilities or overlays."
        ]
    },
    "0x000000D1": {
        "name": "DRIVER_IRQL_NOT_LESS_OR_EQUAL",
        "summary": "A driver accessed invalid memory at an improper IRQL.",
        "actions": [
            "Update or roll back network and storage drivers.",
            "Remove unstable overclocking or monitoring tools.",
            "Run memory diagnostics to rule out faulty RAM."
        ]
    },
    "0x0000007F": {
        "name": "UNEXPECTED_KERNEL_MODE_TRAP",
        "summary": "The CPU generated a trap the kernel failed to catch.",
        "actions": [
            "Check CPU and RAM stability; remove overclocks.",
            "Verify proper cooling and clean dust from hardware.",
            "Run extended memory and CPU stress tests."
        ]
    },
    "0x00000050": {
        "name": "PAGE_FAULT_IN_NONPAGED_AREA",
        "summary": "The system referenced invalid memory in nonpaged area.",
        "actions": [
            "Run memory diagnostics to test RAM.",
            "Check storage and filesystem health with CHKDSK.",
            "Remove recently added drivers or antivirus software."
        ]
    },
    "0x00000124": {
        "name": "WHEA_UNCORRECTABLE_ERROR",
        "summary": "A fatal hardware error was reported by the CPU or chipset.",
        "actions": [
            "Return CPU, RAM, and GPU to stock frequencies.",
            "Monitor temperatures and ensure adequate cooling.",
            "Update BIOS and chipset firmware; test hardware components."
        ]
    }
}

def get_bsod_insight(code):
    normalized = _normalize_bugcheck_code(code)
    if normalized and normalized in _BSOD_KB:
        data = _BSOD_KB[normalized].copy()
        data["code"] = normalized
        return data
    generic_actions = [
        "Install all pending Windows Updates.",
        "Update graphics, storage, and chipset drivers.",
        "Run SFC, DISM, and CHKDSK to repair system files and disks.",
        "Check hardware temperatures and remove any overclocking."
    ]
    return {
        "code": code or "UNKNOWN",
        "name": "Unknown BugCheck",
        "summary": "Windows reported a stop error that does not match known patterns.",
        "actions": generic_actions
    }

def open_minidump_folder():
    try:
        system_root = os.environ.get("SystemRoot", "C:\\Windows")
        minidump_dir = os.path.join(system_root, "Minidump")
        if os.path.isdir(minidump_dir):
            os.startfile(minidump_dir)
            return "Opened minidump folder."
        memory_dump = os.path.join(system_root, "MEMORY.DMP")
        if os.path.exists(memory_dump):
            os.startfile(os.path.dirname(memory_dump))
            return "Opened memory dump location."
        return "No dump files detected."
    except Exception as e:
        return f"Error: {e}"

def export_bsod_report():
    try:
        crashes = get_bsod_history()
        desktop = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")
        if not desktop:
            return "Desktop path not found."
        if not os.path.isdir(desktop):
            return "Desktop path is invalid."
        path = os.path.join(desktop, "pcfix_bsod_report.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("PCFIX BSOD REPORT\n")
            f.write("=================\n\n")
            if not crashes:
                f.write("No recent BugCheck events were found in the System log.\n")
            for crash in crashes:
                code = crash.get("code")
                insight = get_bsod_insight(code)
                f.write(f"Time: {crash.get('time', 'Unknown')}\n")
                f.write(f"Code: {insight.get('code', code)}\n")
                f.write(f"Name: {insight.get('name', 'Unknown')}\n")
                summary = insight.get("summary", "")
                if summary:
                    f.write(f"Summary: {summary}\n")
                message = crash.get("message", "")
                if message:
                    f.write("Raw Event Message:\n")
                    f.write(message)
                    f.write("\n")
                actions = insight.get("actions", [])
                if actions:
                    f.write("Recommended actions:\n")
                    for step in actions:
                        f.write(f"- {step}\n")
                f.write("\n" + "-" * 40 + "\n\n")
        os.startfile(path)
        return "BSOD report exported to Desktop."
    except Exception as e:
        return f"Error: {e}"

# --- ADVANCED BSOD ANALYZER (CDB/KD INTEGRATION) ---

_VENDOR_LINKS = {
    "nvlddmkm.sys": "https://www.nvidia.com/Download/index.aspx",
    "nvidia": "https://www.nvidia.com/Download/index.aspx",
    "atikmdag.sys": "https://www.amd.com/en/support",
    "amdkmdag.sys": "https://www.amd.com/en/support",
    "amd": "https://www.amd.com/en/support",
    "igdkmd": "https://www.intel.com/content/www/us/en/download-center/home.html",
    "intel": "https://www.intel.com/content/www/us/en/download-center/home.html",
    "rtwl": "https://www.realtek.com/en/component/zoo/category/network-interface-controllers-10-100-1000m-gigabit-ethernet-usb-3-0-software",
    "realtek": "https://www.realtek.com/en/",
    "killer": "https://www.intel.com/content/www/us/en/products/docs/wireless.html",
    "bcm": "https://www.broadcom.com/support",
    "storport": "https://support.microsoft.com/",
    "iastor": "https://www.intel.com/content/www/us/en/download-center/home.html",
}

def _pcfix_data_dir():
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    path = os.path.join(base, "PCFIX")
    os.makedirs(path, exist_ok=True)
    return path

def _symbol_cache_dir():
    path = os.path.join(_pcfix_data_dir(), "Symbols")
    os.makedirs(path, exist_ok=True)
    return path

def _find_debugger():
    # Try common Windows Kits Debuggers paths
    program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    program_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    arch = platform.machine().lower()
    candidates = []
    # Prefer cdb.exe (user-mode), kd.exe for kernel; both can open dumps
    subdirs = []
    if "arm" in arch:
        subdirs = ["arm64"]
    else:
        subdirs = ["x64", "amd64", "x86"]
    for base in (program_files, program_files_x86):
        for sd in subdirs:
            candidates.append(os.path.join(base, "Windows Kits", "10", "Debuggers", sd, "cdb.exe"))
            candidates.append(os.path.join(base, "Windows Kits", "10", "Debuggers", sd, "kd.exe"))
    for c in candidates:
        if os.path.exists(c):
            return c
    # Fallback to PATH
    for name in ("cdb.exe", "kd.exe"):
        p = shutil.which(name)
        if p:
            return p
    return None

def _symbol_path():
    cache = _symbol_cache_dir()
    return f"srv*{cache}*https://msdl.microsoft.com/download/symbols"

def _run_debugger(dump_path, timeout=30):
    dbg = _find_debugger()
    if not dbg:
        return {"error": "Windows Debugging Tools (cdb/kd) not found. Install Windows SDK Debugging Tools."}
    cmds = "; ".join([
        ".symfix",
        f".sympath+ {_symbol_path()}",
        ".reload",
        ".echo __PCFIX_BEGIN__",
        "!analyze -v",
        ".echo __PCFIX_SPLIT__",
        "~* kP",
        ".echo __PCFIX_SPLIT2__",
        "lmv",
        ".echo __PCFIX_END__",
        "q"
    ])
    env = os.environ.copy()
    env["_NT_SYMBOL_PATH"] = _symbol_path()
    try:
        # cdb/kd accepts: -z <dump> -c "<commands>"
        p = subprocess.run(
            [dbg, "-z", dump_path, "-c", cmds],
            capture_output=True, text=True, timeout=timeout, env=env, creationflags=subprocess.CREATE_NO_WINDOW
        )
        output = (p.stdout or "") + "\n" + (p.stderr or "")
        return {"output": output, "returncode": p.returncode, "debugger": dbg}
    except subprocess.TimeoutExpired:
        return {"error": f"Analysis timed out after {timeout}s", "timeout": True}
    except Exception as e:
        return {"error": str(e)}

def _parse_bugcheck(an_text):
    code = None
    params = []
    probably = None
    # BugCheck <hex> (args...)
    m = re.search(r"BugCheck\s+([0-9A-Fa-fx]+)", an_text)
    if m:
        code = _normalize_bugcheck_code(m.group(1))
    # Probably caused by : <driver>
    m2 = re.search(r"Probably caused by\s*:\s*([^\s]+)", an_text)
    if m2:
        probably = m2.group(1).strip()
    # Arguments:
    args_block = re.search(r"Arguments:\s*(.+?)(?:\n\n|\Z)", an_text, flags=re.S)
    if args_block:
        for line in args_block.group(1).splitlines():
            m3 = re.search(r"Arg\d+:\s*([0-9A-Fa-f`x]+)", line)
            if m3:
                params.append(m3.group(1))
    return code, params, probably

def _list_suspect_drivers(lm_text):
    suspects = []
    for line in lm_text.splitlines():
        # module name lines often look like: "Image path: \SystemRoot\system32\drivers\xyz.sys"
        m = re.search(r"^\s*Image path:\s*(.+)$", line)
        if m:
            path = m.group(1).strip()
            name = os.path.basename(path).lower()
            # Filter third-party hints: not Microsoft default if possible
            if name.endswith(".sys"):
                suspects.append({"name": name, "path": path})
        else:
            # fall back: grab module names of the form "Loaded symbol image file: xxxx.sys"
            m2 = re.search(r"Loaded symbol image file:\s*([^\s]+\.sys)", line, re.I)
            if m2:
                name = os.path.basename(m2.group(1)).lower()
                suspects.append({"name": name, "path": m2.group(1)})
    # Deduplicate preserving order
    seen = set()
    uniq = []
    for s in suspects:
        n = s["name"]
        if n not in seen:
            seen.add(n)
            uniq.append(s)
    return uniq

def _detect_hardware_signatures(text):
    signs = []
    patterns = [
        ("WHEA", r"\bWHEA\b|\bMACHINE CHECK\b|\bBUSL0\b|\bCACHE HIERARCHY\b"),
        ("MEMORY_CORRUPTION", r"\bmemory[_ ]corruption\b|\bpool[_ ]corruption\b|\bnt!ExFreePool\b"),
        ("DISK_IO", r"\bNTFS\b|\bvolsnap\b|\bstorport\b|\biaStor\b"),
        ("GPU_HANG", r"\bVIDEO_TDR_FAILURE\b|\bTDR\b|\bnvlddmkm\b|\batikmdag\b|\bamdkmdag\b"),
        ("NETWORK", r"\bndis\b|\bnetio\b|\bwin32kfull\b"),
    ]
    for tag, rx in patterns:
        if re.search(rx, text, re.I):
            signs.append(tag)
    return signs

def _heuristics(code, params, probably, stacks_text, lm_text):
    # Base categories
    cause = "unknown"
    confidence = 0.5
    suspects = _list_suspect_drivers(lm_text)
    hw = _detect_hardware_signatures(stacks_text + "\n" + lm_text)

    if code in ("0x00000124", "0x0000009C"):  # WHEA
        cause, confidence = "hardware", 0.98
    elif code in ("0x00000050", "0x0000001A", "0x0000000A", "0x0000007E"):
        cause, confidence = "memory", 0.9
    elif code in ("0x0000009F", "0x000000D1", "0x0000003B", "0x0000007F", "0x000000FE"):
        cause, confidence = "driver", 0.9
    elif code in ("0x000000F4", "0x0000007A"):
        cause, confidence = "storage", 0.88

    # Adjust by 'Probably caused by'
    if probably and probably.lower().endswith(".sys"):
        cause = "driver"
        confidence = max(confidence, 0.93)
        # Promote probable driver to top
        suspects = [{"name": probably.lower(), "path": probably}] + [s for s in suspects if s["name"] != probably.lower()]

    # Hardware signatures boost
    if "WHEA" in hw:
        cause, confidence = "hardware", max(confidence, 0.96)
    if "MEMORY_CORRUPTION" in hw and cause != "hardware":
        cause, confidence = "memory", max(confidence, 0.92)

    return cause, confidence, suspects, hw

def _driver_link(name):
    n = name.lower()
    for key, url in _VENDOR_LINKS.items():
        if key in n:
            return url
    # Default to generic Microsoft update catalog
    return "https://www.catalog.update.microsoft.com/"

def _sanitize(text):
    if not text:
        return text
    # Replace emails
    text = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[redacted-email]", text)
    # Replace IPv4
    text = re.sub(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "[redacted-ipv4]", text)
    # Replace IPv6 (simplified)
    text = re.sub(r"\b([0-9A-Fa-f]{0,4}:){2,7}[0-9A-Fa-f]{0,4}\b", "[redacted-ipv6]", text)
    # Replace domain\username
    text = re.sub(r"\b[\w\.-]+\\[\w\.-]+\b", r"[redacted-user]", text)
    # Replace C:\Users\Name paths
    text = re.sub(r"[A-Za-z]:\\Users\\[^\\\s]+", r"[USERPROFILE]", text, flags=re.I)
    return text

def _save_bsod_analysis(entry):
    path = os.path.join(_pcfix_data_dir(), "bsod_history.json")
    try:
        data = []
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        data.append(entry)
        # keep last 200
        data = data[-200:]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except:
        pass

def _load_bsod_analysis():
    path = os.path.join(_pcfix_data_dir(), "bsod_history.json")
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return []

def _trending():
    hist = _load_bsod_analysis()
    trends = {"by_code": {}, "by_driver": {}}
    for h in hist:
        code = h.get("bugcheck", {}).get("code")
        if code:
            trends["by_code"][code] = trends["by_code"].get(code, 0) + 1
        for d in h.get("suspects", []):
            n = d.get("name")
            if n:
                trends["by_driver"][n] = trends["by_driver"].get(n, 0) + 1
    return trends

def analyze_dump_file(dump_path, timeout=30, open_report=True, sanitize=True):
    start = time.time()
    res = _run_debugger(dump_path, timeout=timeout)
    end = time.time()
    if "error" in res:
        return res["error"]
    out = res.get("output", "")
    # Split sections
    parts = out.split("__PCFIX_BEGIN__")
    if len(parts) < 2:
        return "Failed to parse debugger output."
    body = parts[1]
    segs = body.split("__PCFIX_SPLIT__")
    analyze_v = segs[0] if segs else body
    segs2 = body.split("__PCFIX_SPLIT2__")
    stacks = segs2[1].split("__PCFIX_END__")[0] if len(segs2) > 1 else ""
    lm = segs2[2].split("__PCFIX_END__")[0] if len(segs2) > 2 else ""

    code, params, probably = _parse_bugcheck(analyze_v)
    cause, conf, suspects, hw = _heuristics(code, params, probably, stacks, lm)

    remediation = []
    if cause == "driver" and suspects:
        top = suspects[0]["name"]
        remediation.append(f"Update or roll back driver: {top} → {_driver_link(top)}")
    if cause in ("memory", "hardware"):
        remediation.append("Run extended memory test: mdsched.exe or MemTest86 (bootable).")
    if cause in ("storage", "hardware"):
        remediation.append("Check SMART and run: chkdsk /f /r, verify cables, update storage drivers/BIOS.")
    remediation.extend([
        "Run: sfc /scannow",
        "Run: DISM /Online /Cleanup-Image /RestoreHealth",
        "Ensure Windows Update is current."
    ])

    raw = out
    if sanitize:
        raw = _sanitize(raw)

    analysis = {
        "file": dump_path,
        "duration_sec": round(end - start, 2),
        "bugcheck": {"code": code, "params": params, "probably": probably},
        "root_cause": {"category": cause, "confidence": round(conf, 2)},
        "suspects": suspects,
        "hardware_signatures": hw,
        "remediation": remediation,
        "debugger": res.get("debugger"),
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }
    _save_bsod_analysis(analysis)
    report_path = _generate_bsod_html(analysis, raw, _trending())
    if open_report and os.path.exists(report_path):
        try:
            os.startfile(report_path)
        except:
            pass
    return f"Analysis complete: {report_path}"

def _generate_bsod_html(analysis, raw_text, trends):
    # Simple executive summary + technical detail report
    dest_dir = os.path.join(_pcfix_data_dir(), "reports")
    os.makedirs(dest_dir, exist_ok=True)
    ts = int(time.time())
    name = f"bsod_report_{ts}.html"
    path = os.path.join(dest_dir, name)
    def esc(s):
        return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    code = analysis["bugcheck"]["code"] or "UNKNOWN"
    cause = analysis["root_cause"]["category"]
    conf = analysis["root_cause"]["confidence"]
    dur = analysis["duration_sec"]
    suspects = analysis.get("suspects", [])
    suspect_list = "".join([f"<li>{esc(s['name'])}</li>" for s in suspects[:10]])
    # Trends
    t_code = "".join([f"<li>{esc(k)} &times; {v}</li>" for k, v in sorted(trends.get('by_code', {}).items(), key=lambda x: -x[1])[:8]])
    t_drv = "".join([f"<li>{esc(k)} &times; {v}</li>" for k, v in sorted(trends.get('by_driver', {}).items(), key=lambda x: -x[1])[:8]])
    html = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8"/>
<title>PCFIX BSOD Report</title>
<style>
body {{ background:#0b0b0f; color:#e5e7eb; font-family:Segoe UI, Arial, sans-serif; margin:24px; }}
.card {{ background:#14151a; border:1px solid #27272a; border-radius:10px; padding:16px; margin-bottom:16px; }}
.accent {{ color:#ef4444; }}
code, pre {{ font-family:Consolas, monospace; font-size:12px; color:#e5e7eb; }}
.grid {{ display:grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap:16px; }}
a {{ color:#ef4444; text-decoration:none; }}
</style>
</head>
<body>
<h2 class="accent">PCFIX | BSOD Analysis</h2>
<div class="card">
  <h3>Executive Summary</h3>
  <p><strong>BugCheck:</strong> {esc(code)} | <strong>Root Cause:</strong> {esc(cause)} ({conf*100:.0f}% confidence)</p>
  <p><strong>Duration:</strong> {dur}s | <strong>File:</strong> {esc(analysis['file'])}</p>
  <ul>{suspect_list}</ul>
</div>
<div class="grid">
  <div class="card">
    <h3>Recommended Remediation</h3>
    <ul>{''.join([f'<li>{esc(r)}</li>' for r in analysis.get('remediation', [])])}</ul>
  </div>
  <div class="card">
    <h3>Trending (Last Runs)</h3>
    <p><strong>By BugCheck</strong></p>
    <ul>{t_code or '<li>n/a</li>'}</ul>
    <p><strong>By Driver</strong></p>
    <ul>{t_drv or '<li>n/a</li>'}</ul>
  </div>
</div>
<div class="card">
  <h3>Technical Details</h3>
  <pre>{esc(raw_text)}</pre>
  <p style="opacity:.7">Symbols: {esc(analysis.get('debugger') or '')}</p>
</div>
</body></html>"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path

def analyze_latest_dump_realtime(timeout=30):
    # Search common dump locations
    system_root = os.environ.get("SystemRoot", "C:\\Windows")
    paths = []
    minidump_dir = os.path.join(system_root, "Minidump")
    if os.path.isdir(minidump_dir):
        for p in glob.glob(os.path.join(minidump_dir, "*.dmp")):
            paths.append(p)
    mem_dump = os.path.join(system_root, "MEMORY.DMP")
    if os.path.exists(mem_dump):
        paths.append(mem_dump)
    if not paths:
        return "No dump file found in Windows\\Minidump or MEMORY.DMP."
    latest = max(paths, key=lambda p: os.path.getmtime(p))
    return analyze_dump_file(latest, timeout=timeout, open_report=True, sanitize=True)

def classify_root_cause(bugcheck_code, probable_driver=None, stacks_text="", modules_text=""):
    code = _normalize_bugcheck_code(bugcheck_code) or bugcheck_code
    cause, conf, suspects, hw = _heuristics(code, [], probable_driver, stacks_text or "", modules_text or "")
    return {"category": cause, "confidence": round(conf, 2), "suspects": suspects, "hardware": hw}

def disable_fullscreen_optimizations():
    try:
        k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"System\GameConfigStore")
        winreg.SetValueEx(k, "GameDVR_FSEBehaviorMode", 0, winreg.REG_DWORD, 2)
        winreg.CloseKey(k)
        return "Fullscreen optimizations disabled."
    except Exception as e:
        return f"Error: {e}"

# --- FORCE DELETION ---

def _logs_dir():
    p = os.path.join(_pcfix_data_dir(), "logs")
    os.makedirs(p, exist_ok=True)
    return p

def _quarantine_dir():
    p = os.path.join(_pcfix_data_dir(), "Quarantine")
    os.makedirs(p, exist_ok=True)
    return p

def _log_delete(line):
    ts = datetime.datetime.utcnow().strftime("%Y%m%d")
    path = os.path.join(_logs_dir(), f"force_delete_{ts}.log")
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"{datetime.datetime.utcnow().isoformat()}Z {line}\n")
    except:
        pass

def _is_subpath(child, parent):
    try:
        child = os.path.realpath(child)
        parent = os.path.realpath(parent)
        return os.path.commonprefix([child.upper(), parent.upper()]) == parent.upper()
    except:
        return False

def _protected_roots():
    sysname = platform.system().lower()
    if "windows" in sysname:
        roots = [
            os.environ.get("SystemRoot", r"C:\Windows"),
            r"C:\Windows",
            r"C:\Windows\System32",
            r"C:\Program Files\WindowsApps",
            r"C:\Program Files\Common Files",
        ]
        return [r for r in roots if r]
    if "darwin" in sysname or "mac" in sysname:
        return ["/System", "/usr", "/bin", "/sbin", "/Library/Apple"]
    return ["/bin", "/sbin", "/usr", "/lib", "/lib64", "/etc", "/proc", "/sys", "/dev"]

def _is_protected_path(p):
    for root in _protected_roots():
        try:
            if _is_subpath(p, root):
                return True
        except:
            continue
    return False

def _win_clear_attrs(p):
    try:
        FILE_ATTRIBUTE_NORMAL = 0x80
        ctypes.windll.kernel32.SetFileAttributesW(str(p), FILE_ATTRIBUTE_NORMAL)
    except:
        pass

def _try_icacls_takeown(p):
    try:
        if platform.system().lower().startswith("win"):
            run_command(f'takeown /F "{p}" /A /R /D Y')
            run_command(f'icacls "{p}" /grant *S-1-5-32-544:F /T /C')
    except:
        pass

def _mac_unprotect(p):
    try:
        if platform.system().lower().startswith("darwin"):
            subprocess.run(["/usr/bin/xattr", "-rc", p], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["/usr/bin/chflags", "-R", "nouchg", p], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except:
        pass

def _nix_unprotect(p):
    try:
        if platform.system().lower().startswith("linux"):
            try:
                subprocess.run(["chattr", "-i", "-R", p], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except:
                pass
            try:
                os.chmod(p, 0o777)
            except:
                pass
    except:
        pass

def _win_schedule_delete_on_reboot(p):
    try:
        if not platform.system().lower().startswith("win"):
            return False
        MOVEFILE_DELAY_UNTIL_REBOOT = 0x00000004
        MoveFileExW = ctypes.windll.kernel32.MoveFileExW
        MoveFileExW.restype = ctypes.c_int
        res = MoveFileExW(ctypes.c_wchar_p(p), None, MOVEFILE_DELAY_UNTIL_REBOOT)
        return res != 0
    except:
        return False

def _kill_locking_processes(target):
    killed = 0
    for proc in psutil.process_iter(["pid", "name", "exe", "open_files"]):
        try:
            exe = proc.info.get("exe") or ""
            if exe and _is_subpath(exe, target):
                try:
                    psutil.Process(proc.pid).terminate()
                    killed += 1
                    continue
                except:
                    pass
            ofs = []
            try:
                ofs = proc.open_files()
            except:
                ofs = []
            for of in ofs:
                try:
                    if _is_subpath(of.path, target) or of.path == target:
                        try:
                            psutil.Process(proc.pid).terminate()
                            killed += 1
                            break
                        except:
                            pass
                except:
                    pass
        except:
            pass
    return killed

def find_application_artifacts(name, extra_hints=None, include_processes=True, max_results=500):
    hits = set()
    n = (name or "").lower()
    if include_processes:
        for p in psutil.process_iter(["name", "exe"]):
            try:
                pn = (p.info.get("name") or "").lower()
                pe = p.info.get("exe") or ""
                if n and (n in pn or n in pe.lower()):
                    if pe:
                        hits.add(os.path.dirname(pe))
            except:
                pass
    if platform.system().lower().startswith("win"):
        paths = [
            os.environ.get("ProgramFiles"),
            os.environ.get("ProgramFiles(x86)"),
            os.environ.get("ProgramData"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), ""),
            os.path.join(os.environ.get("APPDATA", ""), ""),
        ]
        try:
            for hive,path in [(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
                              (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")]:
                try:
                    k = winreg.OpenKey(hive, path)
                    i = 0
                    while True:
                        try:
                            sub = winreg.EnumKey(k, i)
                            sk = winreg.OpenKey(hive, path + "\\" + sub)
                            disp = ""
                            loc = ""
                            try:
                                disp = (winreg.QueryValueEx(sk, "DisplayName")[0] or "").lower()
                            except:
                                pass
                            try:
                                loc = winreg.QueryValueEx(sk, "InstallLocation")[0] or ""
                            except:
                                pass
                            winreg.CloseKey(sk)
                            if n and n in disp and loc and os.path.isdir(loc):
                                hits.add(loc)
                        except OSError:
                            break
                        i += 1
                except:
                    pass
        except:
            pass
    else:
        paths = ["/Applications", os.path.expanduser("~/Applications"), "/opt", "/usr/local", os.path.expanduser("~/.config"), os.path.expanduser("~/.local/share")]
    if extra_hints:
        for h in extra_hints:
            if h and os.path.exists(h):
                hits.add(h)
    scanned = 0
    results = set()
    for base in paths:
        if not base or not os.path.isdir(base):
            continue
        try:
            for entry in os.scandir(base):
                if scanned >= max_results:
                    break
                scanned += 1
                try:
                    nm = entry.name.lower()
                    if n and n in nm:
                        results.add(entry.path)
                except:
                    pass
        except:
            pass
    return list(hits | results)

def build_deletion_plan(paths):
    uid = str(int(time.time()*1000))
    base = os.path.join(_quarantine_dir(), uid)
    os.makedirs(base, exist_ok=True)
    items = []
    for p in paths:
        try:
            rp = os.path.realpath(p)
            if _is_protected_path(rp):
                continue
            rel = rp.strip("\\/").replace(":", "")
            dest = os.path.join(base, rel.replace(os.sep, "_"))
            items.append({"src": rp, "dst": dest})
        except:
            pass
    manifest = {"id": uid, "created": datetime.datetime.utcnow().isoformat()+"Z", "items": items}
    try:
        with open(os.path.join(base, "manifest.json"), "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
    except:
        pass
    return manifest

def execute_deletion_plan(manifest, auto_confirm=False, aggressive=True, threads=4):
    if not auto_confirm:
        return {"status": "CONFIRMATION_REQUIRED", "id": manifest.get("id"), "count": len(manifest.get("items", []))}
    items = manifest.get("items", [])
    results = {"moved": 0, "deleted": 0, "scheduled": 0, "errors": 0, "id": manifest.get("id")}
    def worker(it):
        src = it["src"]
        dst = it["dst"]
        try:
            if not os.path.exists(src):
                _log_delete(f"skip {src} notfound")
                return "skip"
            if platform.system().lower().startswith("win"):
                _win_clear_attrs(src)
            if aggressive:
                _try_icacls_takeown(src)
                _mac_unprotect(src)
                _nix_unprotect(src)
            try:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
            except:
                pass
            try:
                os.replace(src, dst)
                _log_delete(f"moved {src} -> {dst}")
                return "moved"
            except Exception as e:
                _kill_locking_processes(src)
                try:
                    os.replace(src, dst)
                    _log_delete(f"moved {src} -> {dst}")
                    return "moved"
                except Exception as e2:
                    try:
                        if os.path.isdir(src):
                            shutil.rmtree(src, ignore_errors=False)
                        else:
                            os.remove(src)
                        _log_delete(f"deleted {src}")
                        return "deleted"
                    except Exception as e3:
                        if platform.system().lower().startswith("win"):
                            if _win_schedule_delete_on_reboot(src):
                                _log_delete(f"scheduled {src}")
                                return "scheduled"
                        _log_delete(f"error {src} {str(e3)}")
                        return "error"
        except Exception as e:
            _log_delete(f"error {src} {str(e)}")
            return "error"
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, int(threads))) as ex:
        for res in ex.map(worker, items):
            if res == "moved":
                results["moved"] += 1
            elif res == "deleted":
                results["deleted"] += 1
            elif res == "scheduled":
                results["scheduled"] += 1
            elif res == "error":
                results["errors"] += 1
    try:
        base = os.path.join(_quarantine_dir(), manifest.get("id"))
        with open(os.path.join(base, "result.json"), "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
    except:
        pass
    return results

def restore_quarantine(manifest_id=None):
    base = _quarantine_dir()
    target = None
    if manifest_id:
        target = os.path.join(base, manifest_id)
    else:
        try:
            dirs = sorted([d for d in os.listdir(base)], reverse=True)
            if dirs:
                target = os.path.join(base, dirs[0])
        except:
            pass
    if not target or not os.path.isdir(target):
        return {"status": "ERROR", "message": "not found"}
    try:
        with open(os.path.join(target, "manifest.json"), "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except:
        return {"status": "ERROR", "message": "manifest missing"}
    errors = 0
    restored = 0
    for it in manifest.get("items", []):
        src = it.get("src")
        dst = it.get("dst")
        try:
            if dst and os.path.exists(dst):
                os.makedirs(os.path.dirname(src), exist_ok=True)
                os.replace(dst, src)
                _log_delete(f"restored {dst} -> {src}")
                restored += 1
        except Exception as e:
            _log_delete(f"restore_error {dst} {str(e)}")
            errors += 1
    return {"status": "OK", "restored": restored, "errors": errors, "id": manifest.get("id")}

def confirm_and_delete_app(name, extra_hints=None, threads=4, auto_confirm=False):
    artifacts = find_application_artifacts(name, extra_hints=extra_hints, include_processes=True)
    if not artifacts:
        return {"status": "NOT_FOUND"}
    plan = build_deletion_plan(artifacts)
    res = execute_deletion_plan(plan, auto_confirm=auto_confirm, threads=threads)
    res["plan"] = plan
    return res

def force_delete_file(path):
    try:
        if not path or not os.path.exists(path):
            return "File not found."
        if _is_protected_path(path):
            return "Blocked: protected system path."
        plan = build_deletion_plan([path])
        res = execute_deletion_plan(plan, auto_confirm=True, aggressive=True, threads=1)
        if res.get("deleted") or res.get("moved"):
            return f"Deleted: {path}"
        if res.get("scheduled"):
            return f"Scheduled for deletion on reboot: {path}"
        return f"Deletion result: {json.dumps(res)}"
    except Exception as e:
        return f"Error: {e}"

def enable_fullscreen_optimizations():
    try:
        k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"System\GameConfigStore")
        winreg.SetValueEx(k, "GameDVR_FSEBehaviorMode", 0, winreg.REG_DWORD, 0)
        winreg.CloseKey(k)
        return "Fullscreen optimizations enabled."
    except Exception as e:
        return f"Error: {e}"

def disable_power_throttling():
    try:
        run_command('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Power\\PowerThrottling" /v PowerThrottlingOff /t REG_DWORD /d 1 /f')
        return "Power throttling disabled."
    except Exception as e:
        return f"Error: {e}"

def enable_power_throttling():
    try:
        run_command('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Power\\PowerThrottling" /v PowerThrottlingOff /t REG_DWORD /d 0 /f')
        return "Power throttling enabled."
    except Exception as e:
        return f"Error: {e}"

def enable_classic_context_menu():
    try:
        base = r"Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\InprocServer32"
        k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, base)
        winreg.SetValueEx(k, "", 0, winreg.REG_SZ, "")
        winreg.CloseKey(k)
        return "Classic context menu enabled."
    except Exception as e:
        return f"Error: {e}"

def disable_classic_context_menu():
    try:
        base = r"Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}"
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, base + r"\InprocServer32")
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, base)
        return "Classic context menu disabled."
    except FileNotFoundError:
        return "Classic context menu disabled."
    except Exception as e:
        return f"Error: {e}"

def enable_boot_verbose():
    try:
        run_command('reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" /v VerboseStatus /t REG_DWORD /d 1 /f')
        return "Boot information enabled."
    except Exception as e:
        return f"Error: {e}"

def disable_boot_verbose():
    try:
        run_command('reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" /v VerboseStatus /t REG_DWORD /d 0 /f')
        return "Boot information disabled."
    except Exception as e:
        return f"Error: {e}"

def disable_lso():
    try:
        run_powershell('Get-NetAdapter | ForEach-Object { Disable-NetAdapterLso -Name $_.Name -IPv4 -IPv6 -ErrorAction SilentlyContinue }')
        return "Large Send Offload disabled."
    except Exception as e:
        return f"Error: {e}"

def enable_lso():
    try:
        run_powershell('Get-NetAdapter | ForEach-Object { Enable-NetAdapterLso -Name $_.Name -IPv4 -IPv6 -ErrorAction SilentlyContinue }')
        return "Large Send Offload enabled."
    except Exception as e:
        return f"Error: {e}"

def apply_tcp_optimizations():
    try:
        cmds = [
            "netsh int tcp set global autotuninglevel=normal",
            "netsh int tcp set global ecncapability=disabled",
            "netsh int tcp set global rss=enabled",
            "netsh int tcp set global timestamps=disabled",
            "netsh int tcp set global chimney=disabled"
        ]
        for c in cmds:
            run_command(c)
        return "TCP optimizations applied."
    except Exception as e:
        return f"Error: {e}"

def reset_tcp_optimizations():
    try:
        run_command("netsh int tcp reset")
        return "TCP settings reset."
    except Exception as e:
        return f"Error: {e}"
        
# --- SECURITY & POLICIES ---

def disable_uac():
    try:
        run_command('reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" /v EnableLUA /t REG_DWORD /d 0 /f')
        return "UAC disabled. Reboot required."
    except Exception as e:
        return f"Error: {e}"

def enable_uac():
    try:
        run_command('reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" /v EnableLUA /t REG_DWORD /d 1 /f')
        return "UAC enabled. Reboot required."
    except Exception as e:
        return f"Error: {e}"

def disable_smartscreen():
    try:
        run_command('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\System" /v EnableSmartScreen /t REG_DWORD /d 0 /f')
        return "SmartScreen disabled."
    except Exception as e:
        return f"Error: {e}"

def enable_smartscreen():
    try:
        run_command('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\System" /v EnableSmartScreen /t REG_DWORD /d 1 /f')
        return "SmartScreen enabled."
    except Exception as e:
        return f"Error: {e}"

def block_driver_updates():
    try:
        run_command('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate" /v ExcludeWUDriversInQualityUpdate /t REG_DWORD /d 1 /f')
        return "Windows Update driver delivery blocked."
    except Exception as e:
        return f"Error: {e}"

def allow_driver_updates():
    try:
        run_command('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate" /v ExcludeWUDriversInQualityUpdate /t REG_DWORD /d 0 /f')
        return "Windows Update driver delivery allowed."
    except Exception as e:
        return f"Error: {e}"

def disable_vpn_support():
    try:
        run_command("sc stop RasMan")
        run_command("sc config RasMan start= disabled")
        return "VPN stack disabled."
    except Exception as e:
        return f"Error: {e}"

def enable_vpn_support():
    try:
        run_command("sc config RasMan start= demand")
        return "VPN stack enabled."
    except Exception as e:
        return f"Error: {e}"

def disable_boot_interface():
    try:
        run_command("bcdedit /set quietboot Yes")
        run_command("bcdedit /set bootux disabled")
        return "Windows boot interface disabled."
    except Exception as e:
        return f"Error: {e}"

def enable_boot_interface():
    try:
        run_command("bcdedit /set quietboot No")
        run_command("bcdedit /set bootux enable")
        return "Windows boot interface enabled."
    except Exception as e:
        return f"Error: {e}"

def remove_settings_ads():
    try:
        base = r"Software\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager"
        keys = [
            "SubscribedContent-338389Enabled",
            "SubscribedContent-310093Enabled",
            "SubscribedContent-338388Enabled",
            "SystemPaneSuggestionsEnabled",
            "SilentInstalledAppsEnabled"
        ]
        for k in keys:
            run_command(f'reg add "HKCU\\{base}" /v {k} /t REG_DWORD /d 0 /f')
        return "Settings ads disabled."
    except Exception as e:
        return f"Error: {e}"

def restore_settings_ads():
    try:
        base = r"Software\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager"
        keys = [
            "SubscribedContent-338389Enabled",
            "SubscribedContent-310093Enabled",
            "SubscribedContent-338388Enabled",
            "SystemPaneSuggestionsEnabled",
            "SilentInstalledAppsEnabled"
        ]
        for k in keys:
            run_command(f'reg add "HKCU\\{base}" /v {k} /t REG_DWORD /d 1 /f')
        return "Settings ads restored."
    except Exception as e:
        return f"Error: {e}"

def disable_touch():
    try:
        run_command("sc stop TabletInputService")
        run_command("sc config TabletInputService start= disabled")
        return "Touch services disabled."
    except Exception as e:
        return f"Error: {e}"

def enable_touch():
    try:
        run_command("sc config TabletInputService start= demand")
        return "Touch services enabled."
    except Exception as e:
        return f"Error: {e}"

def disable_cpu_mitigations():
    try:
        run_command('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management" /v FeatureSettingsOverride /t REG_DWORD /d 3 /f')
        run_command('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management" /v FeatureSettingsOverrideMask /t REG_DWORD /d 3 /f')
        return "CPU mitigations disabled. Reboot required."
    except Exception as e:
        return f"Error: {e}"

def enable_cpu_mitigations():
    try:
        run_command('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management" /v FeatureSettingsOverride /t REG_DWORD /d 0 /f')
        run_command('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management" /v FeatureSettingsOverrideMask /t REG_DWORD /d 0 /f')
        return "CPU mitigations enabled. Reboot required."
    except Exception as e:
        return f"Error: {e}"

# --- BROWSER & APP TELEMETRY ---

def disable_edge_telemetry():
    try:
        run_command('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Edge" /v MetricsReportingEnabled /t REG_DWORD /d 0 /f')
        return "Microsoft Edge telemetry disabled."
    except Exception as e:
        return f"Error: {e}"

def enable_edge_telemetry():
    try:
        run_command('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Edge" /v MetricsReportingEnabled /t REG_DWORD /d 1 /f')
        return "Microsoft Edge telemetry enabled."
    except Exception as e:
        return f"Error: {e}"

def disable_firefox_telemetry():
    try:
        run_command('reg add "HKLM\\SOFTWARE\\Policies\\Mozilla\\Firefox" /v DisableTelemetry /t REG_DWORD /d 1 /f')
        return "Firefox telemetry disabled."
    except Exception as e:
        return f"Error: {e}"

def enable_firefox_telemetry():
    try:
        run_command('reg add "HKLM\\SOFTWARE\\Policies\\Mozilla\\Firefox" /v DisableTelemetry /t REG_DWORD /d 0 /f')
        return "Firefox telemetry enabled."
    except Exception as e:
        return f"Error: {e}"

def disable_office_telemetry():
    try:
        run_command('reg add "HKCU\\Software\\Policies\\Microsoft\\office\\16.0\\common\\privacy" /v disallowtelemetry /t REG_DWORD /d 1 /f')
        return "Microsoft Office telemetry disabled."
    except Exception as e:
        return f"Error: {e}"

def enable_office_telemetry():
    try:
        run_command('reg add "HKCU\\Software\\Policies\\Microsoft\\office\\16.0\\common\\privacy" /v disallowtelemetry /t REG_DWORD /d 0 /f')
        return "Microsoft Office telemetry enabled."
    except Exception as e:
        return f"Error: {e}"

def disable_vs_telemetry():
    try:
        run_command('reg add "HKCU\\Software\\Microsoft\\VisualStudio\\Telemetry" /v TurnOffSwitch /t REG_DWORD /d 1 /f')
        return "Visual Studio telemetry disabled."
    except Exception as e:
        return f"Error: {e}"

def enable_vs_telemetry():
    try:
        run_command('reg add "HKCU\\Software\\Microsoft\\VisualStudio\\Telemetry" /v TurnOffSwitch /t REG_DWORD /d 0 /f')
        return "Visual Studio telemetry enabled."
    except Exception as e:
        return f"Error: {e}"

# Chrome telemetry policies
def disable_chrome_telemetry():
    try:
        run_command('reg add "HKLM\\SOFTWARE\\Policies\\Google\\Chrome" /v MetricsReportingEnabled /t REG_DWORD /d 0 /f')
        return "Chrome telemetry disabled."
    except Exception as e:
        return f"Error: {e}"

def enable_chrome_telemetry():
    try:
        run_command('reg add "HKLM\\SOFTWARE\\Policies\\Google\\Chrome" /v MetricsReportingEnabled /t REG_DWORD /d 1 /f')
        return "Chrome telemetry enabled."
    except Exception as e:
        return f"Error: {e}"

# --- EXPLORER UX ---

def optimize_explorer():
    try:
        base = r"Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced"
        run_command(f'reg add "HKCU\\{base}" /v SeparateProcess /t REG_DWORD /d 1 /f')
        run_command(f'reg add "HKCU\\{base}" /v ShowStatusBar /t REG_DWORD /d 0 /f')
        run_command(f'reg add "HKCU\\{base}" /v AutoCheckSelect /t REG_DWORD /d 0 /f')
        return "Explorer optimized."
    except Exception as e:
        return f"Error: {e}"

def reset_explorer():
    try:
        base = r"Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced"
        run_command(f'reg add "HKCU\\{base}" /v SeparateProcess /t REG_DWORD /d 0 /f')
        run_command(f'reg add "HKCU\\{base}" /v ShowStatusBar /t REG_DWORD /d 1 /f')
        return "Explorer defaults restored."
    except Exception as e:
        return f"Error: {e}"

# --- COMPOSITE OPTIMIZATIONS ---

def apply_general_optimizations():
    log = []
    try:
        log.append(optimize_visual_fx())
        log.append(disable_lso())
        log.append(apply_tcp_optimizations())
        log.append(enable_trim())
        log.append(optimize_explorer())
        return "\n".join(log)
    except Exception as e:
        return f"Error: {e}"

# --- NETWORK & STORAGE EXTRAS ---

def optimize_network_congestion():
    try:
        run_command('reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile" /v NetworkThrottlingIndex /t REG_DWORD /d 4294967295 /f')
        run_command('reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile" /v SystemResponsiveness /t REG_DWORD /d 10 /f')
        return "Network congestion provider optimized."
    except Exception as e:
        return f"Error: {e}"

def reset_network_congestion():
    try:
        run_command('reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile" /v NetworkThrottlingIndex /t REG_DWORD /d 10 /f')
        run_command('reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile" /v SystemResponsiveness /t REG_DWORD /d 20 /f')
        return "Network congestion defaults restored."
    except Exception as e:
        return f"Error: {e}"

def disable_deprecated_network_features():
    try:
        cmds = [
            "netsh interface teredo set state disabled",
            "netsh interface 6to4 set state disabled",
            "netsh interface isatap set state disabled"
        ]
        for c in cmds:
            run_command(c)
        return "Deprecated IPv6 tunneling features disabled."
    except Exception as e:
        return f"Error: {e}"

def enable_deprecated_network_features():
    try:
        cmds = [
            "netsh interface teredo set state type=client",
            "netsh interface 6to4 set state enabled",
            "netsh interface isatap set state enabled"
        ]
        for c in cmds:
            run_command(c)
        return "Deprecated IPv6 tunneling features enabled."
    except Exception as e:
        return f"Error: {e}"

def enable_trim():
    try:
        run_command("fsutil behavior set DisableDeleteNotify 0")
        return "TRIM enabled."
    except Exception as e:
        return f"Error: {e}"

def disable_trim():
    try:
        run_command("fsutil behavior set DisableDeleteNotify 1")
        return "TRIM disabled."
    except Exception as e:
        return f"Error: {e}"

def optimize_drives():
    try:
        run_powershell('Get-Volume | Where-Object {$_.DriveType -eq "Fixed"} | ForEach-Object { Optimize-Volume -DriveLetter $_.DriveLetter -ReTrim -Verbose }')
        run_command("defrag /C /U /V")
        return "Drives optimized (TRIM and defrag)."
    except Exception as e:
        return f"Error: {e}"

def optimize_dscp_policy():
    try:
        run_powershell('New-NetQosPolicy -Name "PCFIX_LowLatency" -AppPathNameMatchCondition "*" -DSCPValue 46 -IPProtocolMatchCondition Both -ErrorAction SilentlyContinue')
        return "DSCP low-latency QoS policy applied."
    except Exception as e:
        return f"Error: {e}"

def remove_dscp_policy():
    try:
        run_powershell('Remove-NetQosPolicy -Name "PCFIX_LowLatency" -Confirm:$false -ErrorAction SilentlyContinue')
        return "DSCP QoS policy removed."
    except Exception as e:
        return f"Error: {e}"

def disable_ucpd():
    try:
        run_command("sc stop UCPD")
        run_command("sc config UCPD start= disabled")
        return "User Choice Protection Driver (UCPD) disabled."
    except Exception as e:
        return f"Error: {e}"

def enable_ucpd():
    try:
        run_command("sc config UCPD start= demand")
        return "User Choice Protection Driver (UCPD) enabled."
    except Exception as e:
        return f"Error: {e}"

# --- ADDITIONAL OPTIMIZATIONS ---

def optimize_netsh():
    try:
        cmds = [
            "netsh interface tcp set heuristics disabled",
            "netsh int tcp set global autotuninglevel=normal",
            "netsh int tcp set global rss=enabled",
            "netsh int tcp set global ecncapability=disabled",
            "netsh int tcp set global dca=disabled",
            "netsh int tcp set global rsc=disabled",
            "netsh int tcp set global pacingprofile=off"
        ]
        for c in cmds:
            run_command(c)
        return "Netsh network settings optimized."
    except Exception as e:
        return f"Error: {e}"

def reset_netsh():
    try:
        run_command("netsh int tcp reset")
        run_command("netsh interface tcp set heuristics enabled")
        return "Netsh TCP settings reset."
    except Exception as e:
        return f"Error: {e}"

def optimize_memory_management():
    try:
        base = r"SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management"
        run_command(f'reg add "HKLM\\{base}" /v DisablePagingExecutive /t REG_DWORD /d 1 /f')
        run_command(f'reg add "HKLM\\{base}" /v LargeSystemCache /t REG_DWORD /d 0 /f')
        return "Memory management optimized (reduced paging of kernel)."
    except Exception as e:
        return f"Error: {e}"

def reset_memory_management():
    try:
        base = r"SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management"
        run_command(f'reg add "HKLM\\{base}" /v DisablePagingExecutive /t REG_DWORD /d 0 /f')
        return "Memory management defaults restored."
    except Exception as e:
        return f"Error: {e}"

def optimize_io_operations():
    try:
        run_command('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management\\PrefetchParameters" /v EnablePrefetcher /t REG_DWORD /d 3 /f')
        run_command('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management\\PrefetchParameters" /v EnableSuperfetch /t REG_DWORD /d 3 /f')
        run_command("sc config SysMain start= auto")
        return "I/O operations optimized (prefetch/superfetch)."
    except Exception as e:
        return f"Error: {e}"

def reset_io_operations():
    try:
        run_command('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management\\PrefetchParameters" /v EnablePrefetcher /t REG_DWORD /d 3 /f')
        run_command('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management\\PrefetchParameters" /v EnableSuperfetch /t REG_DWORD /d 3 /f')
        return "I/O operations defaults restored."
    except Exception as e:
        return f"Error: {e}"

def enable_gpu_hardware_scheduling():
    try:
        run_command('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers" /v HwSchMode /t REG_DWORD /d 2 /f')
        return "Hardware GPU Scheduling enabled."
    except Exception as e:
        return f"Error: {e}"

def disable_gpu_hardware_scheduling():
    try:
        run_command('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers" /v HwSchMode /t REG_DWORD /d 1 /f')
        return "Hardware GPU Scheduling disabled."
    except Exception as e:
        return f"Error: {e}"

def enable_msi():
    try:
        script = (
            'Get-ChildItem -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Enum\\PCI" -Recurse '
            '| Where-Object { $_.Name -like "*MessageSignaledInterruptProperties" } '
            '| ForEach-Object { New-ItemProperty -Path $_.PSPath -Name "MSISupported" -PropertyType DWord -Value 1 -Force }'
        )
        run_powershell(script)
        return "Message Signaled Interrupts enabled where supported."
    except Exception as e:
        return f"Error: {e}"

def disable_msi():
    try:
        script = (
            'Get-ChildItem -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Enum\\PCI" -Recurse '
            '| Where-Object { $_.Name -like "*MessageSignaledInterruptProperties" } '
            '| ForEach-Object { New-ItemProperty -Path $_.PSPath -Name "MSISupported" -PropertyType DWord -Value 0 -Force }'
        )
        run_powershell(script)
        return "Message Signaled Interrupts disabled."
    except Exception as e:
        return f"Error: {e}"

# --- UI & EXPLORER VISIBILITY ---

def show_file_extensions():
    try:
        run_command('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v HideFileExt /t REG_DWORD /d 0 /f')
        return "File extensions shown."
    except Exception as e:
        return f"Error: {e}"

def hide_file_extensions():
    try:
        run_command('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v HideFileExt /t REG_DWORD /d 1 /f')
        return "File extensions hidden."
    except Exception as e:
        return f"Error: {e}"

def show_hidden_files():
    try:
        run_command('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v Hidden /t REG_DWORD /d 1 /f')
        run_command('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v ShowSuperHidden /t REG_DWORD /d 1 /f')
        return "Hidden files shown."
    except Exception as e:
        return f"Error: {e}"

def hide_hidden_files():
    try:
        run_command('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v Hidden /t REG_DWORD /d 2 /f')
        run_command('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v ShowSuperHidden /t REG_DWORD /d 0 /f')
        return "Hidden files hidden."
    except Exception as e:
        return f"Error: {e}"

# --- NETWORK & UPDATE POLICIES ---

def disable_smb1():
    try:
        return run_command("DISM /Online /Disable-Feature /FeatureName:SMB1Protocol /NoRestart")
    except Exception as e:
        return f"Error: {e}"

def enable_smb1():
    try:
        return run_command("DISM /Online /Enable-Feature /FeatureName:SMB1Protocol /All /NoRestart")
    except Exception as e:
        return f"Error: {e}"

def prefer_ipv4():
    try:
        run_command('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip6\\Parameters" /v DisabledComponents /t REG_DWORD /d 32 /f')
        return "Prefer IPv4 over IPv6 applied."
    except Exception as e:
        return f"Error: {e}"

def prefer_ipv_default():
    try:
        run_command('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip6\\Parameters" /v DisabledComponents /t REG_DWORD /d 0 /f')
        return "Default IPv4/IPv6 preference restored."
    except Exception as e:
        return f"Error: {e}"

def disable_netbios():
    try:
        script = 'Get-WmiObject Win32_NetworkAdapterConfiguration -Filter "IPEnabled = True" | ForEach-Object { $_.TcpipNetbiosOptions = 2; $_.Put() }'
        run_powershell(script)
        return "NetBIOS over TCP/IP disabled."
    except Exception as e:
        return f"Error: {e}"

def enable_netbios():
    try:
        script = 'Get-WmiObject Win32_NetworkAdapterConfiguration -Filter "IPEnabled = True" | ForEach-Object { $_.TcpipNetbiosOptions = 0; $_.Put() }'
        run_powershell(script)
        return "NetBIOS over TCP/IP enabled."
    except Exception as e:
        return f"Error: {e}"

def pause_windows_update():
    try:
        run_command('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate\\AU" /v NoAutoUpdate /t REG_DWORD /d 1 /f')
        return "Windows Update paused."
    except Exception as e:
        return f"Error: {e}"

def resume_windows_update():
    try:
        run_command('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate\\AU" /v NoAutoUpdate /t REG_DWORD /d 0 /f')
        return "Windows Update resumed."
    except Exception as e:
        return f"Error: {e}"

def disable_auto_reboot_update():
    try:
        run_command('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate\\AU" /v NoAutoRebootWithLoggedOnUsers /t REG_DWORD /d 1 /f')
        return "Auto-reboot after updates disabled."
    except Exception as e:
        return f"Error: {e}"

def enable_auto_reboot_update():
    try:
        run_command('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate\\AU" /v NoAutoRebootWithLoggedOnUsers /t REG_DWORD /d 0 /f')
        return "Auto-reboot after updates enabled."
    except Exception as e:
        return f"Error: {e}"

# --- SERVICES & APP BEHAVIOR ---

def disable_search_index():
    try:
        run_command("sc stop WSearch")
        run_command("sc config WSearch start= disabled")
        return "Windows Search indexing disabled."
    except Exception as e:
        return f"Error: {e}"

def enable_search_index():
    try:
        run_command("sc config WSearch start= auto")
        run_command("sc start WSearch")
        return "Windows Search indexing enabled."
    except Exception as e:
        return f"Error: {e}"

def disable_sysmain():
    try:
        run_command("sc stop SysMain")
        run_command("sc config SysMain start= disabled")
        return "SysMain disabled."
    except Exception as e:
        return f"Error: {e}"

def enable_sysmain():
    try:
        run_command("sc config SysMain start= auto")
        return "SysMain enabled."
    except Exception as e:
        return f"Error: {e}"

def disable_background_apps():
    try:
        run_command('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\BackgroundAccessApplications" /v GlobalUserDisabled /t REG_DWORD /d 1 /f')
        return "Background apps disabled."
    except Exception as e:
        return f"Error: {e}"

def enable_background_apps():
    try:
        run_command('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\BackgroundAccessApplications" /v GlobalUserDisabled /t REG_DWORD /d 0 /f')
        return "Background apps enabled."
    except Exception as e:
        return f"Error: {e}"

# --- PRIVACY POLICIES ---

def disable_ad_id():
    try:
        run_command('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\AdvertisingInfo" /v Enabled /t REG_DWORD /d 0 /f')
        return "Advertising ID disabled."
    except Exception as e:
        return f"Error: {e}"

def enable_ad_id():
    try:
        run_command('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\AdvertisingInfo" /v Enabled /t REG_DWORD /d 1 /f')
        return "Advertising ID enabled."
    except Exception as e:
        return f"Error: {e}"

def disable_activity_history():
    try:
        run_command('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\System" /v PublishUserActivities /t REG_DWORD /d 0 /f')
        return "Activity history disabled."
    except Exception as e:
        return f"Error: {e}"

def enable_activity_history():
    try:
        run_command('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\System" /v PublishUserActivities /t REG_DWORD /d 1 /f')
        return "Activity history enabled."
    except Exception as e:
        return f"Error: {e}"

def disable_error_reporting():
    try:
        run_command('reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\Windows Error Reporting" /v Disabled /t REG_DWORD /d 1 /f')
        return "Error reporting disabled."
    except Exception as e:
        return f"Error: {e}"

def enable_error_reporting():
    try:
        run_command('reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\Windows Error Reporting" /v Disabled /t REG_DWORD /d 0 /f')
        return "Error reporting enabled."
    except Exception as e:
        return f"Error: {e}"

def disable_feedback():
    try:
        run_command('reg add "HKCU\\Software\\Microsoft\\Siuf\\Rules" /v NumberOfSIUFInPeriod /t REG_DWORD /d 0 /f')
        run_command('reg add "HKCU\\Software\\Microsoft\\Siuf\\Rules" /v PeriodInNanoSeconds /t REG_QWORD /d 0 /f')
        return "Feedback reminders disabled."
    except Exception as e:
        return f"Error: {e}"

def enable_feedback():
    try:
        run_command('reg add "HKCU\\Software\\Microsoft\\Siuf\\Rules" /v NumberOfSIUFInPeriod /t REG_DWORD /d 1 /f')
        return "Feedback reminders enabled."
    except Exception as e:
        return f"Error: {e}"

def disable_location():
    try:
        run_command('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\LocationAndSensors" /v DisableLocation /t REG_DWORD /d 1 /f')
        return "Location services disabled."
    except Exception as e:
        return f"Error: {e}"

def enable_location():
    try:
        run_command('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\LocationAndSensors" /v DisableLocation /t REG_DWORD /d 0 /f')
        return "Location services enabled."
    except Exception as e:
        return f"Error: {e}"

def disable_clipboard_history():
    try:
        run_command('reg add "HKCU\\Software\\Microsoft\\Clipboard" /v EnableClipboardHistory /t REG_DWORD /d 0 /f')
        return "Clipboard history disabled."
    except Exception as e:
        return f"Error: {e}"

def enable_clipboard_history():
    try:
        run_command('reg add "HKCU\\Software\\Microsoft\\Clipboard" /v EnableClipboardHistory /t REG_DWORD /d 1 /f')
        return "Clipboard history enabled."
    except Exception as e:
        return f"Error: {e}"

def disable_widgets():
    try:
        run_command('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v TaskbarDa /t REG_DWORD /d 0 /f')
        return "Widgets disabled."
    except Exception as e:
        return f"Error: {e}"

def enable_widgets():
    try:
        run_command('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v TaskbarDa /t REG_DWORD /d 1 /f')
        return "Widgets enabled."
    except Exception as e:
        return f"Error: {e}"

def disable_snap_assist():
    try:
        run_command('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v SnapAssist /t REG_DWORD /d 0 /f')
        return "Snap Assist disabled."
    except Exception as e:
        return f"Error: {e}"

def enable_snap_assist():
    try:
        run_command('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v SnapAssist /t REG_DWORD /d 1 /f')
        return "Snap Assist enabled."
    except Exception as e:
        return f"Error: {e}"

def disable_gamebar():
    try:
        run_command('reg add "HKCU\\Software\\Microsoft\\GameBar" /v EnableGameBar /t REG_DWORD /d 0 /f')
        return "Game Bar disabled."
    except Exception as e:
        return f"Error: {e}"

def enable_gamebar():
    try:
        run_command('reg add "HKCU\\Software\\Microsoft\\GameBar" /v EnableGameBar /t REG_DWORD /d 1 /f')
        return "Game Bar enabled."
    except Exception as e:
        return f"Error: {e}"

def disable_xbox_services():
    try:
        for svc in ["XblAuthManager", "XblGameSave", "XboxGipSvc", "XboxNetApiSvc"]:
            run_command(f"sc stop {svc}")
            run_command(f"sc config {svc} start= disabled")
        return "Xbox services disabled."
    except Exception as e:
        return f"Error: {e}"

def enable_xbox_services():
    try:
        for svc in ["XblAuthManager", "XblGameSave", "XboxGipSvc", "XboxNetApiSvc"]:
            run_command(f"sc config {svc} start= demand")
        return "Xbox services enabled."
    except Exception as e:
        return f"Error: {e}"

def disable_bing_search():
    try:
        run_command('reg add "HKCU\\Software\\Policies\\Microsoft\\Windows\\Explorer" /v DisableSearchBoxSuggestions /t REG_DWORD /d 1 /f')
        return "Bing web results in Start disabled."
    except Exception as e:
        return f"Error: {e}"

def enable_bing_search():
    try:
        run_command('reg add "HKCU\\Software\\Policies\\Microsoft\\Windows\\Explorer" /v DisableSearchBoxSuggestions /t REG_DWORD /d 0 /f')
        return "Bing web results in Start enabled."
    except Exception as e:
        return f"Error: {e}"

def enable_high_performance_plan():
    try:
        run_command("powercfg -setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c")
        return "High Performance plan enabled."
    except Exception as e:
        return f"Error: {e}"

def enable_balanced_plan():
    try:
        run_command("powercfg -setactive 381b4222-f694-41f0-9685-ff5bb260df2e")
        return "Balanced plan enabled."
    except Exception as e:
        return f"Error: {e}"

def disable_telemetry_global():
    try:
        run_command('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection" /v AllowTelemetry /t REG_DWORD /d 0 /f')
        return "Windows telemetry disabled."
    except Exception as e:
        return f"Error: {e}"

def enable_telemetry_global():
    try:
        run_command('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection" /v AllowTelemetry /t REG_DWORD /d 1 /f')
        return "Windows telemetry enabled."
    except Exception as e:
        return f"Error: {e}"

def disable_cortana_policy():
    try:
        run_command('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Windows Search" /v AllowCortana /t REG_DWORD /d 0 /f')
        return "Cortana disabled."
    except Exception as e:
        return f"Error: {e}"

def enable_cortana_policy():
    try:
        run_command('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Windows Search" /v AllowCortana /t REG_DWORD /d 1 /f')
        return "Cortana enabled."
    except Exception as e:
        return f"Error: {e}"

def disable_mouse_accel():
    try:
        run_command('reg add "HKCU\\Control Panel\\Mouse" /v MouseSpeed /t REG_SZ /d 0 /f')
        run_command('reg add "HKCU\\Control Panel\\Mouse" /v MouseThreshold1 /t REG_SZ /d 0 /f')
        run_command('reg add "HKCU\\Control Panel\\Mouse" /v MouseThreshold2 /t REG_SZ /d 0 /f')
        return "Mouse acceleration disabled."
    except Exception as e:
        return f"Error: {e}"

def enable_mouse_accel():
    try:
        run_command('reg add "HKCU\\Control Panel\\Mouse" /v MouseSpeed /t REG_SZ /d 1 /f')
        run_command('reg add "HKCU\\Control Panel\\Mouse" /v MouseThreshold1 /t REG_SZ /d 6 /f')
        run_command('reg add "HKCU\\Control Panel\\Mouse" /v MouseThreshold2 /t REG_SZ /d 10 /f')
        return "Mouse acceleration enabled."
    except Exception as e:
        return f"Error: {e}"

def disable_remote_desktop():
    try:
        run_command('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server" /v fDenyTSConnections /t REG_DWORD /d 1 /f')
        return "Remote Desktop disabled."
    except Exception as e:
        return f"Error: {e}"

def enable_remote_desktop():
    try:
        run_command('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server" /v fDenyTSConnections /t REG_DWORD /d 0 /f')
        return "Remote Desktop enabled."
    except Exception as e:
        return f"Error: {e}"
def run_memory_diagnostic():
    return run_command("mdsched.exe")
def set_dns_cloudflare():
    try:
        script = 'Get-DnsClient | Where-Object { $_.InterfaceAlias -notlike "*Loopback*" } | Set-DnsClientServerAddress -ServerAddresses 1.1.1.1,1.0.0.1'
        run_powershell(script)
        return "DNS set to Cloudflare."
    except Exception as e:
        return f"Error: {e}"

def restore_dns_dhcp():
    try:
        script = 'Get-DnsClient | Where-Object { $_.InterfaceAlias -notlike "*Loopback*" } | Set-DnsClientServerAddress -ResetServerAddresses'
        run_powershell(script)
        return "DNS restored to DHCP."
    except Exception as e:
        return f"Error: {e}"

def flush_dns():
    try:
        return run_command("ipconfig /flushdns")
    except Exception as e:
        return f"Error: {e}"

def reset_winsock():
    try:
        return run_command("netsh winsock reset")
    except Exception as e:
        return f"Error: {e}"

def disable_hibernate():
    try:
        return run_command("powercfg -h off")
    except Exception as e:
        return f"Error: {e}"

def enable_hibernate():
    try:
        return run_command("powercfg -h on")
    except Exception as e:
        return f"Error: {e}"

def disable_fast_startup():
    try:
        run_command('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Power" /v HiberbootEnabled /t REG_DWORD /d 0 /f')
        return "Fast Startup disabled."
    except Exception as e:
        return f"Error: {e}"

def enable_fast_startup():
    try:
        run_command('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Power" /v HiberbootEnabled /t REG_DWORD /d 1 /f')
        return "Fast Startup enabled."
    except Exception as e:
        return f"Error: {e}"

def disable_power_throttling():
    try:
        run_command('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Power\\PowerThrottling" /v PowerThrottlingOff /t REG_DWORD /d 1 /f')
        return "Power throttling disabled."
    except Exception as e:
        return f"Error: {e}"

def enable_power_throttling():
    try:
        run_command('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Power\\PowerThrottling" /v PowerThrottlingOff /t REG_DWORD /d 0 /f')
        return "Power throttling enabled."
    except Exception as e:
        return f"Error: {e}"

def disable_usb_selective_suspend():
    try:
        run_command("powercfg /SETACVALUEINDEX SCHEME_CURRENT SUB_USB USBSELECTIVE SUSPEND 1")
        run_command("powercfg /SETDCVALUEINDEX SCHEME_CURRENT SUB_USB USBSELECTIVE SUSPEND 1")
        run_command("powercfg -SetActive SCHEME_CURRENT")
        return "USB selective suspend disabled."
    except Exception as e:
        return f"Error: {e}"

def enable_usb_selective_suspend():
    try:
        run_command("powercfg /SETACVALUEINDEX SCHEME_CURRENT SUB_USB USBSELECTIVE SUSPEND 0")
        run_command("powercfg /SETDCVALUEINDEX SCHEME_CURRENT SUB_USB USBSELECTIVE SUSPEND 0")
        run_command("powercfg -SetActive SCHEME_CURRENT")
        return "USB selective suspend enabled."
    except Exception as e:
        return f"Error: {e}"

def disable_print_spooler():
    try:
        run_command("sc stop Spooler")
        run_command("sc config Spooler start= disabled")
        return "Print Spooler disabled."
    except Exception as e:
        return f"Error: {e}"

def enable_print_spooler():
    try:
        run_command("sc config Spooler start= auto")
        run_command("sc start Spooler")
        return "Print Spooler enabled."
    except Exception as e:
        return f"Error: {e}"

def disable_remote_assistance():
    try:
        run_command('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Remote Assistance" /v fAllowToGetHelp /t REG_DWORD /d 0 /f')
        return "Remote Assistance disabled."
    except Exception as e:
        return f"Error: {e}"

def enable_remote_assistance():
    try:
        run_command('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Remote Assistance" /v fAllowToGetHelp /t REG_DWORD /d 1 /f')
        return "Remote Assistance enabled."
    except Exception as e:
        return f"Error: {e}"

def disable_onedrive():
    try:
        run_command('reg add "HKLM\\Software\\Policies\\Microsoft\\Windows\\OneDrive" /v DisableFileSyncNGSC /t REG_DWORD /d 1 /f')
        return "OneDrive sync disabled."
    except Exception as e:
        return f"Error: {e}"

def enable_onedrive():
    try:
        run_command('reg add "HKLM\\Software\\Policies\\Microsoft\\Windows\\OneDrive" /v DisableFileSyncNGSC /t REG_DWORD /d 0 /f')
        return "OneDrive sync enabled."
    except Exception as e:
        return f"Error: {e}"

def disable_windows_tips():
    try:
        run_command('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager" /v SoftLandingEnabled /t REG_DWORD /d 0 /f')
        run_command('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager" /v SubscribedContent-310093Enabled /t REG_DWORD /d 0 /f')
        return "Windows tips disabled."
    except Exception as e:
        return f"Error: {e}"

def enable_windows_tips():
    try:
        run_command('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager" /v SoftLandingEnabled /t REG_DWORD /d 1 /f')
        run_command('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager" /v SubscribedContent-310093Enabled /t REG_DWORD /d 1 /f')
        return "Windows tips enabled."
    except Exception as e:
        return f"Error: {e}"

def disable_app_suggestions():
    try:
        run_command('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager" /v SystemPaneSuggestionsEnabled /t REG_DWORD /d 0 /f')
        run_command('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager" /v SubscribedContent-338388Enabled /t REG_DWORD /d 0 /f')
        return "App suggestions disabled."
    except Exception as e:
        return f"Error: {e}"

def enable_app_suggestions():
    try:
        run_command('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager" /v SystemPaneSuggestionsEnabled /t REG_DWORD /d 1 /f')
        run_command('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager" /v SubscribedContent-338388Enabled /t REG_DWORD /d 1 /f')
        return "App suggestions enabled."
    except Exception as e:
        return f"Error: {e}"

def disable_autoplay():
    try:
        run_command('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\AutoplayHandlers" /v DisableAutoplay /t REG_DWORD /d 1 /f')
        return "Autoplay disabled."
    except Exception as e:
        return f"Error: {e}"

def enable_autoplay():
    try:
        run_command('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\AutoplayHandlers" /v DisableAutoplay /t REG_DWORD /d 0 /f')
        return "Autoplay enabled."
    except Exception as e:
        return f"Error: {e}"

def disable_sharing_wizard():
    try:
        run_command('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v SharingWizardOn /t REG_DWORD /d 0 /f')
        return "Sharing Wizard disabled."
    except Exception as e:
        return f"Error: {e}"

def enable_sharing_wizard():
    try:
        run_command('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v SharingWizardOn /t REG_DWORD /d 1 /f')
        return "Sharing Wizard enabled."
    except Exception as e:
        return f"Error: {e}"

def clear_windows_update_cache():
    try:
        run_command("net stop wuauserv")
        run_command("net stop bits")
        run_command('cmd /c rmdir /S /Q "C:\\Windows\\SoftwareDistribution\\Download"')
        run_command("net start wuauserv")
        run_command("net start bits")
        return "Windows Update cache cleared."
    except Exception as e:
        return f"Error: {e}"

def reset_store_cache():
    try:
        return run_command("wsreset")
    except Exception as e:
        return f"Error: {e}"

def enable_storage_sense():
    try:
        run_command('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\StorageSense\\Parameters\\StoragePolicy" /v 01 /t REG_DWORD /d 1 /f')
        return "Storage Sense enabled."
    except Exception as e:
        return f"Error: {e}"

def disable_storage_sense():
    try:
        run_command('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\StorageSense\\Parameters\\StoragePolicy" /v 01 /t REG_DWORD /d 0 /f')
        return "Storage Sense disabled."
    except Exception as e:
        return f"Error: {e}"

def enable_core_isolation():
    try:
        run_command('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\DeviceGuard" /v EnableVirtualizationBasedSecurity /t REG_DWORD /d 1 /f')
        run_command('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\DeviceGuard\\Scenarios\\HypervisorEnforcedCodeIntegrity" /v Enabled /t REG_DWORD /d 1 /f')
        return "Core Isolation enabled."
    except Exception as e:
        return f"Error: {e}"

def disable_core_isolation():
    try:
        run_command('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\DeviceGuard" /v EnableVirtualizationBasedSecurity /t REG_DWORD /d 0 /f')
        run_command('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\DeviceGuard\\Scenarios\\HypervisorEnforcedCodeIntegrity" /v Enabled /t REG_DWORD /d 0 /f')
        return "Core Isolation disabled."
    except Exception as e:
        return f"Error: {e}"

def disable_driver_auto_update():
    try:
        run_command('reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\DriverSearching" /v SearchOrderConfig /t REG_DWORD /d 0 /f')
        return "Automatic driver updates disabled."
    except Exception as e:
        return f"Error: {e}"

def enable_driver_auto_update():
    try:
        run_command('reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\DriverSearching" /v SearchOrderConfig /t REG_DWORD /d 2 /f')
        return "Automatic driver updates enabled."
    except Exception as e:
        return f"Error: {e}"

def create_restore_point():
    try:
        return run_powershell('Checkpoint-Computer -Description "PCFIX Restore Point" -RestorePointType "MODIFY_SETTINGS"')
    except Exception as e:
        return f"Error: {e}"

def run_sfc():
    try:
        return run_command("sfc /scannow")
    except Exception as e:
        return f"Error: {e}"

def run_dism_restorehealth():
    try:
        return run_command("DISM /Online /Cleanup-Image /RestoreHealth")
    except Exception as e:
        return f"Error: {e}"

def disable_copilot_policy():
    try:
        run_command('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsCopilot" /v TurnOffWindowsCopilot /t REG_DWORD /d 1 /f')
        return "Windows Copilot disabled."
    except Exception as e:
        return f"Error: {e}"

def enable_copilot_policy():
    try:
        run_command('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsCopilot" /v TurnOffWindowsCopilot /t REG_DWORD /d 0 /f')
        return "Windows Copilot enabled."
    except Exception as e:
        return f"Error: {e}"

def disable_lock_screen_spotlight():
    try:
        run_command('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager" /v RotatingLockScreenEnabled /t REG_DWORD /d 0 /f')
        run_command('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager" /v RotatingLockScreenOverlayEnabled /t REG_DWORD /d 0 /f')
        return "Lock screen Spotlight disabled."
    except Exception as e:
        return f"Error: {e}"

def enable_lock_screen_spotlight():
    try:
        run_command('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager" /v RotatingLockScreenEnabled /t REG_DWORD /d 1 /f')
        run_command('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager" /v RotatingLockScreenOverlayEnabled /t REG_DWORD /d 1 /f')
        return "Lock screen Spotlight enabled."
    except Exception as e:
        return f"Error: {e}"

def export_settings_to_desktop():
    try:
        cfg = load_config()
        ts = str(int(time.time()))
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        if not os.path.exists(desktop):
            desktop = os.path.expanduser("~")
        path = os.path.join(desktop, f"pcfix_config_{ts}.json")
        with open(path, "w") as f:
            json.dump(cfg, f, indent=4)
        return f"Exported: {path}"
    except Exception as e:
        return f"Error: {e}"
def run_memory_diagnostic():
    return run_command("mdsched.exe")

def run_chkdsk_scan():
    # Runs read-only scan
    return run_command("chkdsk C:")

# --- POWER & GAMING ---

def enable_ultimate_performance():
    res = run_command("powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61")
    run_command("powercfg -setactive e9a42b02-d5df-448d-aa00-03f14749eb61")
    return "Ultimate Performance Plan Enabled."

def disable_hibernation():
    return run_command("powercfg -h off")

def enable_hibernation():
    return run_command("powercfg -h on")

def optimize_gpu_priority():
    try:
        key_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games"
        run_command(f'reg add "HKLM\\{key_path}" /v "GPU Priority" /t REG_DWORD /d 8 /f')
        run_command(f'reg add "HKLM\\{key_path}" /v "Priority" /t REG_DWORD /d 6 /f')
        run_command(f'reg add "HKLM\\{key_path}" /v "Scheduling Category" /t REG_SZ /d "High" /f')
        return "GPU Priority Optimized."
    except Exception as e:
        return f"Error: {e}"

def gaming_mode_on():
    # Alias for main.py compatibility
    return enable_gaming_mode()

def enable_gaming_mode():
    enable_ultimate_performance()
    optimize_ram()
    # Kill common non-essential apps
    apps = ["chrome", "msedge", "discord", "spotify", "teams"]
    count = 0
    for app in apps:
        try:
            kill_process_by_name(app)
            count += 1
        except:
            pass
    return f"Gaming Mode Active. Apps closed."

# --- DNS ---

def set_dns_google():
    return run_powershell('Set-DnsClientServerAddress -InterfaceAlias "Wi-Fi" -ServerAddresses ("8.8.8.8","8.8.4.4")')

def set_dns_cloudflare():
    return run_powershell('Set-DnsClientServerAddress -InterfaceAlias "Wi-Fi" -ServerAddresses ("1.1.1.1","1.0.0.1")')

def set_dns_auto():
    return run_powershell('Set-DnsClientServerAddress -InterfaceAlias "Wi-Fi" -ResetServerAddresses')

# --- CONFIG MANAGER ---

def _config_path():
    return os.path.join(_pcfix_data_dir(), "config.json")

def _migrate_legacy_config():
    legacy = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.json")
    legacy = os.path.normpath(legacy)
    target = _config_path()
    if os.path.isfile(legacy) and not os.path.isfile(target):
        try:
            shutil.copy2(legacy, target)
        except Exception:
            pass

def load_config():
    _migrate_legacy_config()
    path = _config_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_config(config):
    try:
        path = _config_path()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        return True
    except Exception:
        return False

def play_startup_sound():
    config = load_config()
    sound_path = config.get("startup_sound", "")
    def _play():
        try:
            if sound_path and os.path.exists(sound_path):
                winsound.PlaySound(sound_path, winsound.SND_FILENAME)
            else:
                winsound.Beep(600, 100)
        except:
            pass
    threading.Thread(target=_play, daemon=True).start()

# --- DEBLOATER & PRIVACY ---

def get_installed_bloatware():
    bloat_list = [
        "Microsoft.YourPhone", "Microsoft.XboxApp", "Microsoft.GetHelp", "Microsoft.People", 
        "Microsoft.SkypeApp", "Microsoft.SolitaireCollection", "Microsoft.WindowsAlarms", 
        "Microsoft.WindowsCamera", "Microsoft.WindowsFeedbackHub", "Microsoft.WindowsMaps", 
        "Microsoft.BingNews", "Microsoft.BingWeather"
    ]
    installed = []
    try:
        res = run_powershell('Get-AppxPackage | Select-Object -ExpandProperty Name')
        for pkg in res.split('\n'):
            pkg = pkg.strip()
            if pkg in bloat_list:
                installed.append(pkg)
    except:
        pass
    return installed

def remove_bloatware(package_name):
    try:
        run_powershell(f'Get-AppxPackage *{package_name}* | Remove-AppxPackage')
        return f"Removed {package_name}"
    except Exception as e:
        return f"Error: {e}"

def apply_privacy_shield():
    try:
        run_command('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection" /v AllowTelemetry /t REG_DWORD /d 0 /f')
        run_command('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Windows Search" /v AllowCortana /t REG_DWORD /d 0 /f')
        return "Privacy Shield Applied."
    except Exception as e:
        return f"Error: {e}"

def create_god_mode():
    try:
        desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
        path = os.path.join(desktop, "GodMode.{ED7BA470-8E54-465E-825C-99712043E01C}")
        if not os.path.exists(path):
            os.mkdir(path)
            return "God Mode created."
        return "God Mode exists."
    except Exception as e:
        return f"Error: {e}"

# --- SMART SCAN ---

def run_smart_scan():
    log = []
    log.append(clean_temp_files())
    log.append(flush_dns())
    log.append(optimize_ram())
    log.append(optimize_visual_fx())
    return "\n".join(log)

def generate_battery_report():
    try:
        desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
        path = os.path.join(desktop, "battery_report.html")
        run_command(f"powercfg /batteryreport /output \"{path}\"")
        os.startfile(path)
        return "Battery Report generated."
    except Exception as e:
        return f"Error: {e}"

def export_system_info():
    try:
        info = get_detailed_info()
        desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
        path = os.path.join(desktop, "system_specs.txt")
        with open(path, "w") as f:
            for k, v in info.items():
                f.write(f"{k}: {v}\n")
        os.startfile(path)
        return "Specs exported."
    except Exception as e:
        return f"Error: {e}"

def launch_tool(tool_name):
    tools = {"taskmgr": "taskmgr", "regedit": "regedit", "devmgmt": "devmgmt.msc", "control": "control"}
    if tool_name in tools:
        subprocess.Popen(tools[tool_name], shell=True)
        return f"Launched {tool_name}"
    return "Unknown Tool"

# --- NETWORK INFO ---

def get_network_info():
    info = {'ip': 'N/A', 'mac': 'N/A', 'iface': 'Wi-Fi', 'gateway': 'N/A'}
    try:
        addrs = psutil.net_if_addrs()
        for iface, snics in addrs.items():
            if "wi-fi" in iface.lower() or "ethernet" in iface.lower():
                for snic in snics:
                    if snic.family == socket.AF_INET:
                        info['ip'] = snic.address
                        info['iface'] = iface
                    if snic.family == psutil.AF_LINK:
                        info['mac'] = snic.address
        
        # Gateway
        res = run_command("ipconfig")
        for line in res.split('\n'):
            if "Default Gateway" in line:
                val = line.split(":")[-1].strip()
                if val and val != "0.0.0.0":
                    info['gateway'] = val
                    break
    except:
        pass
    return info

def run_ping_test(host):
    res = run_command(f"ping -n 1 -w 1000 {host}")
    if "Received = 1" in res:
        match = re.search(r"time[=<](\d+)ms", res)
        return f"{match.group(1)} ms" if match else "Online"
    return "Offline"

def reset_adapter(adapter_name):
    run_command(f'netsh interface set interface "{adapter_name}" admin=disable')
    time.sleep(2)
    run_command(f'netsh interface set interface "{adapter_name}" admin=enable')
    return "Adapter Reset."

# --- STARTUP MANAGER ---
DISABLED_STARTUP_FILE = "disabled_startup.json"

def get_startup_apps():
    apps = []
    disabled_list = []
    if os.path.exists(DISABLED_STARTUP_FILE):
        try:
            with open(DISABLED_STARTUP_FILE, "r") as f:
                disabled_list = json.load(f)
        except:
            pass

    # Registry Read
    for root in [winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE]:
        try:
            key = winreg.OpenKey(root, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
            i = 0
            while True:
                try:
                    name, value, _ = winreg.EnumValue(key, i)
                    loc = "User" if root == winreg.HKEY_CURRENT_USER else "System"
                    apps.append({"name": name, "path": value, "location": f"Registry ({loc})", "enabled": True})
                    i += 1
                except OSError:
                    break
            winreg.CloseKey(key)
        except:
            pass

    # Merge Disabled
    for d in disabled_list:
        d["enabled"] = False
        if not any(a['name'] == d['name'] for a in apps):
            apps.append(d)
    return apps

def toggle_startup_app(app_data, enable):
    try:
        disabled = []
        if os.path.exists(DISABLED_STARTUP_FILE):
            with open(DISABLED_STARTUP_FILE, "r") as f:
                disabled = json.load(f)

        if enable:
            # Re-enable
            entry = next((d for d in disabled if d["name"] == app_data["name"]), None)
            if not entry and app_data.get("path"): entry = app_data # Fallback
            
            if entry:
                disabled = [d for d in disabled if d["name"] != entry["name"]]
                with open(DISABLED_STARTUP_FILE, "w") as f: json.dump(disabled, f, indent=4)
                
                root = winreg.HKEY_CURRENT_USER if "User" in entry.get("location", "User") else winreg.HKEY_LOCAL_MACHINE
                key = winreg.OpenKey(root, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_WRITE)
                winreg.SetValueEx(key, entry["name"], 0, winreg.REG_SZ, entry["path"])
                winreg.CloseKey(key)
                return True
        else:
            # Disable
            if not any(d['name'] == app_data['name'] for d in disabled):
                disabled.append(app_data)
                with open(DISABLED_STARTUP_FILE, "w") as f: json.dump(disabled, f, indent=4)
            
            root = winreg.HKEY_CURRENT_USER if "User" in app_data["location"] else winreg.HKEY_LOCAL_MACHINE
            key = winreg.OpenKey(root, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_WRITE)
            winreg.DeleteValue(key, app_data["name"])
            winreg.CloseKey(key)
            return True
    except Exception as e:
        return False
    return False

def force_delete_path(path):
    # Shred/Force Delete
    try:
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)
        return "Deleted successfully."
    except:
        # Try unlocker approach (basic)
        return f"Could not delete {path}. Access Denied."
