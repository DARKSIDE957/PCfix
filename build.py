import os
import shutil
import subprocess
import time
import psutil

def kill_process(name):
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == name:
            try:
                proc.terminate()
                proc.wait(timeout=3)
            except:
                pass

def clean_old_builds():
    print("Cleaning old builds...")
    kill_process("PCFIX.exe")
    
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

VERSION = "v3.2"

def build_exe():
    print("Building PCFIX.exe...")
    import customtkinter
    ctk_path = os.path.dirname(customtkinter.__file__)
    
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--icon", "icon.ico",
        "--name", "PCFIX",
        "--hidden-import", "modules",
        "--hidden-import", "modules.core",
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

    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--uac-admin", # Request admin for setup
        "--icon", "icon.ico",
        "--name", setup_name,
        "--add-data", f"{main_exe};.", # Bundle the main exe
        "installer.py"
    ]
    
    subprocess.run(cmd, check=True)
    print(f"{setup_name}.exe Build complete.")

if __name__ == "__main__":
    clean_old_builds()
    build_exe()
    build_setup()
    
    setup_exe = f"PCFIX_Setup_{VERSION}.exe"
    portable_exe = f"PCFIX_{VERSION}.exe"
    
    if os.path.exists("dist/PCFIX.exe") and os.path.exists(f"dist/{setup_exe}"):
        # Rename PCFIX.exe to versioned name for portable distribution
        shutil.move("dist/PCFIX.exe", f"dist/{portable_exe}")
        
        print(f"SUCCESS: dist/{portable_exe} and dist/{setup_exe} created.")
    else:
        print("ERROR: Build failed.")
