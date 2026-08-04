import os
import shutil
import subprocess
import time
import zipfile

try:
    import psutil
except ImportError:
    psutil = None

VERSION = "v4.0"
APP_DIR_NAME = "PCFIX"


def kill_process(name):
    if psutil is None:
        return
    for proc in psutil.process_iter(["pid", "name"]):
        if proc.info["name"] == name:
            try:
                proc.terminate()
                proc.wait(timeout=3)
            except Exception:
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


def clean_old_builds():
    print("Cleaning old builds...")
    kill_process("PCFIX.exe")
    kill_process("PCFIX_v3.8.exe")
    kill_process("PCFIX_v3.9.exe")
    kill_process("PCFIX_v3.10.exe")
    kill_process("PCFIX_v4.0.exe")
    kill_process(f"PCFIX_Setup_{VERSION}.exe")

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
    for name in ("PCFIX.spec", "PCFIX_Setup.spec", f"PCFIX_Setup_{VERSION}.spec"):
        if os.path.exists(name):
            os.remove(name)
    for f in os.listdir("."):
        if f.startswith("PCFIX_Setup_") and f.endswith(".spec"):
            os.remove(f)
    print("Cleaned.")


def rebuild_bootloader():
    """Rebuild PyInstaller bootloader from source for a unique binary fingerprint."""
    print("Rebuilding PyInstaller bootloader from source...")
    env = os.environ.copy()
    env["PYINSTALLER_COMPILE_BOOTLOADER"] = "1"
    try:
        subprocess.run(
            ["python", "-m", "pip", "install", "--force-reinstall", "--no-binary=pyinstaller", "pyinstaller"],
            check=True,
            env=env,
        )
        print("Bootloader rebuild complete.")
    except Exception as e:
        print(f"Bootloader rebuild skipped or failed ({e}). Continuing with installed PyInstaller.")


def _common_flags(name):
    import customtkinter
    ctk_path = os.path.dirname(customtkinter.__file__)
    return [
        "pyinstaller",
        "--noconfirm",
        "--windowed",
        "--noupx",
        "--uac-admin",
        "--icon", "icon.ico",
        "--name", name,
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
    ]


def build_exe():
    print("Building PCFIX (onedir)...")
    cmd = _common_flags(APP_DIR_NAME) + ["--onedir", "main.py"]
    subprocess.run(cmd, check=True)
    print("PCFIX onedir build complete.")


def zip_portable():
    app_dir = os.path.join("dist", APP_DIR_NAME)
    zip_path = os.path.join("dist", f"PCFIX_{VERSION}_Portable.zip")
    if not os.path.isdir(app_dir):
        print(f"Error: {app_dir} not found.")
        return False
    if os.path.exists(zip_path):
        safe_remove(zip_path)
    print(f"Creating {zip_path}...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _dirs, files in os.walk(app_dir):
            for file in files:
                full = os.path.join(root, file)
                arc = os.path.join(APP_DIR_NAME, os.path.relpath(full, app_dir))
                zf.write(full, arcname=arc)
    print(f"Portable zip ready: {zip_path}")
    return True


def build_setup():
    setup_name = f"PCFIX_Setup_{VERSION}"
    print(f"Building {setup_name}.exe...")
    app_dir = os.path.join("dist", APP_DIR_NAME)
    if not os.path.isdir(app_dir):
        print(f"Error: {app_dir} not found. Build main app first.")
        return

    import customtkinter
    ctk_path = os.path.dirname(customtkinter.__file__)
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--noupx",
        "--uac-admin",
        "--icon", "icon.ico",
        "--name", setup_name,
        "--hidden-import", "PIL",
        "--hidden-import", "PIL.Image",
        "--collect-submodules", "customtkinter",
        "--add-data", f"{ctk_path};customtkinter",
        "--add-data", f"{app_dir};{APP_DIR_NAME}",
        "--add-data", "icon.ico;.",
        "installer.py",
    ]
    subprocess.run(cmd, check=True)
    print(f"{setup_name}.exe Build complete.")


def build_tester():
    print("Building PCFIX Diagnostic Tool...")
    import customtkinter
    ctk_path = os.path.dirname(customtkinter.__file__)
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--noupx",
        "--windowed",
        "--name", "PCFIX_Tester",
        "--icon", "icon.ico",
        "--hidden-import", "modules",
        "--hidden-import", "modules.core",
        "--add-data", f"{ctk_path};customtkinter",
        "--add-data", "modules;modules",
        "diagnostic_tool.py",
    ]
    subprocess.run(cmd, check=True)
    print("PCFIX_Tester.exe Build complete.")


if __name__ == "__main__":
    import sys
    skip_tester = "--no-tester" in sys.argv
    skip_bootloader = "--skip-bootloader" in sys.argv
    clean_old_builds()
    if not skip_bootloader:
        rebuild_bootloader()
    build_exe()
    zip_ok = zip_portable()
    build_setup()
    if not skip_tester:
        build_tester()

    setup_exe = os.path.join("dist", f"PCFIX_Setup_{VERSION}.exe")
    portable_zip = os.path.join("dist", f"PCFIX_{VERSION}_Portable.zip")
    if os.path.isdir(os.path.join("dist", APP_DIR_NAME)) and os.path.exists(setup_exe) and zip_ok:
        print(f"SUCCESS: {portable_zip} and {setup_exe} created.")
    else:
        print("ERROR: Build failed.")
