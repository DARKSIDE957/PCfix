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
from PIL import Image
import customtkinter as ctk

# --- Configuration ---
APP_NAME = "PCFIX"
EXE_NAME = "PCFIX.exe"
DEFAULT_INSTALL_DIR = os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), APP_NAME)
APP_VERSION = "3.1"

# --- Theme Colors (Gothic/Dark/Cyberpunk) ---
COLOR_BG = "#050505"       # Deep Black
COLOR_SIDEBAR = "#0a0a0a"  # Slightly Lighter Black
COLOR_SURFACE = "#121212"  # Dark Gray
COLOR_ACCENT = "#4a00e0"   # Deep Purple/Blue Neon
COLOR_ACCENT_HOVER = "#3d00b8"
COLOR_TEXT = "#e0e0e0"     # Light Gray
COLOR_DIM = "#606060"      # Dim Gray
COLOR_SUCCESS = "#00c853"
COLOR_ERROR = "#cf0000"

FONT_MAIN = "Segoe UI"
FONT_MONO = "Consolas"
FONT_DISPLAY = "Segoe UI Display"

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
    """ Create Windows Shortcut using VBScript """
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

# --- UI Components ---

class StepIndicator(ctk.CTkFrame):
    def __init__(self, master, step_name, is_active=False):
        super().__init__(master, fg_color="transparent")
        
        color = COLOR_ACCENT if is_active else COLOR_DIM
        font_weight = "bold" if is_active else "normal"
        
        self.dot = ctk.CTkFrame(self, width=8, height=8, corner_radius=4, fg_color=color)
        self.dot.pack(side="left", padx=(0, 10))
        
        self.label = ctk.CTkLabel(self, text=step_name, font=(FONT_MAIN, 12, font_weight), text_color=color)
        self.label.pack(side="left")

    def set_active(self, is_active):
        color = COLOR_ACCENT if is_active else COLOR_DIM
        font_weight = "bold" if is_active else "normal"
        self.dot.configure(fg_color=color)
        self.label.configure(text_color=color, font=(FONT_MAIN, 12, font_weight))

class InstallerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"{APP_NAME} Installer")
        self.geometry("700x500")
        self.resizable(False, False)
        self.configure(fg_color=COLOR_BG)
        
        # Center the window
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - 700) // 2
        y = (screen_height - 500) // 2
        self.geometry(f"700x500+{x}+{y}")

        # Icon
        try:
            icon_path = resource_path("icon.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
                self.icon_image = ctk.CTkImage(Image.open(icon_path), size=(64, 64))
            else:
                self.icon_image = None
        except:
            self.icon_image = None

        self.current_step = 0
        self.steps = ["Welcome", "Options", "Install", "Finish"]
        self.setup_ui()
        self.show_step(0)

    def setup_ui(self):
        # --- Sidebar ---
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color=COLOR_SIDEBAR)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Sidebar Logo Area
        if self.icon_image:
            ctk.CTkLabel(self.sidebar, text="", image=self.icon_image).pack(pady=(40, 20))
        
        ctk.CTkLabel(self.sidebar, text=APP_NAME, font=(FONT_DISPLAY, 24, "bold"), text_color=COLOR_TEXT).pack(pady=(0, 5))
        ctk.CTkLabel(self.sidebar, text=f"v{APP_VERSION}", font=(FONT_MONO, 10), text_color=COLOR_DIM).pack(pady=(0, 40))

        # Steps Container
        self.step_indicators = []
        for step in self.steps:
            indicator = StepIndicator(self.sidebar, step.upper())
            indicator.pack(fill="x", padx=30, pady=10)
            self.step_indicators.append(indicator)

        # --- Main Content Area ---
        self.main_area = ctk.CTkFrame(self, fg_color="transparent")
        self.main_area.pack(side="right", fill="both", expand=True, padx=40, pady=40)

    def update_sidebar(self):
        for i, indicator in enumerate(self.step_indicators):
            indicator.set_active(i == self.current_step)

    def clear_main_area(self):
        for widget in self.main_area.winfo_children():
            widget.destroy()

    def show_step(self, step_index):
        self.current_step = step_index
        self.update_sidebar()
        self.clear_main_area()

        if step_index == 0:
            self.show_welcome()
        elif step_index == 1:
            self.show_options()
        elif step_index == 2:
            self.show_install()
        elif step_index == 3:
            self.show_finish()

    # --- Step 1: Welcome ---
    def show_welcome(self):
        ctk.CTkLabel(self.main_area, text="WELCOME", font=(FONT_DISPLAY, 32, "bold"), text_color=COLOR_TEXT).pack(anchor="w", pady=(20, 10))
        
        msg = (f"This wizard will guide you through the installation of {APP_NAME}.\n\n"
               "PCFIX is a high-performance system optimization tool designed to\n"
               "clean, repair, and boost your Windows experience.\n\n"
               "Click Next to continue.")
        
        ctk.CTkLabel(self.main_area, text=msg, font=(FONT_MAIN, 14), text_color=COLOR_DIM, justify="left").pack(anchor="w", pady=20)

        # Buttons
        btn_frame = ctk.CTkFrame(self.main_area, fg_color="transparent")
        btn_frame.pack(side="bottom", fill="x")
        
        ctk.CTkButton(btn_frame, text="NEXT", width=120, height=40, fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER, font=(FONT_MAIN, 12, "bold"),
                      command=lambda: self.show_step(1)).pack(side="right")

    # --- Step 2: Options ---
    def show_options(self):
        ctk.CTkLabel(self.main_area, text="CONFIGURATION", font=(FONT_DISPLAY, 32, "bold"), text_color=COLOR_TEXT).pack(anchor="w", pady=(20, 10))

        # Install Path
        ctk.CTkLabel(self.main_area, text="INSTALL LOCATION", font=(FONT_MAIN, 12, "bold"), text_color=COLOR_ACCENT).pack(anchor="w", pady=(20, 5))
        
        path_frame = ctk.CTkFrame(self.main_area, fg_color=COLOR_SURFACE)
        path_frame.pack(fill="x", pady=(0, 20))
        
        self.var_path = tk.StringVar(value=DEFAULT_INSTALL_DIR)
        self.path_entry = ctk.CTkEntry(path_frame, textvariable=self.var_path, font=(FONT_MONO, 12), border_width=0, fg_color="transparent", height=40)
        self.path_entry.pack(side="left", fill="x", expand=True, padx=10)
        
        ctk.CTkButton(path_frame, text="...", width=40, height=40, fg_color=COLOR_DIM, hover_color=COLOR_ACCENT, command=self.browse_folder).pack(side="right")

        # Shortcuts
        ctk.CTkLabel(self.main_area, text="SHORTCUTS", font=(FONT_MAIN, 12, "bold"), text_color=COLOR_ACCENT).pack(anchor="w", pady=(10, 5))
        
        self.var_desktop = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(self.main_area, text="Create Desktop Shortcut", variable=self.var_desktop, font=(FONT_MAIN, 12), 
                        fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER).pack(anchor="w", pady=5)
        
        self.var_startmenu = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(self.main_area, text="Create Start Menu Entry", variable=self.var_startmenu, font=(FONT_MAIN, 12),
                        fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER).pack(anchor="w", pady=5)

        # Buttons
        btn_frame = ctk.CTkFrame(self.main_area, fg_color="transparent")
        btn_frame.pack(side="bottom", fill="x")
        
        ctk.CTkButton(btn_frame, text="BACK", width=100, height=40, fg_color="transparent", border_width=1, border_color=COLOR_DIM, text_color=COLOR_DIM, hover_color=COLOR_SURFACE,
                      command=lambda: self.show_step(0)).pack(side="left")
        
        ctk.CTkButton(btn_frame, text="INSTALL", width=120, height=40, fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER, font=(FONT_MAIN, 12, "bold"),
                      command=lambda: self.show_step(2)).pack(side="right")

    def browse_folder(self):
        folder = filedialog.askdirectory(initialdir=os.environ.get("ProgramFiles"))
        if folder:
            if not folder.endswith(APP_NAME):
                folder = os.path.join(folder, APP_NAME)
            self.var_path.set(folder)

    # --- Step 3: Install ---
    def show_install(self):
        ctk.CTkLabel(self.main_area, text="INSTALLING", font=(FONT_DISPLAY, 32, "bold"), text_color=COLOR_TEXT).pack(anchor="w", pady=(20, 10))
        
        self.status_label = ctk.CTkLabel(self.main_area, text="Initializing...", font=(FONT_MAIN, 14), text_color=COLOR_DIM)
        self.status_label.pack(anchor="w", pady=(20, 5))
        
        self.progress = tk.DoubleVar(value=0)
        self.progress_bar = ctk.CTkProgressBar(self.main_area, variable=self.progress, height=10, progress_color=COLOR_ACCENT)
        self.progress_bar.pack(fill="x", pady=(0, 20))
        
        # Log Output
        self.log_box = ctk.CTkTextbox(self.main_area, height=150, font=(FONT_MONO, 10), fg_color=COLOR_SURFACE, text_color=COLOR_DIM)
        self.log_box.pack(fill="x")
        
        # Start installation in thread
        threading.Thread(target=self.run_installation, daemon=True).start()

    def log(self, message):
        self.log_box.insert("end", f"> {message}\n")
        self.log_box.see("end")

    def run_installation(self):
        install_dir = self.var_path.get()
        exe_source = resource_path(EXE_NAME)
        
        if not os.path.exists(exe_source):
            exe_source = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist", EXE_NAME)
            
        if not os.path.exists(exe_source):
            self.status_label.configure(text="Error: Source file missing!", text_color=COLOR_ERROR)
            self.log("CRITICAL ERROR: Source executable not found.")
            return

        try:
            # 1. Directories
            self.status_label.configure(text="Creating directories...")
            self.log(f"Creating directory: {install_dir}")
            self.progress.set(0.1)
            time.sleep(0.5)
            if not os.path.exists(install_dir):
                os.makedirs(install_dir)

            # 2. Kill Process
            self.status_label.configure(text="Stopping services...")
            self.log("Checking for running instances...")
            self.progress.set(0.3)
            subprocess.run(f'taskkill /F /IM "{EXE_NAME}"', shell=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            time.sleep(1)

            # 3. Copy
            self.status_label.configure(text="Copying files...")
            self.log(f"Copying {EXE_NAME}...")
            self.progress.set(0.5)
            target_exe = os.path.join(install_dir, EXE_NAME)
            shutil.copy2(exe_source, target_exe)
            
            # 4. Shortcuts
            self.status_label.configure(text="Creating shortcuts...")
            self.progress.set(0.7)
            
            if self.var_desktop.get():
                self.log("Creating Desktop shortcut...")
                desktop = os.path.join(os.environ["PUBLIC"], "Desktop")
                if not os.path.exists(desktop): desktop = os.path.join(os.environ["USERPROFILE"], "Desktop")
                create_shortcut_vbs(target_exe, os.path.join(desktop, f"{APP_NAME}.lnk"), "PCFIX System Optimizer")

            if self.var_startmenu.get():
                self.log("Creating Start Menu entry...")
                start_menu = os.path.join(os.environ["ProgramData"], r"Microsoft\Windows\Start Menu\Programs")
                if not os.path.exists(start_menu): os.makedirs(start_menu)
                create_shortcut_vbs(target_exe, os.path.join(start_menu, f"{APP_NAME}.lnk"), "PCFIX System Optimizer")

            # 5. Registry
            self.log("Updating Registry...")
            try:
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\PCFIX")
                winreg.SetValueEx(key, "InstallPath", 0, winreg.REG_SZ, install_dir)
                winreg.SetValueEx(key, "Version", 0, winreg.REG_SZ, APP_VERSION)
                winreg.CloseKey(key)
            except Exception as e:
                self.log(f"Registry Warning: {e}")

            self.progress.set(1.0)
            self.status_label.configure(text="Installation Complete", text_color=COLOR_SUCCESS)
            self.log("Done.")
            time.sleep(1)
            
            self.after(0, lambda: self.show_step(3))

        except Exception as e:
            self.status_label.configure(text="Installation Failed", text_color=COLOR_ERROR)
            self.log(f"ERROR: {str(e)}")

    # --- Step 4: Finish ---
    def show_finish(self):
        ctk.CTkLabel(self.main_area, text="COMPLETE", font=(FONT_DISPLAY, 32, "bold"), text_color=COLOR_SUCCESS).pack(anchor="w", pady=(20, 10))
        
        ctk.CTkLabel(self.main_area, text=f"{APP_NAME} has been successfully installed.", font=(FONT_MAIN, 14), text_color=COLOR_TEXT).pack(anchor="w", pady=(0, 20))
        
        self.var_launch = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(self.main_area, text=f"Launch {APP_NAME} now", variable=self.var_launch, font=(FONT_MAIN, 12),
                        fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER).pack(anchor="w", pady=20)
        
        # Buttons
        btn_frame = ctk.CTkFrame(self.main_area, fg_color="transparent")
        btn_frame.pack(side="bottom", fill="x")
        
        ctk.CTkButton(btn_frame, text="FINISH", width=120, height=40, fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER, font=(FONT_MAIN, 12, "bold"),
                      command=self.finish_install).pack(side="right")

    def finish_install(self):
        if self.var_launch.get():
            install_dir = self.var_path.get()
            target_exe = os.path.join(install_dir, EXE_NAME)
            try:
                subprocess.Popen([target_exe], shell=True, close_fds=True, creationflags=subprocess.DETACHED_PROCESS)
            except Exception as e:
                tk.messagebox.showerror("Error", f"Failed to launch: {e}")
        self.quit()

if __name__ == "__main__":
    if not is_admin():
        run_as_admin()
    else:
        app = InstallerApp()
        app.mainloop()

