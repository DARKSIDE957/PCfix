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
    # Query System Event Log for BugCheck events (Event ID 1001)
    crashes = []
    try:
        # We use PowerShell to get the last 5 BugCheck events formatted as a list
        cmd = "Get-EventLog -LogName System -EventId 1001 -Newest 5 | Format-List TimeGenerated, Message"
        res = run_powershell(cmd)
        
        if not res or "No matches found" in res:
            return []

        # Parse the output. PowerShell Format-List output separates entries with blank lines.
        # We split by "TimeGenerated :" since that's the first field we requested.
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
            
            # Extract BugCheck Code (Hex)
            code_val = "CRITICAL"
            match = re.search(r'0x[0-9A-Fa-f]{8}', message_val)
            if match:
                code_val = match.group(0)
            
            crashes.append({
                "time": time_val,
                "code": code_val
            })
            
        return crashes
    except Exception:
        return []

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

CONFIG_FILE = "config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_config(config):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
        return True
    except:
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
