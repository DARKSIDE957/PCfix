import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
import threading
import time
from modules import core
from PIL import Image
import sys
import os

# pystray is loaded lazily to improve startup time

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# --- GOTHIC THEME CONFIG ---
COLOR_BG = "#050505"      # Pitch Black
COLOR_SURFACE = "#0A0A0A" # Deep Gray
COLOR_ACCENT = "#D50000"  # Blood Red
COLOR_TEXT = "#E0E0E0"    # Off-White
COLOR_DIM = "#424242"     # Dim Gray for inactive
FONT_MAIN = "Segoe UI"
FONT_MONO = "Consolas"

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue") # Placeholder, we override

class GothicButton(ctk.CTkButton):
    def __init__(self, master, text, command, **kwargs):
        kwargs.setdefault("fg_color", COLOR_SURFACE)
        kwargs.setdefault("hover_color", COLOR_ACCENT)
        kwargs.setdefault("border_color", COLOR_DIM)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("text_color", COLOR_TEXT)
        kwargs.setdefault("corner_radius", 0)
        kwargs.setdefault("font", (FONT_MAIN, 12, "bold"))
        kwargs.setdefault("height", 40)
        
        super().__init__(master, text=text, command=command, **kwargs)

class StatusCard(ctk.CTkFrame):
    def __init__(self, master, title, value_var):
        super().__init__(master, fg_color=COLOR_SURFACE, border_color=COLOR_DIM, border_width=1, corner_radius=0)
        self.title_label = ctk.CTkLabel(self, text=title, font=(FONT_MAIN, 10, "bold"), text_color=COLOR_DIM)
        self.title_label.pack(pady=(10, 0))
        self.value_label = ctk.CTkLabel(self, textvariable=value_var, font=(FONT_MONO, 24, "bold"), text_color=COLOR_ACCENT)
        self.value_label.pack(pady=(0, 10))

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Self-Elevate Check
        if not core.is_admin():
            core.elevate()

        self.title("PCFIX | NECROMANCER")
        self.geometry("900x700")
        self.resizable(False, False)
        self.configure(fg_color=COLOR_BG)
        
        # Config
        self.config = core.load_config()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        try:
            self.iconbitmap(resource_path("icon.ico"))
        except:
            pass
        
        # Variables
        self.running = True
        self.var_cpu = ctk.StringVar(value="0%")
        self.var_ram = ctk.StringVar(value="0%")
        self.var_disk = ctk.StringVar(value="0%")
        self.status_msg = ctk.StringVar(value="SYSTEM READY")

        # Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color=COLOR_SURFACE, border_color=COLOR_DIM, border_width=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        # Logo
        try:
            img_path = resource_path("icon.ico")
            self.logo_img = ctk.CTkImage(Image.open(img_path), size=(80, 80))
            self.logo = ctk.CTkLabel(self.sidebar, text="", image=self.logo_img)
        except:
            self.logo = ctk.CTkLabel(self.sidebar, text="PCFIX", font=(FONT_MAIN, 30, "bold"), text_color=COLOR_TEXT)
        self.logo.pack(pady=30)
        
        self.btn_dash = GothicButton(self.sidebar, text="DASHBOARD", command=self.show_dashboard)
        self.btn_dash.pack(fill="x", pady=2, padx=10)
        
        self.btn_clean = GothicButton(self.sidebar, text="CLEANER", command=self.show_cleaner)
        self.btn_clean.pack(fill="x", pady=2, padx=10)

        self.btn_repair = GothicButton(self.sidebar, text="REPAIR", command=self.show_repair)
        self.btn_repair.pack(fill="x", pady=2, padx=10)

        self.btn_boost = GothicButton(self.sidebar, text="BOOST", command=self.show_boost)
        self.btn_boost.pack(fill="x", pady=2, padx=10)

        self.btn_startup = GothicButton(self.sidebar, text="STARTUP MANAGER", command=self.show_startup)
        self.btn_startup.pack(fill="x", pady=2, padx=10)

        self.btn_info = GothicButton(self.sidebar, text="SPECS", command=self.show_info)
        self.btn_info.pack(fill="x", pady=2, padx=10)

        self.btn_tools = GothicButton(self.sidebar, text="TOOLS", command=self.show_tools)
        self.btn_tools.pack(fill="x", pady=2, padx=10)

        self.btn_net = GothicButton(self.sidebar, text="NETWORK", command=self.show_network)
        self.btn_net.pack(fill="x", pady=2, padx=10)

        self.btn_shred = GothicButton(self.sidebar, text="UNLOCKER", command=self.show_shredder)
        self.btn_shred.pack(fill="x", pady=2, padx=10)

        self.btn_debloat = GothicButton(self.sidebar, text="DEBLOATER", command=self.show_debloater)
        self.btn_debloat.pack(fill="x", pady=2, padx=10)

        self.btn_privacy = GothicButton(self.sidebar, text="PRIVACY", command=self.show_privacy)
        self.btn_privacy.pack(fill="x", pady=2, padx=10)

        self.btn_bsod = GothicButton(self.sidebar, text="BSOD ANALYZER", command=self.show_bsod)
        self.btn_bsod.pack(fill="x", pady=2, padx=10)

        self.btn_settings = GothicButton(self.sidebar, text="SETTINGS", command=self.show_settings)
        self.btn_settings.pack(fill="x", pady=2, padx=10)

        self.btn_about = GothicButton(self.sidebar, text="ABOUT", command=self.show_about)
        self.btn_about.pack(fill="x", pady=2, padx=10)
        
        self.btn_exit = GothicButton(self.sidebar, text="EXIT", command=self.destroy, fg_color="#1a0000", hover_color="#ff0000")
        self.btn_exit.pack(fill="x", pady=20, padx=10, side="bottom")

        # Main Area
        self.main_area = ctk.CTkFrame(self, fg_color="transparent")
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        self.show_dashboard()

        # Monitoring
        self.running = True
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()

        # Startup Sound
        core.play_startup_sound()
        
        # Start Auto RAM Optimization
        self.start_auto_ram_optimization()

    def start_auto_ram_optimization(self):
        def _auto_opt():
            while self.running:
                # Default to True now as requested
                if self.config.get("auto_ram", True):
                    res = core.optimize_ram()
                    # Optional: Update status silently or log
                time.sleep(1800) # 30 minutes
        
        threading.Thread(target=_auto_opt, daemon=True).start()

    def clear_main(self):
        for widget in self.main_area.winfo_children():
            widget.destroy()

    def show_dashboard(self):
        self.clear_main()
        
        # Header
        ctk.CTkLabel(self.main_area, text="SYSTEM METRICS", font=(FONT_MAIN, 20, "bold"), text_color=COLOR_TEXT).pack(anchor="w", pady=(0, 20))
        
        # Cards Grid
        grid = ctk.CTkFrame(self.main_area, fg_color="transparent")
        grid.pack(fill="x")
        grid.columnconfigure((0, 1, 2), weight=1)
        
        StatusCard(grid, "CPU LOAD", self.var_cpu).grid(row=0, column=0, padx=5, sticky="ew")
        StatusCard(grid, "RAM USAGE", self.var_ram).grid(row=0, column=1, padx=5, sticky="ew")
        StatusCard(grid, "DISK SPACE", self.var_disk).grid(row=0, column=2, padx=5, sticky="ew")

        # Auto RAM Status
        auto_ram_status = "ACTIVE" if self.config.get("auto_ram", True) else "DISABLED"
        color = COLOR_ACCENT if auto_ram_status == "ACTIVE" else COLOR_DIM
        ctk.CTkLabel(self.main_area, text=f"AUTO RAM OPTIMIZER: {auto_ram_status}", font=(FONT_MONO, 12), text_color=color).pack(pady=(10, 0))

        # AI Smart Scan (New Feature)
        ctk.CTkLabel(self.main_area, text="AI OPTIMIZATION", font=(FONT_MAIN, 20, "bold"), text_color=COLOR_ACCENT).pack(anchor="w", pady=(30, 10))
        
        scan_btn = GothicButton(
            self.main_area, 
            text="RUN SMART SCAN (AUTO-FIX)", 
            command=lambda: self.run_threaded(core.run_smart_scan, "RUNNING SMART SCAN..."),
            fg_color=COLOR_ACCENT,
            text_color=COLOR_BG,
            hover_color="#b71c1c"
        )
        scan_btn.pack(fill="x", pady=5)

        # Quick Actions
        ctk.CTkLabel(self.main_area, text="QUICK PROTOCOLS", font=(FONT_MAIN, 20, "bold"), text_color=COLOR_TEXT).pack(anchor="w", pady=(30, 10))

        
        actions = ctk.CTkFrame(self.main_area, fg_color="transparent")
        actions.pack(fill="x")
        
        GothicButton(actions, text="FLUSH DNS", command=self.cmd_flush_dns).pack(side="left", fill="x", expand=True, padx=5)
        GothicButton(actions, text="OPTIMIZE RAM", command=self.cmd_optimize_ram).pack(side="left", fill="x", expand=True, padx=5)

        # Status Bar
        ctk.CTkLabel(self.main_area, textvariable=self.status_msg, font=(FONT_MONO, 12), text_color=COLOR_DIM).pack(side="bottom", anchor="w")

    def show_cleaner(self):
        self.clear_main()
        ctk.CTkLabel(self.main_area, text="CLEANING PROTOCOLS", font=(FONT_MAIN, 20, "bold"), text_color=COLOR_TEXT).pack(anchor="w", pady=(0, 20))
        
        GothicButton(self.main_area, text="PURGE TEMP FILES", command=self.cmd_purge_temp).pack(fill="x", pady=5)
        GothicButton(self.main_area, text="EMPTY RECYCLE BIN", command=self.cmd_recycle_bin).pack(fill="x", pady=5)
        
        # Chrome/Edge Killer
        frame = ctk.CTkFrame(self.main_area, fg_color="transparent")
        frame.pack(fill="x", pady=20)
        ctk.CTkLabel(frame, text="PROCESS TERMINATION", font=(FONT_MAIN, 14, "bold"), text_color=COLOR_DIM).pack(anchor="w")
        
        GothicButton(frame, text="KILL CHROME", command=lambda: self.cmd_kill("chrome")).pack(fill="x", pady=2)
        GothicButton(frame, text="KILL EDGE", command=lambda: self.cmd_kill("msedge")).pack(fill="x", pady=2)

        ctk.CTkLabel(self.main_area, textvariable=self.status_msg, font=(FONT_MONO, 12), text_color=COLOR_DIM).pack(side="bottom", anchor="w")

    def show_repair(self):
        self.clear_main()
        ctk.CTkLabel(self.main_area, text="ADVANCED REPAIR", font=(FONT_MAIN, 20, "bold"), text_color=COLOR_TEXT).pack(anchor="w", pady=(0, 20))
        
        ctk.CTkLabel(self.main_area, text="WARNING: Operations may take several minutes.", font=(FONT_MAIN, 12), text_color=COLOR_ACCENT).pack(anchor="w", pady=(0, 10))

        GothicButton(self.main_area, text="SYSTEM FILE CHECK (SFC)", command=lambda: self.run_threaded(core.run_sfc, "SFC SCANNING...")).pack(fill="x", pady=5)
        GothicButton(self.main_area, text="REPAIR WINDOWS IMAGE (DISM)", command=lambda: self.run_threaded(core.run_dism, "DISM REPAIRING...")).pack(fill="x", pady=5)
        GothicButton(self.main_area, text="RESET NETWORK STACK", command=lambda: self.run_threaded(core.reset_network, "RESETTING NETWORK...")).pack(fill="x", pady=5)
        GothicButton(self.main_area, text="SCHEDULE DISK CHECK", command=lambda: self.run_threaded(core.check_disk_schedule, "SCHEDULING CHKDSK...")).pack(fill="x", pady=5)
        
        ctk.CTkLabel(self.main_area, textvariable=self.status_msg, font=(FONT_MONO, 12), text_color=COLOR_DIM).pack(side="bottom", anchor="w")

    def show_debloater(self):
        self.clear_main()
        ctk.CTkLabel(self.main_area, text="SYSTEM DEBLOATER", font=(FONT_MAIN, 20, "bold"), text_color=COLOR_TEXT).pack(anchor="w", pady=(0, 20))
        ctk.CTkLabel(self.main_area, text="REMOVE PRE-INSTALLED BLOATWARE", font=(FONT_MAIN, 14, "bold"), text_color=COLOR_DIM).pack(anchor="w", pady=(0, 10))

        # Scan Button
        scan_btn = GothicButton(self.main_area, text="SCAN FOR BLOATWARE", command=lambda: self.scan_bloatware(results_frame))
        scan_btn.pack(fill="x", pady=5)

        # Results Area
        results_frame = ctk.CTkScrollableFrame(self.main_area, fg_color="transparent", height=300, border_color=COLOR_DIM, border_width=1)
        results_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(results_frame, text="Click SCAN to detect bloatware...", font=(FONT_MONO, 12), text_color=COLOR_DIM).pack(pady=20)

        ctk.CTkLabel(self.main_area, textvariable=self.status_msg, font=(FONT_MONO, 12), text_color=COLOR_DIM).pack(side="bottom", anchor="w")

    def scan_bloatware(self, frame):
        for widget in frame.winfo_children():
            widget.destroy()
            
        self.status_msg.set("SCANNING APPS...")
        
        def _scan():
            apps = core.get_installed_bloatware()
            if not apps:
                ctk.CTkLabel(frame, text="No common bloatware detected.", font=(FONT_MONO, 12), text_color=COLOR_ACCENT).pack(pady=20)
            else:
                for app in apps:
                    row = ctk.CTkFrame(frame, fg_color=COLOR_SURFACE)
                    row.pack(fill="x", pady=2)
                    ctk.CTkLabel(row, text=app, font=(FONT_MONO, 12), text_color=COLOR_TEXT).pack(side="left", padx=10)
                    GothicButton(row, text="REMOVE", width=80, height=30, command=lambda a=app, r=row: self.remove_app(a, r)).pack(side="right", padx=10, pady=5)
            self.status_msg.set("SCAN COMPLETE")
            
        threading.Thread(target=_scan, daemon=True).start()

    def remove_app(self, app_name, row_widget):
        self.status_msg.set(f"REMOVING {app_name}...")
        def _rem():
            res = core.remove_bloatware(app_name)
            self.status_msg.set(res)
            row_widget.destroy()
        threading.Thread(target=_rem, daemon=True).start()

    def show_privacy(self):
        self.clear_main()
        ctk.CTkLabel(self.main_area, text="PRIVACY SHIELD", font=(FONT_MAIN, 20, "bold"), text_color=COLOR_TEXT).pack(anchor="w", pady=(0, 20))
        
        ctk.CTkLabel(self.main_area, text="TELEMETRY & TRACKING", font=(FONT_MAIN, 14, "bold"), text_color=COLOR_DIM).pack(anchor="w", pady=(10, 5))
        GothicButton(self.main_area, text="DISABLE WINDOWS TELEMETRY (REGISTRY)", command=lambda: self.run_threaded(core.apply_privacy_shield, "APPLYING PRIVACY SHIELD...")).pack(fill="x", pady=5)

        ctk.CTkLabel(self.main_area, text="ADVANCED TOOLS", font=(FONT_MAIN, 14, "bold"), text_color=COLOR_DIM).pack(anchor="w", pady=(20, 5))
        GothicButton(self.main_area, text="ENABLE 'GOD MODE' (DESKTOP SHORTCUT)", command=lambda: self.run_threaded(core.create_god_mode, "CREATING GOD MODE...")).pack(fill="x", pady=5)
        
        ctk.CTkLabel(self.main_area, textvariable=self.status_msg, font=(FONT_MONO, 12), text_color=COLOR_DIM).pack(side="bottom", anchor="w")

    def show_bsod(self):
        self.clear_main()
        ctk.CTkLabel(self.main_area, text="BSOD ANALYZER", font=(FONT_MAIN, 20, "bold"), text_color=COLOR_TEXT).pack(anchor="w", pady=(0, 20))
        
        # History Section
        ctk.CTkLabel(self.main_area, text="RECENT CRASH HISTORY", font=(FONT_MAIN, 14, "bold"), text_color=COLOR_DIM).pack(anchor="w", pady=(10, 5))
        
        try:
            crashes = core.get_bsod_history()
        except Exception as e:
            crashes = []
            print(f"Error fetching BSOD history: {e}")

        # Scrollable area for history
        history_frame = ctk.CTkScrollableFrame(self.main_area, fg_color="transparent", height=150, border_color=COLOR_DIM, border_width=1)
        history_frame.pack(fill="x", pady=(0, 20))
        
        if not crashes:
            ctk.CTkLabel(history_frame, text="No Recent Blue Screen Events Detected.", font=(FONT_MONO, 12), text_color=COLOR_ACCENT).pack(pady=20)
        else:
            # Header
            header = ctk.CTkFrame(history_frame, fg_color="transparent")
            header.pack(fill="x", pady=2)
            ctk.CTkLabel(header, text="DATE/TIME", font=(FONT_MAIN, 10, "bold"), text_color=COLOR_DIM, width=150, anchor="w").pack(side="left", padx=10)
            ctk.CTkLabel(header, text="ERROR CODE", font=(FONT_MAIN, 10, "bold"), text_color=COLOR_DIM, width=100, anchor="w").pack(side="left", padx=10)

            for crash in crashes:
                row = ctk.CTkFrame(history_frame, fg_color=COLOR_SURFACE)
                row.pack(fill="x", pady=2)
                
                time_str = crash.get('time', 'Unknown')
                code_str = crash.get('code', 'Unknown')
                
                ctk.CTkLabel(row, text=time_str, font=(FONT_MONO, 11), text_color=COLOR_TEXT, width=150, anchor="w").pack(side="left", padx=10)
                ctk.CTkLabel(row, text=code_str, font=(FONT_MONO, 11, "bold"), text_color=COLOR_ACCENT, width=100, anchor="w").pack(side="left", padx=10)

        # Fix Section
        ctk.CTkLabel(self.main_area, text="RECOMMENDED FIXES", font=(FONT_MAIN, 14, "bold"), text_color=COLOR_DIM).pack(anchor="w", pady=(10, 5))
        
        btn_frame = ctk.CTkFrame(self.main_area, fg_color="transparent")
        btn_frame.pack(fill="x")
        
        GothicButton(btn_frame, text="RUN MEMORY DIAGNOSTIC (RESTART)", command=lambda: self.run_threaded(core.run_memory_diagnostic, "LAUNCHING MEMORY TOOL...")).pack(fill="x", pady=5)
        GothicButton(btn_frame, text="SCAN DISK FOR ERRORS (CHKDSK)", command=lambda: self.run_threaded(core.run_chkdsk_scan, "RUNNING CHKDSK...")).pack(fill="x", pady=5)
        GothicButton(btn_frame, text="REPAIR SYSTEM FILES (SFC)", command=lambda: self.run_threaded(core.run_sfc, "SCANNING SYSTEM FILES...")).pack(fill="x", pady=5)

        ctk.CTkLabel(self.main_area, textvariable=self.status_msg, font=(FONT_MONO, 12), text_color=COLOR_DIM).pack(side="bottom", anchor="w")

    def show_settings(self):
        self.clear_main()
        ctk.CTkLabel(self.main_area, text="APPLICATION SETTINGS", font=(FONT_MAIN, 20, "bold"), text_color=COLOR_TEXT).pack(anchor="w", pady=(0, 20))

        # Sound Section
        ctk.CTkLabel(self.main_area, text="STARTUP SOUND", font=(FONT_MAIN, 14, "bold"), text_color=COLOR_DIM).pack(anchor="w", pady=(10, 5))
        
        config = core.load_config()
        current_sound = config.get("startup_sound", "")
        
        sound_frame = ctk.CTkFrame(self.main_area, fg_color="transparent")
        sound_frame.pack(fill="x", pady=5)
        
        self.lbl_sound_path = ctk.CTkLabel(sound_frame, text=current_sound if current_sound else "Default (Cyberpunk Beep)", font=(FONT_MONO, 10), text_color=COLOR_DIM, anchor="w")
        self.lbl_sound_path.pack(side="left", fill="x", expand=True)
        
        def _browse_sound():
            file_path = filedialog.askopenfilename(filetypes=[("WAV Files", "*.wav")])
            if file_path:
                self.lbl_sound_path.configure(text=file_path)
                config["startup_sound"] = file_path
                if core.save_config(config):
                    self.status_msg.set("SOUND SAVED")
                else:
                    self.status_msg.set("ERROR SAVING CONFIG")

        def _clear_sound():
            self.lbl_sound_path.configure(text="Default (Cyberpunk Beep)")
            config["startup_sound"] = ""
            core.save_config(config)
            self.status_msg.set("SOUND RESET TO DEFAULT")

        GothicButton(sound_frame, text="BROWSE...", width=100, command=_browse_sound).pack(side="right", padx=5)
        GothicButton(sound_frame, text="RESET", width=80, fg_color="#333", command=_clear_sound).pack(side="right", padx=5)
        
        GothicButton(self.main_area, text="TEST PLAY SOUND", command=core.play_startup_sound).pack(fill="x", pady=20)

        # Background Section
        ctk.CTkLabel(self.main_area, text="BACKGROUND MODE", font=(FONT_MAIN, 14, "bold"), text_color=COLOR_DIM).pack(anchor="w", pady=(20, 5))
        
        bg_frame = ctk.CTkFrame(self.main_area, fg_color="transparent")
        bg_frame.pack(fill="x", pady=5)
        
        self.var_tray = ctk.BooleanVar(value=self.config.get("minimize_to_tray", False))
        
        def _toggle_tray():
            self.config["minimize_to_tray"] = self.var_tray.get()
            if core.save_config(self.config):
                self.status_msg.set("SETTING SAVED")
            else:
                self.status_msg.set("ERROR SAVING CONFIG")
            
        ctk.CTkSwitch(bg_frame, text="MINIMIZE TO TRAY ON CLOSE", variable=self.var_tray, command=_toggle_tray, 
                      progress_color=COLOR_ACCENT, fg_color=COLOR_DIM).pack(anchor="w")

        # Auto RAM Optimize Section
        ctk.CTkLabel(self.main_area, text="AUTOMATION", font=(FONT_MAIN, 14, "bold"), text_color=COLOR_DIM).pack(anchor="w", pady=(20, 5))
        
        auto_ram_frame = ctk.CTkFrame(self.main_area, fg_color="transparent")
        auto_ram_frame.pack(fill="x", pady=5)
        
        self.var_auto_ram = ctk.BooleanVar(value=self.config.get("auto_ram", True))
        def _toggle_auto_ram():
            self.config["auto_ram"] = self.var_auto_ram.get()
            if core.save_config(self.config):
                self.status_msg.set("AUTO RAM SAVED")
            else:
                self.status_msg.set("ERROR SAVING CONFIG")
        ctk.CTkSwitch(auto_ram_frame, text="AUTO OPTIMIZE RAM (EVERY 30 MINS)", variable=self.var_auto_ram, command=_toggle_auto_ram, 
                      progress_color=COLOR_ACCENT, fg_color=COLOR_DIM).pack(anchor="w")

        ctk.CTkLabel(self.main_area, textvariable=self.status_msg, font=(FONT_MONO, 12), text_color=COLOR_DIM).pack(side="bottom", anchor="w")

    def show_about(self):
        self.clear_main()
        ctk.CTkLabel(self.main_area, text="PCFIX v3.1", font=(FONT_MAIN, 24, "bold"), text_color=COLOR_ACCENT).pack(pady=(40, 5))
        ctk.CTkLabel(self.main_area, text="NECROMANCER | ALL IN ONE EDITION", font=(FONT_MONO, 14), text_color=COLOR_DIM).pack(pady=(0, 20))
        
        # Description
        desc = ("PCFIX is the ultimate system utility designed to resurrect your PC.\n"
                "It offers advanced debloating, privacy protection, system repair, \n"
                "network optimization, and hardware diagnostics in one lightweight tool.")
        ctk.CTkLabel(self.main_area, text=desc, font=(FONT_MAIN, 12), text_color=COLOR_TEXT, justify="center").pack(pady=10)
        
        # Credits / Contact
        contact_frame = ctk.CTkFrame(self.main_area, fg_color="transparent")
        contact_frame.pack(pady=30)
        
        ctk.CTkLabel(contact_frame, text="DEVELOPER: DARKSIDE957", font=(FONT_MAIN, 14, "bold"), text_color=COLOR_TEXT).pack(pady=2)
        ctk.CTkLabel(contact_frame, text="DISCORD: _OMV", font=(FONT_MONO, 12), text_color=COLOR_ACCENT).pack(pady=2)
        
        link = "https://github.com/DARKSIDE957"
        def open_link():
            import webbrowser
            webbrowser.open(link)
            
        btn_gh = GothicButton(self.main_area, text="GITHUB: DARKSIDE957", command=open_link, width=200)
        btn_gh.pack(pady=20)
        
        ctk.CTkLabel(self.main_area, text="© 2026 DARKSIDE957. All Rights Reserved.", font=(FONT_MAIN, 10), text_color=COLOR_DIM).pack(side="bottom", pady=20)

    def show_boost(self):
        self.clear_main()
        ctk.CTkLabel(self.main_area, text="PERFORMANCE BOOST", font=(FONT_MAIN, 20, "bold"), text_color=COLOR_TEXT).pack(anchor="w", pady=(0, 20))
        
        GothicButton(self.main_area, text="ENABLE HIGH PERFORMANCE PLAN", command=lambda: self.run_threaded(core.enable_ultimate_performance, "ACTIVATING POWER PLAN...")).pack(fill="x", pady=5)
        GothicButton(self.main_area, text="DISABLE HIBERNATION", command=lambda: self.run_threaded(core.disable_hibernation, "DISABLING HIBERNATION...")).pack(fill="x", pady=5)
        GothicButton(self.main_area, text="OPTIMIZE VISUAL EFFECTS", command=lambda: self.run_threaded(core.optimize_visual_fx, "TWEAKING REGISTRY...")).pack(fill="x", pady=5)
        GothicButton(self.main_area, text="SET GPU HIGH PRIORITY (REGISTRY)", command=lambda: self.run_threaded(core.optimize_gpu_priority, "SETTING GPU PRIORITY...")).pack(fill="x", pady=5)

        
        ctk.CTkLabel(self.main_area, textvariable=self.status_msg, font=(FONT_MONO, 12), text_color=COLOR_DIM).pack(side="bottom", anchor="w")

    def monitor_loop(self):
        while self.running:
            try:
                stats = core.get_system_status()
                self.var_cpu.set(f"{stats['cpu']}%")
                self.var_ram.set(f"{stats['ram']}%")
                self.var_disk.set(f"{stats['disk']}%")
            except:
                pass
            time.sleep(2)

    def show_info(self):
        self.clear_main()
        ctk.CTkLabel(self.main_area, text="SYSTEM SPECIFICATIONS", font=(FONT_MAIN, 20, "bold"), text_color=COLOR_TEXT).pack(anchor="w", pady=(0, 20))
        
        info = core.get_detailed_info()
        
        grid = ctk.CTkFrame(self.main_area, fg_color="transparent")
        grid.pack(fill="x")
        grid.columnconfigure(1, weight=1)
        
        row = 0
        for key, label in [('os', 'OS BUILD'), ('cpu', 'PROCESSOR'), ('gpu', 'GRAPHICS'), ('ram', 'MEMORY'), ('uptime', 'UPTIME')]:
            ctk.CTkLabel(grid, text=label, font=(FONT_MAIN, 12, "bold"), text_color=COLOR_DIM).grid(row=row, column=0, sticky="nw", pady=5)
            ctk.CTkLabel(grid, text=info.get(key, "N/A"), font=(FONT_MONO, 12), text_color=COLOR_TEXT, wraplength=400, justify="left").grid(row=row, column=1, sticky="w", padx=20, pady=5)
            row += 1

        # Export Button
        GothicButton(self.main_area, text="EXPORT SPECS TO FILE", command=lambda: self.run_threaded(core.export_system_info, "EXPORTING SPECS...")).pack(fill="x", pady=20)

        ctk.CTkLabel(self.main_area, textvariable=self.status_msg, font=(FONT_MONO, 12), text_color=COLOR_DIM).pack(side="bottom", anchor="w")


    def show_tools(self):
        self.clear_main()
        ctk.CTkLabel(self.main_area, text="SYSTEM TOOLS", font=(FONT_MAIN, 20, "bold"), text_color=COLOR_TEXT).pack(anchor="w", pady=(0, 20))
        
        # DNS Switcher
        ctk.CTkLabel(self.main_area, text="DNS CONFIGURATION", font=(FONT_MAIN, 14, "bold"), text_color=COLOR_DIM).pack(anchor="w", pady=(10, 5))
        dns_frame = ctk.CTkFrame(self.main_area, fg_color="transparent")
        dns_frame.pack(fill="x")
        
        GothicButton(dns_frame, text="GOOGLE DNS", command=lambda: self.run_threaded(core.set_dns_google, "SETTING GOOGLE DNS...")).pack(side="left", fill="x", expand=True, padx=2)
        GothicButton(dns_frame, text="CLOUDFLARE", command=lambda: self.run_threaded(core.set_dns_cloudflare, "SETTING CLOUDFLARE...")).pack(side="left", fill="x", expand=True, padx=2)
        GothicButton(dns_frame, text="AUTO (ISP)", command=lambda: self.run_threaded(core.set_dns_auto, "RESETTING DNS...")).pack(side="left", fill="x", expand=True, padx=2)
        
        # Gaming Mode
        ctk.CTkLabel(self.main_area, text="GAMING OPTIMIZATION", font=(FONT_MAIN, 14, "bold"), text_color=COLOR_DIM).pack(anchor="w", pady=(20, 5))
        GothicButton(self.main_area, text="ACTIVATE GAMING MODE (KILL BG APPS)", command=lambda: self.run_threaded(core.gaming_mode_on, "KILLING BACKGROUND APPS...")).pack(fill="x", pady=5)
        
        # Quick Launchers
        ctk.CTkLabel(self.main_area, text="QUICK ACCESS", font=(FONT_MAIN, 14, "bold"), text_color=COLOR_DIM).pack(anchor="w", pady=(20, 5))
        
        tools_grid = ctk.CTkFrame(self.main_area, fg_color="transparent")
        tools_grid.pack(fill="x")
        tools_grid.columnconfigure((0, 1), weight=1)
        
        GothicButton(tools_grid, text="TASK MANAGER", command=lambda: core.launch_tool("taskmgr")).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        GothicButton(tools_grid, text="REGISTRY EDITOR", command=lambda: core.launch_tool("regedit")).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        GothicButton(tools_grid, text="DEVICE MANAGER", command=lambda: core.launch_tool("devmgmt")).grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        GothicButton(tools_grid, text="CONTROL PANEL", command=lambda: core.launch_tool("control")).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        # Reports
        ctk.CTkLabel(self.main_area, text="REPORTS", font=(FONT_MAIN, 14, "bold"), text_color=COLOR_DIM).pack(anchor="w", pady=(20, 5))
        GothicButton(self.main_area, text="GENERATE BATTERY HEALTH REPORT", command=lambda: self.run_threaded(core.generate_battery_report, "GENERATING REPORT...")).pack(fill="x", pady=5)

        
        ctk.CTkLabel(self.main_area, textvariable=self.status_msg, font=(FONT_MONO, 12), text_color=COLOR_DIM).pack(side="bottom", anchor="w")

    def show_network(self):
        self.clear_main()
        ctk.CTkLabel(self.main_area, text="NETWORK COMMANDER", font=(FONT_MAIN, 20, "bold"), text_color=COLOR_TEXT).pack(anchor="w", pady=(0, 20))
        
        self.net_info = core.get_network_info()
        self.net_hidden = True
        
        # Info Grid
        grid = ctk.CTkFrame(self.main_area, fg_color="transparent")
        grid.pack(fill="x")
        grid.columnconfigure(1, weight=1)
        
        # Interface (Always Visible)
        ctk.CTkLabel(grid, text="INTERFACE", font=(FONT_MAIN, 12, "bold"), text_color=COLOR_DIM).grid(row=0, column=0, sticky="w", pady=5)
        ctk.CTkLabel(grid, text=self.net_info.get('iface', 'N/A'), font=(FONT_MONO, 12), text_color=COLOR_TEXT).grid(row=0, column=1, sticky="w", padx=20, pady=5)
        
        self.net_labels = {}
        # Hidden Fields
        fields = [('ip', 'LOCAL IP'), ('gateway', 'GATEWAY'), ('mac', 'MAC ADDR')]
        for i, (key, label) in enumerate(fields, start=1):
            ctk.CTkLabel(grid, text=label, font=(FONT_MAIN, 12, "bold"), text_color=COLOR_DIM).grid(row=i, column=0, sticky="w", pady=5)
            lbl = ctk.CTkLabel(grid, text="* HIDDEN *", font=(FONT_MONO, 12), text_color=COLOR_TEXT)
            lbl.grid(row=i, column=1, sticky="w", padx=20, pady=5)
            self.net_labels[key] = lbl
            
        # Toggle Button
        self.btn_toggle_net = GothicButton(self.main_area, text="SHOW SENSITIVE DATA", width=150, height=25, command=self.toggle_network_details)
        self.btn_toggle_net.pack(anchor="w", pady=(10, 0))
            
        # Ping Test
        ctk.CTkLabel(self.main_area, text="LATENCY TESTS", font=(FONT_MAIN, 14, "bold"), text_color=COLOR_DIM).pack(anchor="w", pady=(20, 5))
        
        ping_frame = ctk.CTkFrame(self.main_area, fg_color="transparent")
        ping_frame.pack(fill="x")
        
        self.lbl_ping_google = ctk.CTkLabel(ping_frame, text="GOOGLE: ...", font=(FONT_MONO, 12), text_color=COLOR_TEXT)
        self.lbl_ping_google.pack(side="left", padx=(0, 20))
        
        self.lbl_ping_cf = ctk.CTkLabel(ping_frame, text="CLOUDFLARE: ...", font=(FONT_MONO, 12), text_color=COLOR_TEXT)
        self.lbl_ping_cf.pack(side="left")
        
        GothicButton(self.main_area, text="RUN PING TEST", command=self.run_ping_check).pack(fill="x", pady=10)
        
        # Reset Adapter
        ctk.CTkLabel(self.main_area, text="ADAPTER CONTROL", font=(FONT_MAIN, 14, "bold"), text_color=COLOR_DIM).pack(anchor="w", pady=(20, 5))
        GothicButton(self.main_area, text="RESET ADAPTER (RESTART WI-FI)", command=lambda: self.run_threaded(lambda: core.reset_adapter(self.net_info.get('iface', 'Wi-Fi')), "RESETTING ADAPTER...")).pack(fill="x", pady=5)
        
        ctk.CTkLabel(self.main_area, textvariable=self.status_msg, font=(FONT_MONO, 12), text_color=COLOR_DIM).pack(side="bottom", anchor="w")

    def toggle_network_details(self):
        self.net_hidden = not self.net_hidden
        
        if self.net_hidden:
            self.btn_toggle_net.configure(text="SHOW SENSITIVE DATA")
            for key, lbl in self.net_labels.items():
                lbl.configure(text="* HIDDEN *")
        else:
            self.btn_toggle_net.configure(text="HIDE SENSITIVE DATA")
            for key, lbl in self.net_labels.items():
                lbl.configure(text=self.net_info.get(key, "N/A"))

    def show_startup(self):
        self.clear_main()
        ctk.CTkLabel(self.main_area, text="STARTUP MANAGER", font=(FONT_MAIN, 20, "bold"), text_color=COLOR_TEXT).pack(anchor="w", pady=(0, 20))
        
        # Scrollable list
        scroll = ctk.CTkScrollableFrame(self.main_area, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        
        apps = core.get_startup_apps()
        
        if not apps:
            ctk.CTkLabel(scroll, text="NO STARTUP APPS FOUND", font=(FONT_MAIN, 14), text_color=COLOR_DIM).pack(pady=20)
            return

        for app in apps:
            row = ctk.CTkFrame(scroll, fg_color=COLOR_SURFACE, border_color=COLOR_DIM, border_width=1)
            row.pack(fill="x", pady=2)
            
            # Name & Location
            info_frame = ctk.CTkFrame(row, fg_color="transparent")
            info_frame.pack(side="left", padx=10, pady=5, fill="x", expand=True)
            
            name_lbl = ctk.CTkLabel(info_frame, text=app['name'], font=(FONT_MAIN, 12, "bold"), text_color=COLOR_TEXT, anchor="w")
            name_lbl.pack(fill="x")
            
            loc_lbl = ctk.CTkLabel(info_frame, text=f"{app['location']} | {app['path'][:50]}...", font=(FONT_MONO, 10), text_color=COLOR_DIM, anchor="w")
            loc_lbl.pack(fill="x")
            
            # Toggle
            is_enabled = app['enabled']
            btn_text = "DISABLE" if is_enabled else "ENABLE"
            btn_col = COLOR_ACCENT if is_enabled else "#2E7D32" # Green for enable
            
            def _toggle(a=app):
                new_state = not a['enabled']
                if core.toggle_startup_app(a, new_state):
                    self.show_startup() # Refresh
                else:
                    self.status_msg.set("ERROR TOGGLING APP")

            GothicButton(row, text=btn_text, width=80, fg_color=btn_col, command=_toggle).pack(side="right", padx=10, pady=5)

        ctk.CTkLabel(self.main_area, textvariable=self.status_msg, font=(FONT_MONO, 12), text_color=COLOR_DIM).pack(side="bottom", anchor="w")

    def show_shredder(self):
        self.clear_main()
        ctk.CTkLabel(self.main_area, text="FORCE DELETE / UNLOCKER", font=(FONT_MAIN, 20, "bold"), text_color=COLOR_TEXT).pack(anchor="w", pady=(0, 20))
        
        ctk.CTkLabel(self.main_area, text="WARNING: This tool terminates processes locking the file and permanently deletes it.", font=(FONT_MAIN, 12), text_color=COLOR_ACCENT).pack(anchor="w", pady=(0, 30))
        
        # File Selection
        frame = ctk.CTkFrame(self.main_area, fg_color=COLOR_SURFACE)
        frame.pack(fill="x", pady=20, padx=20)
        
        ctk.CTkLabel(frame, text="Select Target to Destroy", font=(FONT_MAIN, 14, "bold"), text_color=COLOR_DIM).pack(pady=(10, 5))
        
        GothicButton(frame, text="SELECT FILE", command=self.cmd_select_file).pack(fill="x", pady=10, padx=20)
        GothicButton(frame, text="SELECT FOLDER", command=self.cmd_select_folder).pack(fill="x", pady=10, padx=20)
        
        ctk.CTkLabel(self.main_area, textvariable=self.status_msg, font=(FONT_MONO, 12), text_color=COLOR_DIM).pack(side="bottom", anchor="w")

    def cmd_select_file(self):
        path = filedialog.askopenfilename()
        if path:
            self.confirm_and_destroy(path)

    def cmd_select_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.confirm_and_destroy(path)
            
    def confirm_and_destroy(self, path):
        # In a real app, we might want a confirmation dialog, but for now we proceed with status update
        self.status_msg.set(f"TARGET ACQUIRED: {path}")
        # Small delay or just run it
        self.run_threaded(lambda: core.force_delete_path(path), "INITIATING DESTRUCTION...")

    def on_close(self):
        if self.config.get("minimize_to_tray", False):
            self.withdraw()
            threading.Thread(target=self.setup_tray, daemon=True).start()
        else:
            self.quit_app()

    def quit_app(self):
        self.running = False
        self.destroy()
        sys.exit()

    def setup_tray(self):
        try:
            import pystray
            from pystray import MenuItem as item
            
            image = Image.open(resource_path("icon.ico"))
            menu = (item('Open', self.show_window), item('Exit', self.quit_app_tray))
            self.tray_icon = pystray.Icon("PCFIX", image, "PCFIX", menu)
            self.tray_icon.run()
        except Exception as e:
            self.deiconify() # Fallback if tray fails

    def show_window(self, icon, item):
        self.tray_icon.stop()
        self.after(0, self.deiconify)

    def quit_app_tray(self, icon, item):
        self.tray_icon.stop()
        self.after(0, self.quit_app)

    def run_ping_check(self):
        self.status_msg.set("PINGING...")
        def task():
            p1 = core.run_ping_test("8.8.8.8")
            self.lbl_ping_google.configure(text=f"GOOGLE: {p1}")
            p2 = core.run_ping_test("1.1.1.1")
            self.lbl_ping_cf.configure(text=f"CLOUDFLARE: {p2}")
            self.status_msg.set("PING TEST COMPLETE")
        threading.Thread(target=task, daemon=True).start()

    def monitor_loop(self):
        while self.running:
            stats = core.get_system_status()
            self.var_cpu.set(f"{stats['cpu']}%")
            self.var_ram.set(f"{stats['ram']}%")
            self.var_disk.set(f"{stats['disk']}%")
            time.sleep(1)

    def cmd_flush_dns(self):
        self.status_msg.set("FLUSHING DNS...")
        res = core.flush_dns()
        self.status_msg.set(res if res else "DNS FLUSHED")

    def cmd_optimize_ram(self):
        self.status_msg.set("OPTIMIZING RAM...")
        res = core.optimize_ram()
        self.status_msg.set(res)

    def cmd_purge_temp(self):
        self.status_msg.set("PURGING TEMP...")
        res = core.clean_temp_files()
        self.status_msg.set(res)
    
    def cmd_recycle_bin(self):
        self.status_msg.set("EMPTYING BIN...")
        res = core.empty_recycle_bin()
        self.status_msg.set(res)

    def cmd_kill(self, name):
        res = core.kill_process_by_name(name)
        self.status_msg.set(res)

    def run_threaded(self, func, start_msg):
        def task():
            self.status_msg.set(start_msg)
            try:
                res = func()
                self.status_msg.set(res[:50] + "..." if len(res) > 50 else res)
            except Exception as e:
                self.status_msg.set(f"Error: {str(e)}")
        
        threading.Thread(target=task, daemon=True).start()

if __name__ == "__main__":
    app = App()
    app.mainloop()
