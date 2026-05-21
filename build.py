import os
import shutil
import subprocess
import time

try:
    import psutil
except ImportError:
    psutil = None

def kill_process(name):
    if psutil is None:
        return
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == name:
            try:
                proc.terminate()
                proc.wait(timeout=3)
            except:
                pass
            
def safe_remove(path):
    if not os.path.exists(path):
        return
    try:
        os.remove(path)
    except Exception as e:
        print(f"Warning: could not remove {path}: {e}")
        try:
            os.replace(path, path + ".old")
        except Exception as e2:
            print(f"Warning: could not rename {path}: {e2}")

def safe_move(src, dst):
    # Ensure destination directory exists
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    # If destination exists, remove or overwrite
    if os.path.exists(dst):
        safe_remove(dst)
    try:
        os.replace(src, dst)  # atomic replace on Windows
    except Exception:
        shutil.move(src, dst)

def clean_old_builds():
    print("Cleaning old builds...")
    kill_process("PCFIX.exe")
    kill_process("PCFIX_v3.8.exe")
    kill_process("PCFIX_v3.9.exe")
    kill_process("PCFIX_v3.10.exe")
    
    # Try multiple times to delete dist
    for i in range(3):
        try:
            if os.path.exists("dist"):
                shutil.rmtree("dist")
            break
        except Exception as e:
            print(f"Retry {i+1} deleting dist: {e}")
            time.sleep(1)

    if os.path.exists("build"):
        shutil.rmtree("build")
    if os.path.exists("PCFIX.spec"):
        os.remove("PCFIX.spec")
    if os.path.exists("PCFIX_Setup.spec"):
        os.remove("PCFIX_Setup.spec")
    
    # Remove versioned specs if any
    for f in os.listdir("."):
        if f.startswith("PCFIX_Setup_") and f.endswith(".spec"):
            os.remove(f)
            
    print("Cleaned.")

VERSION = "v3.10"

def build_exe():
    print("Building PCFIX.exe...")
    import customtkinter
    ctk_path = os.path.dirname(customtkinter.__file__)
    
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--uac-admin",
        "--icon", "icon.ico",
        "--name", "PCFIX",
        "--hidden-import", "modules",
        "--hidden-import", "modules.core",
        "--hidden-import", "PIL",
        "--hidden-import", "PIL.Image",
        "--hidden-import", "pystray",
        "--hidden-import", "psutil",
        "--collect-submodules", "customtkinter",
        "--add-data", f"{ctk_path};customtkinter",
        "--add-data", "modules;modules",
        "--add-data", "icon.ico;.",
        "main.py"
    ]
    
    subprocess.run(cmd, check=True)
    print("PCFIX.exe Build complete.")

def build_setup():
    setup_name = f"PCFIX_Setup_{VERSION}"
    print(f"Building {setup_name}.exe...")
    
    # Check if main app exists
    main_exe = os.path.join("dist", "PCFIX.exe")
    if not os.path.exists(main_exe):
        print(f"Error: {main_exe} not found. Build main app first.")
        return

    import customtkinter
    ctk_path = os.path.dirname(customtkinter.__file__)
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--uac-admin",
        "--icon", "icon.ico",
        "--name", setup_name,
        "--hidden-import", "PIL",
        "--hidden-import", "PIL.Image",
        "--collect-submodules", "customtkinter",
        "--add-data", f"{ctk_path};customtkinter",
        "--add-data", f"{main_exe};.",
        "--add-data", "icon.ico;.",
        "installer.py"
    ]
    
    subprocess.run(cmd, check=True)
    print(f"{setup_name}.exe Build complete.")

def build_tester():
    print("Building PCFIX Diagnostic Tool...")
    # Assume customtkinter is installed
    import customtkinter
    ctk_path = os.path.dirname(customtkinter.__file__)
    
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name", "PCFIX_Tester",
        "--icon", "icon.ico",
        "--hidden-import", "modules",
        "--hidden-import", "modules.core",
        "--add-data", f"{ctk_path};customtkinter",
        "--add-data", "modules;modules",
        "diagnostic_tool.py"
    ]
    
    subprocess.run(cmd, check=True)
    print("PCFIX_Tester.exe Build complete.")

if __name__ == "__main__":
    import sys
    skip_tester = "--no-tester" in sys.argv
    clean_old_builds()
    build_exe()
    build_setup()
    if not skip_tester:
        build_tester()
    
    setup_exe = f"PCFIX_Setup_{VERSION}.exe"
    portable_exe = f"PCFIX_{VERSION}.exe"
    
    if os.path.exists("dist/PCFIX.exe") and os.path.exists(f"dist/{setup_exe}"):
        # Rename PCFIX.exe to versioned name for portable distribution
        safe_move("dist/PCFIX.exe", f"dist/{portable_exe}")
        
        print(f"SUCCESS: dist/{portable_exe} and dist/{setup_exe} created.")
    else:
        print("ERROR: Build failed.")
