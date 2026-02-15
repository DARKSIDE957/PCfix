import customtkinter as ctk
import os
import sys
import threading
import time
import subprocess
import psutil
import hashlib
from modules import core

# --- Configuration ---
APP_NAME = "PCFIX DIAGNOSTIC TOOL"
VERSION = "v1.0"
TARGET_VERSION = "3.7"
DIST_DIR = "dist"
APP_EXE = f"PCFIX_{VERSION.replace('v', '')}.exe" if 'v' in VERSION else "PCFIX_v3.7.exe" # Fallback logic, will refine
APP_EXE_NAME = "PCFIX_v3.7.exe"
SETUP_EXE_NAME = "PCFIX_Setup_v3.7.exe"

# Colors
COLOR_BG = "#050505"
COLOR_SURFACE = "#121212"
COLOR_ACCENT = "#d00000" # Red for diagnostic
COLOR_TEXT = "#e0e0e0"
COLOR_SUCCESS = "#00c853"
COLOR_WARN = "#ffd600"
COLOR_ERROR = "#cf0000"

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class DiagnosticApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("700x500")
        self.configure(fg_color=COLOR_BG)
        
        # Header
        self.header = ctk.CTkLabel(self, text=f"{APP_NAME} {VERSION}", font=("Segoe UI", 24, "bold"), text_color=COLOR_ACCENT)
        self.header.pack(pady=20)
        
        self.sub_header = ctk.CTkLabel(self, text="DEEP SYSTEM & INTEGRITY CHECK", font=("Consolas", 12), text_color=COLOR_TEXT)
        self.sub_header.pack(pady=(0, 20))

        # Log Area
        self.log_frame = ctk.CTkScrollableFrame(self, fg_color=COLOR_SURFACE, height=300, width=650)
        self.log_frame.pack(pady=10)
        
        # Actions
        self.btn_run = ctk.CTkButton(self, text="INITIATE DEEP SCAN", font=("Segoe UI", 14, "bold"), 
                                     fg_color=COLOR_ACCENT, hover_color="#b00000", height=40, width=200,
                                     command=self.start_scan)
        self.btn_run.pack(pady=20)
        
        self.running = False

    def log(self, message, status="INFO"):
        color = COLOR_TEXT
        if status == "PASS": color = COLOR_SUCCESS
        elif status == "FAIL": color = COLOR_ERROR
        elif status == "WARN": color = COLOR_WARN
        elif status == "HEADER": 
            color = COLOR_ACCENT
            message = f"\n[{message}]"

        lbl = ctk.CTkLabel(self.log_frame, text=f"{time.strftime('%H:%M:%S')} | {message}", 
                           font=("Consolas", 11), text_color=color, anchor="w")
        lbl.pack(fill="x", padx=5, pady=1)
        self.log_frame._parent_canvas.yview_moveto(1.0)
        self.update()

    def start_scan(self):
        if self.running: return
        self.running = True
        self.btn_run.configure(state="disabled", text="SCANNING...")
        
        # Run in thread
        threading.Thread(target=self.run_diagnostics, daemon=True).start()

    def run_diagnostics(self):
        try:
            self.log("STARTING DIAGNOSTIC PROTOCOL...", "HEADER")
            time.sleep(1)
            
            # 1. Environment Check
            self.log("CHECKING ENVIRONMENT...", "HEADER")
            self.log(f"OS: {os.name} | Platform: {sys.platform}")
            try:
                stats = core.get_system_status()
                self.log(f"Core Logic Check: PASS (CPU: {stats['cpu']}%, RAM: {stats['ram']}%)", "PASS")
            except Exception as e:
                self.log(f"Core Logic Check: FAIL ({e})", "FAIL")

            # 2. Dist File Check
            self.log("VERIFYING BUILD ARTIFACTS...", "HEADER")
            cwd = os.getcwd()
            dist_path = os.path.join(cwd, "dist")
            
            # Verify Main App
            app_path = os.path.join(dist_path, APP_EXE_NAME)
            if os.path.exists(app_path):
                size = os.path.getsize(app_path) / (1024*1024)
                self.log(f"Found {APP_EXE_NAME}: {size:.2f} MB", "PASS")
            else:
                self.log(f"Missing {APP_EXE_NAME}", "FAIL")
                
            # Verify Setup
            setup_path = os.path.join(dist_path, SETUP_EXE_NAME)
            if os.path.exists(setup_path):
                size = os.path.getsize(setup_path) / (1024*1024)
                self.log(f"Found {SETUP_EXE_NAME}: {size:.2f} MB", "PASS")
            else:
                self.log(f"Missing {SETUP_EXE_NAME}", "FAIL")

            # 3. Functional Test (BSOD)
            self.log("TESTING INTERNAL MODULES...", "HEADER")
            try:
                crashes = core.get_bsod_history()
                self.log(f"BSOD Module: PASS ({len(crashes)} events found)", "PASS")
            except Exception as e:
                self.log(f"BSOD Module: FAIL ({e})", "FAIL")

            # 4. Live App Test
            self.log("LIVE APP EXECUTION TEST...", "HEADER")
            if os.path.exists(app_path):
                self.log(f"Launching {APP_EXE_NAME} for stability check...")
                try:
                    proc = subprocess.Popen([app_path], cwd=dist_path)
                    pid = proc.pid
                    self.log(f"Process started (PID: {pid})")
                    
                    # Monitor for 5 seconds
                    for i in range(5):
                        if proc.poll() is not None:
                            self.log(f"Process exited prematurely with code {proc.returncode}", "FAIL")
                            break
                        time.sleep(1)
                    
                    if proc.poll() is None:
                        self.log("Process stable after 5 seconds.", "PASS")
                        self.log("Closing test instance...")
                        proc.terminate()
                        try:
                            proc.wait(timeout=2)
                        except:
                            proc.kill()
                    
                except Exception as e:
                    self.log(f"Execution Failed: {e}", "FAIL")
            else:
                self.log("Skipping Live Test (Executable not found)", "WARN")

            self.log("DIAGNOSTIC COMPLETE.", "HEADER")
            
        except Exception as e:
            self.log(f"CRITICAL ERROR: {e}", "FAIL")
        
        self.running = False
        self.btn_run.configure(state="normal", text="RUN DEEP DIAGNOSTIC")

if __name__ == "__main__":
    app = DiagnosticApp()
    app.mainloop()
