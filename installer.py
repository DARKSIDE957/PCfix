import os
import sys
import shutil
import ctypes
import subprocess
import time
import threading
import tkinter as tk
import winreg
from tkinter import filedialog
import customtkinter as ctk

# --- Configuration ---
APP_NAME = "PCFIX"
EXE_NAME = "PCFIX.exe"
DEFAULT_INSTALL_DIR = os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), APP_NAME)
APP_VERSION = "3.1"

# --- Theme Colors (Gothic/Dark) ---
COLOR_BG = "#050505"       # Deep Black
COLOR_SURFACE = "#121212"  # Dark Gray
COLOR_ACCENT = "#4a00e0"   # Deep Purple/Blue Neon (matches main app vibe)
COLOR_TEXT = "#e0e0e0"     # Light Gray
COLOR_DIM = "#606060"      # Dim Gray
FONT_MAIN = "Segoe UI"
FONT_MONO = "Consolas"

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

# --- Helper Functions ---

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def create_shortcut_vbs(target_path, shortcut_path, description):
    """ Create Windows Shortcut using VBScript (more reliable than PowerShell in some restricted envs) """
    try:
        vbs_script = os.path.join(os.environ["TEMP"], f"create_shortcut_{int(time.time())}.vbs")
        with open(vbs_script, "w") as f:
            f.write('Set oWS = WScript.CreateObject("WScript.Shell")\n')
            f.write(f'sLinkFile = "{shortcut_path}"\n')
            f.write('Set oLink = oWS.CreateShortcut(sLinkFile)\n')
            f.write(f'oLink.TargetPath = "{target_path}"\n')
            f.write(f'oLink.Description = "{description}"\n')
            f.write('oLink.Save\n')
        
        subprocess.run(["cscript", "//Nologo", vbs_script], check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        os.remove(vbs_script)
        return True
    except Exception as e:
        print(f"Shortcut error: {e}")
        return False

# --- UI Class ---

class InstallerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"{APP_NAME} Installer")
        self.geometry("600x450")
        self.resizable(False, False)
        self.configure(fg_color=COLOR_BG)
        
        # Center the window
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - 600) // 2
        y = (screen_height - 450) // 2
        self.geometry(f"600x450+{x}+{y}")

        # Icon
        try:
            icon_path = resource_path("icon.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except:
            pass

        self.setup_ui()

    def setup_ui(self):
        # Check Existing Install
        self.check_existing_install()

        # Header
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(pady=(30, 20))

        ctk.CTkLabel(
            self.header_frame, 
            text=f"INSTALL {APP_NAME}", 
            font=(FONT_MAIN, 28, "bold"), 
            text_color=COLOR_TEXT
        ).pack()
        
        ctk.CTkLabel(
            self.header_frame, 
            text="High-Performance System Optimization Tool", 
            font=(FONT_MAIN, 12), 
            text_color=COLOR_DIM
        ).pack()

        # Install Location
        self.loc_frame = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, corner_radius=10)
        self.loc_frame.pack(fill="x", padx=40, pady=20)
        
        ctk.CTkLabel(
            self.loc_frame, 
            text="INSTALLATION FOLDER", 
            font=(FONT_MAIN, 10, "bold"), 
            text_color=COLOR_DIM
        ).pack(anchor="w", padx=15, pady=(15, 5))

        self.var_path = tk.StringVar(value=DEFAULT_INSTALL_DIR)
        self.path_entry = ctk.CTkEntry(
            self.loc_frame, 
            width=350, 
            height=35,
            font=(FONT_MONO, 12),
            fg_color=COLOR_BG, 
            border_color=COLOR_DIM,
            text_color=COLOR_TEXT,
            textvariable=self.var_path
        )
        self.path_entry.pack(side="left", padx=(15, 10), pady=(0, 15), fill="x", expand=True)

        self.browse_btn = ctk.CTkButton(
            self.loc_frame, 
            text="BROWSE", 
            width=80, 
            height=35,
            fg_color=COLOR_SURFACE, 
            border_color=COLOR_ACCENT, 
            border_width=1,
            text_color=COLOR_ACCENT,
            hover_color=COLOR_BG,
            command=self.browse_folder
        )
        self.browse_btn.pack(side="right", padx=(0, 15), pady=(0, 15))

        # Progress
        self.progress = tk.DoubleVar()
        self.progress_bar = ctk.CTkProgressBar(self, width=520, height=10, progress_color=COLOR_ACCENT, variable=self.progress)
        self.progress_bar.pack(pady=(20, 10))
        
        self.status_label = ctk.CTkLabel(
            self, 
            text="Ready to Install", 
            font=(FONT_MAIN, 12), 
            text_color=COLOR_DIM
        )
        self.status_label.pack(pady=(0, 20))

        # Actions
        self.action_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_frame.pack(side="bottom", pady=30)

        self.install_btn = ctk.CTkButton(
            self.action_frame, 
            text="INSTALL NOW", 
            width=200, 
            height=45,
            font=(FONT_MAIN, 14, "bold"),
            fg_color=COLOR_ACCENT,
            hover_color="#3a00b0",
            command=self.start_install_thread
        )
        self.install_btn.pack()

    def launch(self, exe_path):
        try:
            subprocess.Popen(exe_path)
            sys.exit()
        except Exception as e:
            tk.messagebox.showerror("Error", f"Failed to launch: {e}")

    def check_existing_install(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\PCFIX", 0, winreg.KEY_READ)
            path, _ = winreg.QueryValueEx(key, "InstallPath")
            ver, _ = winreg.QueryValueEx(key, "Version")
            winreg.CloseKey(key)

            if path and os.path.exists(path) and ver == APP_VERSION:
                tk.messagebox.showinfo("Installer", f"PCFIX is already installed at:\n{path}\n\nVersion {ver} is up to date.\nYou don't need to install it again.")
                sys.exit()
        except:
            pass
            
    def browse_folder(self):
        folder = filedialog.askdirectory(initialdir=os.environ.get("ProgramFiles"))
        if folder:
            # Append app name if not present
            if not folder.endswith(APP_NAME):
                folder = os.path.join(folder, APP_NAME)
            
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, folder)

    def start_install_thread(self):
        self.install_btn.configure(state="disabled", text="INSTALLING...")
        self.browse_btn.configure(state="disabled")
        self.path_entry.configure(state="disabled")
        
        thread = threading.Thread(target=self.run_installation, daemon=True)
        thread.start()

    def update_status(self, text, progress):
        self.status_label.configure(text=text)
        self.progress_bar.set(progress)
        self.update_idletasks()

    def run_installation(self):
        install_dir = self.path_entry.get()
        exe_source = resource_path(EXE_NAME)
        
        # Check source
        if not os.path.exists(exe_source):
            # Fallback for dev environment
            exe_source = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist", EXE_NAME)
            
        if not os.path.exists(exe_source):
            self.update_status("Error: Source file not found!", 0)
            self.install_btn.configure(text="FAILED", fg_color="#cf0000")
            return

        try:
            # 1. Create Directory
            self.update_status("Creating directories...", 0.2)
            time.sleep(0.5)
            if not os.path.exists(install_dir):
                os.makedirs(install_dir)

            # 2. Kill existing process
            self.update_status("Stopping running instances...", 0.4)
            subprocess.run(f'taskkill /F /IM "{EXE_NAME}"', shell=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            time.sleep(1)

            # 3. Copy Files
            self.update_status("Copying application files...", 0.6)
            target_exe = os.path.join(install_dir, EXE_NAME)
            shutil.copy2(exe_source, target_exe)
            
            # Copy uninstaller/maintenance tools if any (none for now)

            # 4. Create Shortcuts
            self.update_status("Creating shortcuts...", 0.8)
            
            # Desktop
            desktop = os.path.join(os.environ["PUBLIC"], "Desktop")
            if not os.path.exists(desktop):
                desktop = os.path.join(os.environ["USERPROFILE"], "Desktop")
            
            create_shortcut_vbs(target_exe, os.path.join(desktop, f"{APP_NAME}.lnk"), "PCFIX System Optimizer")

            # Start Menu
            start_menu = os.path.join(os.environ["ProgramData"], r"Microsoft\Windows\Start Menu\Programs")
            if not os.path.exists(start_menu):
                os.makedirs(start_menu)
            
            create_shortcut_vbs(target_exe, os.path.join(start_menu, f"{APP_NAME}.lnk"), "PCFIX System Optimizer")

            # 5. Registry Entry
            try:
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\PCFIX")
                winreg.SetValueEx(key, "InstallPath", 0, winreg.REG_SZ, install_dir)
                winreg.SetValueEx(key, "Version", 0, winreg.REG_SZ, APP_VERSION)
                winreg.CloseKey(key)
            except Exception as e:
                print(f"Reg Error: {e}")

            # 6. Finish
            self.update_status("Installation Complete!", 1.0)
            time.sleep(0.5)
            self.installation_complete(target_exe)

        except Exception as e:
            self.update_status(f"Error: {str(e)}", 0)
            self.install_btn.configure(text="ERROR", fg_color="#cf0000")

    def installation_complete(self, target_exe):
        self.install_btn.configure(
            text="LAUNCH PCFIX", 
            state="normal", 
            fg_color="#00c853", 
            hover_color="#009624",
            command=lambda: self.launch_app(target_exe)
        )
        self.browse_btn.configure(state="disabled")

    def launch_app(self, path):
        try:
            subprocess.Popen([path], shell=True, close_fds=True, creationflags=subprocess.DETACHED_PROCESS)
            self.quit()
        except Exception as e:
            self.status_label.configure(text=f"Launch Error: {e}")

if __name__ == "__main__":
    if not is_admin():
        run_as_admin()
    else:
        app = InstallerApp()
        app.mainloop()
