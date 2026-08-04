import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import threading
import time
import queue
import traceback
import uuid
import concurrent.futures
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

# --- NECROMANCER v4.0 — OLED Crimson ---
APP_VERSION = "v4.0"
COLOR_BG = "#000000"
COLOR_SURFACE = "#0c0c0e"
COLOR_ELEVATED = "#141416"
COLOR_ACCENT = "#e11d48"
COLOR_ACCENT_HOVER = "#f43f5e"
COLOR_ACCENT_DIM = "#9f1239"
COLOR_TEXT = "#f4f4f5"
COLOR_DIM = "#71717a"
COLOR_MUTED = "#a1a1aa"
COLOR_BORDER = "#1f1f23"
COLOR_GOOD = "#22c55e"
COLOR_WARN = "#f59e0b"

FONT_MAIN = "Segoe UI"
FONT_DISPLAY = "Segoe UI Semibold"
FONT_MONO = "Consolas"

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class GothicButton(ctk.CTkButton):
    def __init__(self, master, text, command, **kwargs):
        kwargs.setdefault("fg_color", COLOR_ELEVATED)
        kwargs.setdefault("hover_color", "#1c1c20")
        kwargs.setdefault("border_color", COLOR_BORDER)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("text_color", COLOR_TEXT)
        kwargs.setdefault("corner_radius", 8)
        kwargs.setdefault("font", (FONT_MAIN, 12, "bold"))
        kwargs.setdefault("height", 42)
        super().__init__(master, text=text, command=command, **kwargs)

class AccentButton(ctk.CTkButton):
    def __init__(self, master, text, command, **kwargs):
        kwargs.setdefault("fg_color", COLOR_ACCENT)
        kwargs.setdefault("hover_color", COLOR_ACCENT_HOVER)
        kwargs.setdefault("text_color", "#ffffff")
        kwargs.setdefault("corner_radius", 8)
        kwargs.setdefault("font", (FONT_MAIN, 13, "bold"))
        kwargs.setdefault("height", 48)
        kwargs.setdefault("border_width", 0)
        super().__init__(master, text=text, command=command, **kwargs)

class StatusCard(ctk.CTkFrame):
    def __init__(self, master, title, value_var, icon=""):
        super().__init__(master, fg_color=COLOR_SURFACE, border_color=COLOR_BORDER, border_width=1, corner_radius=12)
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=16)

        head = ctk.CTkFrame(inner, fg_color="transparent")
        head.pack(fill="x")
        if icon:
            ctk.CTkLabel(head, text=icon, font=(FONT_MAIN, 14), text_color=COLOR_ACCENT).pack(side="left", padx=(0, 6))
        ctk.CTkLabel(head, text=title, font=(FONT_MAIN, 11, "bold"), text_color=COLOR_DIM).pack(side="left")

        self.value_label = ctk.CTkLabel(inner, textvariable=value_var, font=(FONT_MONO, 30, "bold"), text_color=COLOR_TEXT)
        self.value_label.pack(anchor="w", pady=(10, 8))

        self.bar = ctk.CTkProgressBar(inner, height=4, corner_radius=2, progress_color=COLOR_ACCENT, fg_color=COLOR_BORDER)
        self.bar.pack(fill="x")
        self.bar.set(0)
        self._value_var = value_var
        self._tick()

    def _tick(self):
        try:
            raw = self._value_var.get().replace("%", "").strip()
            for ch in ("⚡", "🔋", " "):
                raw = raw.replace(ch, "")
            pct = max(0.0, min(1.0, float(raw) / 100.0)) if raw.replace(".", "", 1).isdigit() else 0.0
            self.bar.set(pct)
            self.bar.configure(progress_color=COLOR_ACCENT if pct < 0.85 else COLOR_WARN)
        except Exception:
            pass
        try:
            self.after(800, self._tick)
        except Exception:
            pass

class SectionLabel(ctk.CTkLabel):
    def __init__(self, master, text, **kwargs):
        kwargs.setdefault("font", (FONT_MAIN, 11, "bold"))
        kwargs.setdefault("text_color", COLOR_DIM)
        kwargs.setdefault("anchor", "w")
        super().__init__(master, text=text.upper(), **kwargs)

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Self-Elevate Check
        if not core.is_admin():
            core.elevate()

        self.title(f"PCFIX | NECROMANCER {APP_VERSION}")
        self.geometry("1280x860")
        self.minsize(1000, 700)
        self.resizable(True, True)
        self.configure(fg_color=COLOR_BG)

        self.config = core.load_config()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        try:
            self.iconbitmap(resource_path("icon.ico"))
        except Exception:
            pass

        self.running = True
        self.var_cpu = ctk.StringVar(value="0%")
        self.var_ram = ctk.StringVar(value="0%")
        self.var_disk = ctk.StringVar(value="0%")
        self.var_battery = ctk.StringVar(value="N/A")
        self.status_msg = ctk.StringVar(value="SYSTEM READY")
        self._ui_queue = queue.Queue()
        self._log_file = self._resolve_log_file()
        self._log("APP_START")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar shell
        self.sidebar = ctk.CTkFrame(self, width=248, corner_radius=0, fg_color=COLOR_SURFACE)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        ctk.CTkFrame(self.sidebar, width=1, fg_color=COLOR_BORDER).pack(side="right", fill="y")

        brand = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand.pack(fill="x", padx=18, pady=(22, 8))
        try:
            self.logo_img = ctk.CTkImage(Image.open(resource_path("icon.ico")), size=(42, 42))
            ctk.CTkLabel(brand, text="  PCFIX", image=self.logo_img, compound="left",
                         font=(FONT_DISPLAY, 22, "bold"), text_color=COLOR_TEXT).pack(anchor="w")
        except Exception:
            ctk.CTkLabel(brand, text="PCFIX", font=(FONT_DISPLAY, 24, "bold"), text_color=COLOR_TEXT).pack(anchor="w")
        ctk.CTkLabel(brand, text=f"NECROMANCER  ·  {APP_VERSION}", font=(FONT_MONO, 10),
                     text_color=COLOR_ACCENT).pack(anchor="w", pady=(6, 0))

        self.nav_scroll = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent",
                                                 scrollbar_button_color=COLOR_BORDER,
                                                 scrollbar_button_hover_color=COLOR_ELEVATED)
        self.nav_scroll.pack(fill="both", expand=True, padx=8, pady=(4, 0))
        self.nav_frame = self.nav_scroll

        self._nav_buttons = {}
        self._nav_accents = {}
        self._active_nav = None

        nav_groups = [
            ("Overview", [
                ("Dashboard", self.show_dashboard, "dashboard"),
                ("Specs", self.show_info, "specs"),
            ]),
            ("Maintain", [
                ("Cleaner", self.show_cleaner, "cleaner"),
                ("Repair", self.show_repair, "repair"),
                ("Debloater", self.show_debloater, "debloater"),
                ("Unlocker", self.show_shredder, "unlocker"),
                ("Force Remove", self.show_force_remove_app, "force_remove"),
            ]),
            ("Tune", [
                ("Boost", self.show_boost, "boost"),
                ("Tweaks", self.show_tweaks, "tweaks"),
                ("Startup", self.show_startup, "startup"),
                ("Privacy", self.show_privacy, "privacy"),
            ]),
            ("Network", [
                ("Network", self.show_network, "network"),
                ("Tools", self.show_tools, "tools"),
            ]),
            ("Diagnose", [
                ("BSOD Analyzer", self.show_bsod, "bsod"),
            ]),
            ("App", [
                ("Settings", self.show_settings, "settings"),
                ("About", self.show_about, "about"),
            ]),
        ]
        for group_name, items in nav_groups:
            SectionLabel(self.nav_frame, group_name).pack(anchor="w", padx=10, pady=(14, 4))
            for label, cmd, nav_id in items:
                self.create_nav_btn(label, cmd, nav_id)

        GothicButton(
            self.sidebar, text="Exit", command=self.destroy,
            fg_color="#1a0508", hover_color=COLOR_ACCENT_DIM, border_color=COLOR_ACCENT_DIM, height=38
        ).pack(fill="x", pady=14, padx=12, side="bottom")

        self.main_shell = ctk.CTkFrame(self, fg_color="transparent")
        self.main_shell.grid(row=0, column=1, sticky="nsew")
        self.main_shell.grid_columnconfigure(0, weight=1)
        self.main_shell.grid_rowconfigure(0, weight=1)

        self.main_area = ctk.CTkFrame(self.main_shell, fg_color="transparent")
        self.main_area.grid(row=0, column=0, sticky="nsew", padx=28, pady=(24, 8))

        self.status_bar = ctk.CTkFrame(self.main_shell, fg_color=COLOR_SURFACE, height=36, corner_radius=0)
        self.status_bar.grid(row=1, column=0, sticky="ew")
        ctk.CTkFrame(self.status_bar, height=1, fg_color=COLOR_BORDER).pack(fill="x")
        status_inner = ctk.CTkFrame(self.status_bar, fg_color="transparent")
        status_inner.pack(fill="x", padx=20, pady=8)
        ctk.CTkLabel(status_inner, text="●", font=(FONT_MAIN, 10), text_color=COLOR_ACCENT).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(status_inner, textvariable=self.status_msg, font=(FONT_MONO, 11),
                     text_color=COLOR_MUTED).pack(side="left")
        ctk.CTkLabel(status_inner, text=APP_VERSION, font=(FONT_MONO, 10),
                     text_color=COLOR_DIM).pack(side="right")

        self.show_dashboard()

        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
        core.play_startup_sound()
        self.start_auto_ram_optimization()
        self.after(50, self._process_ui_queue)

    def _resolve_log_file(self):
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        folder = os.path.join(base, "PCFIX")
        os.makedirs(folder, exist_ok=True)
        return os.path.join(folder, "pcfix.log")

    def _log(self, message):
        try:
            ts = time.strftime("%Y-%m-%d %H:%M:%S")
            with open(self._log_file, "a", encoding="utf-8") as f:
                f.write(f"[{ts}] {message}\n")
        except Exception:
            pass

    def report_callback_exception(self, exc, val, tb):
        detail = "".join(traceback.format_exception(exc, val, tb))
        self._log("UI_EXCEPTION")
        self._log(detail)
        try:
            messagebox.showerror("PCFIX UI Error", detail[-2500:] if len(detail) > 2500 else detail)
        except Exception:
            pass

    def ui_enqueue(self, func, *args, **kwargs):
        self._ui_queue.put((func, args, kwargs))

    def _process_ui_queue(self):
        while True:
            try:
                func, args, kwargs = self._ui_queue.get_nowait()
            except queue.Empty:
                break
            try:
                func(*args, **kwargs)
            except Exception:
                pass
        if self.running:
            self.after(50, self._process_ui_queue)

    def set_active_nav(self, nav_id):
        if nav_id == self._active_nav:
            return
        self._active_nav = nav_id
        for key, btn in self._nav_buttons.items():
            accent = self._nav_accents.get(key)
            if key == nav_id:
                btn.configure(fg_color=COLOR_ELEVATED, hover_color=COLOR_ELEVATED, text_color=COLOR_TEXT)
                if accent:
                    accent.configure(fg_color=COLOR_ACCENT)
            else:
                btn.configure(fg_color="transparent", hover_color="#161618", text_color=COLOR_DIM)
                if accent:
                    accent.configure(fg_color="transparent")

    def add_config_switch(self, parent, cfg, text, key, on_func, off_func, desc, warn_text=None):
        var = ctk.BooleanVar(value=cfg.get(key, False))

        def _toggle():
            if var.get() and warn_text:
                if not messagebox.askyesno("Confirm Change", f"{text}\n\n{warn_text}\n\nDo you want to proceed?"):
                    var.set(False)
                    return
            cfg[key] = var.get()
            core.save_config(cfg)
            if var.get():
                self.run_threaded(on_func, f"APPLYING {text}...")
            else:
                self.run_threaded(off_func, f"REVERTING {text}...")

        sw = ctk.CTkSwitch(parent, text=text, variable=var, command=_toggle, progress_color=COLOR_ACCENT, fg_color=COLOR_BORDER)
        sw.pack(anchor="w", pady=6)
        ctk.CTkLabel(parent, text=desc, font=(FONT_MAIN, 10), text_color=COLOR_DIM, wraplength=900, justify="left").pack(anchor="w", pady=(0, 8))
        if warn_text:
            ctk.CTkLabel(parent, text=f"Warning: {warn_text}", font=(FONT_MAIN, 10, "bold"), text_color=COLOR_ACCENT, wraplength=900, justify="left").pack(anchor="w", pady=(0, 12))

        return var

    def navigate(self, nav_id, screen_func):
        self._log(f"NAVIGATE {nav_id}")
        try:
            screen_func()
        except Exception as e:
            detail = traceback.format_exc()
            self._log(f"NAVIGATION_FAILED {nav_id} {e}")
            self._log(detail)
            try:
                messagebox.showerror("Navigation Error", detail[-2500:] if len(detail) > 2500 else detail)
            except Exception:
                pass

    def create_nav_btn(self, text, command, nav_id):
        row = ctk.CTkFrame(self.nav_frame, fg_color="transparent", height=36)
        row.pack(fill="x", pady=1)
        row.pack_propagate(False)
        accent = ctk.CTkFrame(row, width=3, fg_color="transparent", corner_radius=2)
        accent.pack(side="left", fill="y", padx=(2, 0), pady=4)
        btn = ctk.CTkButton(
            row, text=text, command=lambda: self.navigate(nav_id, command),
            anchor="w", fg_color="transparent", hover_color="#161618",
            border_width=0, height=36, corner_radius=6,
            text_color=COLOR_DIM, font=(FONT_MAIN, 12),
        )
        btn.pack(side="left", fill="both", expand=True, padx=(6, 4))
        self._nav_buttons[nav_id] = btn
        self._nav_accents[nav_id] = accent

    def start_auto_ram_optimization(self):
        def _auto_opt():
            while self.running:
                # Default to True now as requested
                if self.config.get("auto_ram", True):
                    res = core.optimize_ram()
                time.sleep(1800) # 30 minutes
        
        threading.Thread(target=_auto_opt, daemon=True).start()

    def clear_main(self):
        for widget in self.main_area.winfo_children():
            widget.destroy()

    def add_header(self, title, subtitle=""):
        head = ctk.CTkFrame(self.main_area, fg_color="transparent")
        head.pack(fill="x", pady=(0, 18))
        accent_line = ctk.CTkFrame(head, width=4, height=36, fg_color=COLOR_ACCENT, corner_radius=2)
        accent_line.pack(side="left", padx=(0, 12))
        text_col = ctk.CTkFrame(head, fg_color="transparent")
        text_col.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(text_col, text=title, font=(FONT_DISPLAY, 24, "bold"), text_color=COLOR_TEXT).pack(anchor="w")
        if subtitle:
            ctk.CTkLabel(text_col, text=subtitle, font=(FONT_MAIN, 12), text_color=COLOR_DIM).pack(anchor="w", pady=(2, 0))

    def show_dashboard(self):
        self.set_active_nav("dashboard")
        self.clear_main()

        hero = ctk.CTkFrame(self.main_area, fg_color=COLOR_SURFACE, border_color=COLOR_BORDER, border_width=1, corner_radius=14)
        hero.pack(fill="x", pady=(0, 18))
        hero_inner = ctk.CTkFrame(hero, fg_color="transparent")
        hero_inner.pack(fill="x", padx=22, pady=20)
        ctk.CTkLabel(hero_inner, text="PCFIX", font=(FONT_DISPLAY, 32, "bold"), text_color=COLOR_TEXT).pack(anchor="w")
        ctk.CTkLabel(
            hero_inner,
            text="Resurrect performance — clean, repair, and tune from one place.",
            font=(FONT_MAIN, 13), text_color=COLOR_MUTED
        ).pack(anchor="w", pady=(4, 14))
        AccentButton(
            hero_inner,
            text="Run Smart Scan",
            command=lambda: self.run_threaded(core.run_smart_scan, "RUNNING SMART SCAN..."),
            width=220
        ).pack(anchor="w")

        grid = ctk.CTkFrame(self.main_area, fg_color="transparent")
        grid.pack(fill="x")
        stats = core.get_system_status()
        has_battery = "battery" in stats

        if has_battery:
            grid.columnconfigure((0, 1, 2, 3), weight=1)
            StatusCard(grid, "CPU", self.var_cpu).grid(row=0, column=0, padx=(0, 8), sticky="ew")
            StatusCard(grid, "RAM", self.var_ram).grid(row=0, column=1, padx=8, sticky="ew")
            StatusCard(grid, "DISK", self.var_disk).grid(row=0, column=2, padx=8, sticky="ew")
            StatusCard(grid, "BATTERY", self.var_battery).grid(row=0, column=3, padx=(8, 0), sticky="ew")
        else:
            grid.columnconfigure((0, 1, 2), weight=1)
            StatusCard(grid, "CPU", self.var_cpu).grid(row=0, column=0, padx=(0, 8), sticky="ew")
            StatusCard(grid, "RAM", self.var_ram).grid(row=0, column=1, padx=8, sticky="ew")
            StatusCard(grid, "DISK", self.var_disk).grid(row=0, column=2, padx=(8, 0), sticky="ew")

        auto_ram_status = "ACTIVE" if self.config.get("auto_ram", True) else "DISABLED"
        color = COLOR_GOOD if auto_ram_status == "ACTIVE" else COLOR_DIM
        ctk.CTkLabel(
            self.main_area,
            text=f"Auto RAM optimizer  ·  {auto_ram_status}",
            font=(FONT_MONO, 11), text_color=color
        ).pack(pady=(14, 0), anchor="w")

        SectionLabel(self.main_area, "Quick actions").pack(anchor="w", pady=(28, 10))
        actions = ctk.CTkFrame(self.main_area, fg_color="transparent")
        actions.pack(fill="x")
        GothicButton(actions, text="Flush DNS", command=self.cmd_flush_dns).pack(side="left", fill="x", expand=True, padx=(0, 6))
        GothicButton(actions, text="Optimize RAM", command=self.cmd_optimize_ram).pack(side="left", fill="x", expand=True, padx=(6, 6))
        GothicButton(actions, text="Purge Temp", command=self.cmd_purge_temp).pack(side="left", fill="x", expand=True, padx=(6, 0))

    def show_tweaks(self):
        self.set_active_nav("tweaks")
        self.clear_main()
        self.add_header("SYSTEM TWEAKS", "Apply high-impact optimizations")
        cfg = core.load_config()
        body = ctk.CTkScrollableFrame(self.main_area, fg_color="transparent")
        body.pack(fill="both", expand=True, pady=(0, 10))
        panel = ctk.CTkFrame(body, fg_color="transparent")
        panel.pack(fill="x")

        def add_switch(parent, text, key, on_func, off_func, desc, warn_text=None):
            self.add_config_switch(parent, cfg, text, key, on_func, off_func, desc, warn_text)

        add_switch(panel, "Disable Hibernation", "tweak_disable_hibernation", core.disable_hibernation, core.enable_hibernation,
                   "Turns off hibernation and frees disk space. Disables Fast Startup. Reboot may be required.")
        add_switch(panel, "Visual Effects: Performance Mode", "tweak_visual_fx_perf", core.optimize_visual_fx, core.reset_visual_fx,
                   "Reduces animations and effects to improve responsiveness. Reset to restore default visuals.")
        add_switch(panel, "Disable Fullscreen Optimizations", "tweak_disable_fso", core.disable_fullscreen_optimizations, core.enable_fullscreen_optimizations,
                   "Prevents Windows from altering fullscreen apps, which can reduce input delay in some games.")
        add_switch(panel, "Disable Power Throttling", "tweak_disable_power_throttling", core.disable_power_throttling, core.enable_power_throttling,
                   "Stops background power limits for better performance at the cost of higher power use.")
        add_switch(panel, "Enable Classic Right-Click Menu", "tweak_classic_context", core.enable_classic_context_menu, core.disable_classic_context_menu,
                   "Restores the Windows 10 style context menu on Windows 11. Sign out/in may be needed.")
        add_switch(panel, "Show Verbose Boot Information", "tweak_boot_verbose", core.enable_boot_verbose, core.disable_boot_verbose,
                   "Displays detailed startup and shutdown messages for easier troubleshooting.")
        add_switch(panel, "Disable Large Send Offload (LSO)", "tweak_disable_lso", core.disable_lso, core.enable_lso,
                   "Disables NIC offloading that can cause latency on some adapters. Improves network responsiveness.")
        add_switch(panel, "Apply TCP Optimizations", "tweak_tcp_opt", core.apply_tcp_optimizations, core.reset_tcp_optimizations,
                   "Tunes TCP settings for stability and latency. Reset if you notice connectivity issues.")
        add_switch(panel, "Disable SmartScreen", "tweak_smartscreen", core.disable_smartscreen, core.enable_smartscreen,
                   "Turns off Microsoft SmartScreen checks. Reduces prompts but lowers protection.",
                   warn_text="Disabling SmartScreen reduces protection against malicious downloads and apps.")
        add_switch(panel, "Disable User Account Control (UAC)", "tweak_uac", core.disable_uac, core.enable_uac,
                   "Removes elevation prompts. Requires reboot.",
                   warn_text="Disabling UAC lowers system security and can let malware run without prompts.")
        add_switch(panel, "Block Windows Driver Updates", "tweak_block_driver_updates", core.block_driver_updates, core.allow_driver_updates,
                   "Prevents Windows Update from installing device drivers automatically.",
                   warn_text="Blocking driver updates can leave devices outdated or incompatible after major updates.")
        add_switch(panel, "Disable VPN Support", "tweak_disable_vpn", core.disable_vpn_support, core.enable_vpn_support,
                   "Stops VPN services if you never use VPNs. Can be re-enabled anytime.",
                   warn_text="Disabling VPN services prevents VPN clients from working until re-enabled.")
        add_switch(panel, "Disable Windows Boot Interface", "tweak_boot_ui", core.disable_boot_interface, core.enable_boot_interface,
                   "Hides boot UX animations and logos.",
                   warn_text="Advanced boot visuals are disabled. Use only if you prefer minimal boot UI.")
        add_switch(panel, "Remove Windows Settings Ads", "tweak_remove_settings_ads", core.remove_settings_ads, core.restore_settings_ads,
                   "Disables suggestions and ads in Settings and Start recommendations.")
        add_switch(panel, "Disable Touch Settings", "tweak_disable_touch", core.disable_touch, core.enable_touch,
                   "Turns off touch keyboard/ink services on non-touch devices.")
        add_switch(panel, "Disable CPU Mitigations", "tweak_disable_mitigations", core.disable_cpu_mitigations, core.enable_cpu_mitigations,
                   "Disables certain CPU security mitigations for performance. Reboot required.",
                   warn_text="Reduces protection against side-channel attacks (Meltdown/Spectre class). Not recommended on shared or sensitive systems.")
        add_switch(panel, "Optimize Windows Explorer", "tweak_optimize_explorer", core.optimize_explorer, core.reset_explorer,
                   "Runs Explorer in a separate process and trims UI extras for snappier browsing.")
        add_switch(panel, "Optimize Network Congestion Provider", "tweak_net_congestion", core.optimize_network_congestion, core.reset_network_congestion,
                   "Adjusts throttling and responsiveness for lower latency networking.")
        add_switch(panel, "Disable Deprecated Network Features", "tweak_disable_deprecated_net", core.disable_deprecated_network_features, core.enable_deprecated_network_features,
                   "Disables legacy IPv6 tunneling (Teredo/6to4/ISATAP) that can cause issues.",
                   warn_text="If you rely on IPv6 tunneling, keep these enabled.")
        add_switch(panel, "Enable TRIM", "tweak_enable_trim", core.enable_trim, core.disable_trim,
                   "Ensures SSDs receive TRIM commands to maintain performance.")
        add_switch(panel, "Optimize Drives (TRIM/Defrag)", "tweak_optimize_drives", core.optimize_drives, lambda: None,
                   "Runs TRIM for SSDs and defrag for HDDs. Safe on modern Windows.",
                   warn_text="May take time depending on drive size and fragmentation.")
        add_switch(panel, "Apply DSCP Low-Latency Policy", "tweak_dscp", core.optimize_dscp_policy, core.remove_dscp_policy,
                   "Creates a QoS policy marking app traffic as low latency (DSCP 46).",
                   warn_text="Some enterprise networks may override DSCP; harmless at home.")
        add_switch(panel, "Disable UCPD", "tweak_ucpd", core.disable_ucpd, core.enable_ucpd,
                   "Disables User Choice Protection Driver to allow programmatic default changes.",
                   warn_text="Advanced setting; only for users who change defaults via scripts.")
        add_switch(panel, "Optimize Netsh Network Settings", "tweak_netsh", core.optimize_netsh, core.reset_netsh,
                   "Tunes TCP heuristics and offload preferences via netsh.",
                   warn_text="If network connectivity degrades, use Reset to restore defaults.")
        add_switch(panel, "Optimize Memory Management", "tweak_memory_mgmt", core.optimize_memory_management, core.reset_memory_management,
                   "Reduces kernel paging to improve responsiveness.",
                   warn_text="May increase RAM use; not ideal on low-memory systems.")
        add_switch(panel, "Optimize I/O Operations", "tweak_io_ops", core.optimize_io_operations, core.reset_io_operations,
                   "Enables Prefetch/Superfetch and SysMain for faster app and file access.",
                   warn_text="Can increase background disk activity on HDDs.")
        add_switch(panel, "Enable Hardware GPU Scheduling", "tweak_hwsch", core.enable_gpu_hardware_scheduling, core.disable_gpu_hardware_scheduling,
                   "Lets GPU handle scheduling directly to reduce latency.",
                   warn_text="Requires supported drivers and may need reboot.")
        add_switch(panel, "Optimize Message Signal Interrupts (MSI)", "tweak_msi", core.enable_msi, core.disable_msi,
                   "Enables MSI on supported PCI devices to reduce interrupt latency.",
                   warn_text="Hardware-specific; enable only if devices and drivers support MSI.")
        add_switch(panel, "Disable Edge Telemetry", "tweak_edge_telemetry", core.disable_edge_telemetry, core.enable_edge_telemetry,
                   "Stops usage metrics being sent by Microsoft Edge.")
        add_switch(panel, "Disable Firefox Telemetry", "tweak_firefox_telemetry", core.disable_firefox_telemetry, core.enable_firefox_telemetry,
                   "Stops Mozilla Firefox from sending telemetry.")
        add_switch(panel, "Disable Office Telemetry", "tweak_office_telemetry", core.disable_office_telemetry, core.enable_office_telemetry,
                   "Reduces Microsoft Office diagnostic data collection.")
        add_switch(panel, "Disable Visual Studio Telemetry", "tweak_vs_telemetry", core.disable_vs_telemetry, core.enable_vs_telemetry,
                   "Prevents Visual Studio from sending telemetry data.")
        add_switch(panel, "Disable Chrome Telemetry", "tweak_chrome_telemetry", core.disable_chrome_telemetry, core.enable_chrome_telemetry,
                   "Stops Google Chrome from sending usage metrics.",
                   warn_text="Policies apply to managed Chrome instances; restart Chrome after change.")
        
        ctk.CTkLabel(body, text="ONE-CLICK PRESETS", font=(FONT_MAIN, 14, "bold"), text_color=COLOR_DIM).pack(anchor="w", pady=(18, 6))
        GothicButton(body, text="⚡ APPLY GENERAL WINDOWS OPTIMIZATIONS", command=lambda: self.run_threaded(core.apply_general_optimizations, "APPLYING GENERAL OPTIMIZATIONS...")).pack(fill="x", padx=2, pady=(0, 12))
        ctk.CTkLabel(body, text="RECOVERY & REPAIR", font=(FONT_MAIN, 14, "bold"), text_color=COLOR_DIM).pack(anchor="w", pady=(10, 6))
        GothicButton(body, text="🛡️ CREATE RESTORE POINT", command=lambda: self.run_threaded(core.create_restore_point, "CREATING RESTORE POINT...")).pack(fill="x", padx=2, pady=4)
        GothicButton(body, text="🧰 RUN SFC /SCANNOW", command=lambda: self.run_threaded(core.run_sfc, "RUNNING SFC...")).pack(fill="x", padx=2, pady=4)
        GothicButton(body, text="🩺 RUN DISM RESTOREHEALTH", command=lambda: self.run_threaded(core.run_dism_restorehealth, "RUNNING DISM...")).pack(fill="x", padx=2, pady=4)
        ctk.CTkLabel(body, text="SETTINGS", font=(FONT_MAIN, 14, "bold"), text_color=COLOR_DIM).pack(anchor="w", pady=(12, 6))
        GothicButton(body, text="📦 EXPORT SETTINGS TO DESKTOP", command=lambda: self.run_threaded(core.export_settings_to_desktop, "EXPORTING SETTINGS...")).pack(fill="x", padx=2, pady=(0, 12))
        ctk.CTkLabel(self.main_area, textvariable=self.status_msg, font=(FONT_MONO, 11), text_color=COLOR_DIM).pack(side="bottom", anchor="w")

    def show_cleaner(self):
        self.set_active_nav("cleaner")
        self.clear_main()
        self.add_header("CLEANING PROTOCOLS", "Free up space and remove junk")
        cfg = core.load_config()
        body = ctk.CTkScrollableFrame(self.main_area, fg_color="transparent")
        body.pack(fill="both", expand=True, pady=(0, 10))

        def add_switch(parent, text, key, on_func, off_func, desc, warn_text=None):
            self.add_config_switch(parent, cfg, text, key, on_func, off_func, desc, warn_text)

        GothicButton(body, text="🗑️ PURGE TEMP FILES", command=self.cmd_purge_temp).pack(fill="x", pady=5)
        GothicButton(body, text="♻️ EMPTY RECYCLE BIN", command=self.cmd_recycle_bin).pack(fill="x", pady=5)
        ctk.CTkLabel(body, text="VISIBILITY & EXPLORER", font=(FONT_MAIN, 14, "bold"), text_color=COLOR_DIM).pack(anchor="w", pady=(16, 8))
        add_switch(body, "Show File Extensions", "tweak_show_ext", core.show_file_extensions, core.hide_file_extensions, "Displays file extensions in Explorer.")
        add_switch(body, "Show Hidden Files", "tweak_show_hidden", core.show_hidden_files, core.hide_hidden_files, "Shows hidden and system files in Explorer.", warn_text="Editing system files can be risky.")
        ctk.CTkLabel(body, text="NETWORK & UPDATE POLICIES", font=(FONT_MAIN, 14, "bold"), text_color=COLOR_DIM).pack(anchor="w", pady=(16, 8))
        add_switch(body, "Disable SMBv1", "tweak_smb1", core.disable_smb1, core.enable_smb1, "Turns off legacy SMBv1 protocol.", warn_text="Some very old devices may require SMBv1.")
        add_switch(body, "Prefer IPv4 Over IPv6", "tweak_ipv4_pref", core.prefer_ipv4, core.prefer_ipv_default, "Prefers IPv4 routing for stability on some ISPs.")
        add_switch(body, "Disable NetBIOS over TCP/IP", "tweak_netbios", core.disable_netbios, core.enable_netbios, "Reduces legacy broadcast traffic.", warn_text="Legacy network discovery may stop working.")
        add_switch(body, "Pause Windows Update", "tweak_pause_update", core.pause_windows_update, core.resume_windows_update, "Pauses automatic Windows Updates.", warn_text="Ensure you manually update periodically.")
        add_switch(body, "Disable Auto-Reboot After Update", "tweak_update_reboot", core.disable_auto_reboot_update, core.enable_auto_reboot_update, "Prevents forced reboots when a user is logged in.")
        frame_net = ctk.CTkFrame(body, fg_color="transparent")
        frame_net.pack(fill="x", pady=(8, 0))
        GothicButton(frame_net, text="🧹 FLUSH DNS", command=lambda: self.run_threaded(core.flush_dns, "FLUSHING DNS...")).pack(side="left", fill="x", expand=True, padx=(0, 6))
        GothicButton(frame_net, text="🔄 RESET WINSOCK", command=lambda: self.run_threaded(core.reset_winsock, "RESETTING WINSOCK...")).pack(side="left", fill="x", expand=True)
        frame_dns = ctk.CTkFrame(body, fg_color="transparent")
        frame_dns.pack(fill="x", pady=(8, 12))
        GothicButton(frame_dns, text="🌐 SET DNS: CLOUDFLARE", command=lambda: self.run_threaded(core.set_dns_cloudflare, "SETTING DNS TO CLOUDFLARE...")).pack(side="left", fill="x", expand=True, padx=(0, 6))
        GothicButton(frame_dns, text="🌐 RESTORE DNS: DHCP", command=lambda: self.run_threaded(core.restore_dns_dhcp, "RESTORING DNS TO DHCP...")).pack(side="left", fill="x", expand=True)
        GothicButton(body, text="🧼 CLEAR WINDOWS UPDATE CACHE", command=lambda: self.run_threaded(core.clear_windows_update_cache, "CLEARING UPDATE CACHE...")).pack(fill="x", pady=(8, 12))
        ctk.CTkLabel(body, text="SERVICES & APP BEHAVIOR", font=(FONT_MAIN, 14, "bold"), text_color=COLOR_DIM).pack(anchor="w", pady=(16, 8))
        add_switch(body, "Disable Search Indexing", "tweak_search_index", core.disable_search_index, core.enable_search_index, "Disables Windows Search indexing to reduce disk usage.", warn_text="Search performance may be slower.")
        add_switch(body, "Disable SysMain", "tweak_sysmain", core.disable_sysmain, core.enable_sysmain, "Stops SysMain service to reduce background disk activity.", warn_text="App launch prefetch may be reduced.")
        add_switch(body, "Disable Background Apps", "tweak_bg_apps", core.disable_background_apps, core.enable_background_apps, "Prevents background UWP apps from running.")
        add_switch(body, "Disable Print Spooler", "tweak_spooler", core.disable_print_spooler, core.enable_print_spooler, "Turns off printing service to reduce attack surface.", warn_text="Printing will not work while disabled.")
        add_switch(body, "Disable Remote Assistance", "tweak_remote_assist", core.disable_remote_assistance, core.enable_remote_assistance, "Blocks Windows Remote Assistance connections.")
        add_switch(body, "Disable OneDrive Sync", "tweak_onedrive", core.disable_onedrive, core.enable_onedrive, "Prevents OneDrive syncing via policy.", warn_text="OneDrive features will be unavailable.")
        GothicButton(body, text="🛍️ RESET MICROSOFT STORE CACHE", command=lambda: self.run_threaded(core.reset_store_cache, "RESETTING STORE CACHE...")).pack(fill="x", pady=(8, 12))
        ctk.CTkLabel(body, text="PRIVACY", font=(FONT_MAIN, 14, "bold"), text_color=COLOR_DIM).pack(anchor="w", pady=(16, 8))
        add_switch(body, "Disable Advertising ID", "tweak_ad_id", core.disable_ad_id, core.enable_ad_id, "Stops apps using Advertising ID.")
        add_switch(body, "Disable Activity History", "tweak_activity", core.disable_activity_history, core.enable_activity_history, "Stops Windows from collecting activity history.")
        add_switch(body, "Disable Error Reporting", "tweak_wer", core.disable_error_reporting, core.enable_error_reporting, "Disables Windows Error Reporting.")
        add_switch(body, "Disable Feedback Reminders", "tweak_feedback", core.disable_feedback, core.enable_feedback, "Stops feedback notification prompts.")
        add_switch(body, "Disable Location Services", "tweak_location", core.disable_location, core.enable_location, "Prevents location APIs from being used.")
        add_switch(body, "Disable Clipboard History", "tweak_clipboard", core.disable_clipboard_history, core.enable_clipboard_history, "Turns off clipboard history synchronization.")
        add_switch(body, "Disable Windows Tips", "tweak_tips", core.disable_windows_tips, core.enable_windows_tips, "Turns off Windows tips and suggestions.")
        add_switch(body, "Disable App Suggestions", "tweak_app_suggest", core.disable_app_suggestions, core.enable_app_suggestions, "Stops app suggestions and recommendations.")
        ctk.CTkLabel(body, text="TASKBAR & UI", font=(FONT_MAIN, 14, "bold"), text_color=COLOR_DIM).pack(anchor="w", pady=(16, 8))
        add_switch(body, "Disable Widgets", "tweak_widgets", core.disable_widgets, core.enable_widgets, "Hides Widgets on the taskbar.")
        add_switch(body, "Disable Snap Assist", "tweak_snap", core.disable_snap_assist, core.enable_snap_assist, "Disables Snap Assist popups.")
        add_switch(body, "Disable Autoplay", "tweak_autoplay", core.disable_autoplay, core.enable_autoplay, "Prevents autoplay on removable media.")
        add_switch(body, "Disable Sharing Wizard", "tweak_sharing_wizard", core.disable_sharing_wizard, core.enable_sharing_wizard, "Turns off simplified sharing.")
        ctk.CTkLabel(body, text="GAMING", font=(FONT_MAIN, 14, "bold"), text_color=COLOR_DIM).pack(anchor="w", pady=(16, 8))
        add_switch(body, "Disable Game Bar", "tweak_gamebar", core.disable_gamebar, core.enable_gamebar, "Stops Xbox Game Bar overlays.", warn_text="Screen capture via Game Bar will be unavailable.")
        add_switch(body, "Disable Xbox Services", "tweak_xbox", core.disable_xbox_services, core.enable_xbox_services, "Disables Xbox services to reduce background usage.", warn_text="Xbox app features may break.")
        ctk.CTkLabel(body, text="SEARCH & POWER", font=(FONT_MAIN, 14, "bold"), text_color=COLOR_DIM).pack(anchor="w", pady=(16, 8))
        add_switch(body, "Disable Bing Web in Start", "tweak_bing_start", core.disable_bing_search, core.enable_bing_search, "Removes web results from Start menu search.")
        add_switch(body, "Enable High Performance Plan", "tweak_power_high", core.enable_high_performance_plan, core.enable_balanced_plan, "Switches active power plan to High Performance.")
        add_switch(body, "Disable Hibernate", "tweak_hibernate", core.disable_hibernate, core.enable_hibernate, "Turns off hibernation to free disk space.", warn_text="Hibernate functionality will be unavailable.")
        add_switch(body, "Disable Fast Startup", "tweak_fast_startup", core.disable_fast_startup, core.enable_fast_startup, "Prevents hybrid boot for more stable device initialization.")
        add_switch(body, "Disable Power Throttling", "tweak_power_throttle", core.disable_power_throttling, core.enable_power_throttling, "Stops background power throttling on processes.")
        add_switch(body, "Disable USB Selective Suspend", "tweak_usb_suspend", core.disable_usb_selective_suspend, core.enable_usb_selective_suspend, "Prevents USB devices from power suspending.", warn_text="May increase power usage on battery.")
        ctk.CTkLabel(body, text="SYSTEM POLICIES", font=(FONT_MAIN, 14, "bold"), text_color=COLOR_DIM).pack(anchor="w", pady=(16, 8))
        add_switch(body, "Disable Windows Telemetry (Global)", "tweak_telemetry_global", core.disable_telemetry_global, core.enable_telemetry_global, "Reduces Windows diagnostic data collection.", warn_text="Some personalization features may be limited.")
        add_switch(body, "Disable Windows Copilot", "tweak_copilot", core.disable_copilot_policy, core.enable_copilot_policy, "Hides Copilot and disables its policy integration.", warn_text="Requires Windows 11. Reboot may be needed.")
        add_switch(body, "Disable Lock Screen Spotlight", "tweak_lock_spotlight", core.disable_lock_screen_spotlight, core.enable_lock_screen_spotlight, "Stops Spotlight rotating lock screen content.", warn_text="Affects lock screen imagery and tips.")
        add_switch(body, "Disable Cortana Policy", "tweak_cortana_policy", core.disable_cortana_policy, core.enable_cortana_policy, "Disables Cortana assistant.")
        add_switch(body, "Enable Storage Sense", "tweak_storage_sense", core.enable_storage_sense, core.disable_storage_sense, "Enables automatic storage cleanup.")
        add_switch(body, "Enable Core Isolation", "tweak_core_isolation", core.enable_core_isolation, core.disable_core_isolation, "Enables VBS and Memory Integrity.", warn_text="May require reboot and supported virtualization.")
        add_switch(body, "Disable Automatic Driver Updates", "tweak_driver_updates", core.disable_driver_auto_update, core.enable_driver_auto_update, "Prevents Windows from automatically installing drivers.")
        ctk.CTkLabel(body, text="INPUT", font=(FONT_MAIN, 14, "bold"), text_color=COLOR_DIM).pack(anchor="w", pady=(16, 8))
        add_switch(body, "Disable Mouse Acceleration", "tweak_mouse_accel", core.disable_mouse_accel, core.enable_mouse_accel, "Sets raw mouse input without acceleration.")
        ctk.CTkLabel(body, text="REMOTE ACCESS", font=(FONT_MAIN, 14, "bold"), text_color=COLOR_DIM).pack(anchor="w", pady=(16, 8))
        add_switch(body, "Disable Remote Desktop", "tweak_remote", core.disable_remote_desktop, core.enable_remote_desktop, "Prevents Remote Desktop connections.", warn_text="Remote access will be blocked.")
        GothicButton(body, text="🔓 UNLOCKER (FORCE DELETE)", command=self.show_shredder).pack(fill="x", pady=5)
        
        # Chrome/Edge Killer
        ctk.CTkLabel(body, text="PROCESS TERMINATION", font=(FONT_MAIN, 14, "bold"), text_color=COLOR_DIM).pack(anchor="w", pady=(30, 10))
        
        frame = ctk.CTkFrame(body, fg_color="transparent")
        frame.pack(fill="x")
        GothicButton(frame, text="💀 KILL CHROME", command=lambda: self.cmd_kill("chrome")).pack(side="left", fill="x", expand=True, padx=(0, 5))
        GothicButton(frame, text="💀 KILL EDGE", command=lambda: self.cmd_kill("msedge")).pack(side="left", fill="x", expand=True, padx=(5, 0))

        ctk.CTkLabel(self.main_area, textvariable=self.status_msg, font=(FONT_MONO, 11), text_color=COLOR_DIM).pack(side="bottom", anchor="w")

    def show_repair(self):
        self.set_active_nav("repair")
        self.clear_main()
        self.add_header("ADVANCED REPAIR", "Fix system corruptions and errors")
        
        ctk.CTkLabel(self.main_area, text="⚠️ Operations may take several minutes to complete.", font=(FONT_MAIN, 12), text_color=COLOR_ACCENT).pack(anchor="w", pady=(0, 10))

        GothicButton(self.main_area, text="🩺 SYSTEM FILE CHECK (SFC)", command=lambda: self.run_threaded(core.run_sfc, "SFC SCANNING...")).pack(fill="x", pady=5)
        GothicButton(self.main_area, text="🚑 REPAIR WINDOWS IMAGE (DISM)", command=lambda: self.run_threaded(core.run_dism, "DISM REPAIRING...")).pack(fill="x", pady=5)
        GothicButton(self.main_area, text="🔌 RESET NETWORK STACK", command=lambda: self.run_threaded(core.reset_network, "RESETTING NETWORK...")).pack(fill="x", pady=5)
        GothicButton(self.main_area, text="💿 SCHEDULE DISK CHECK (RESTART)", command=lambda: self.run_threaded(core.check_disk_schedule, "SCHEDULING CHKDSK...")).pack(fill="x", pady=5)
        
        ctk.CTkLabel(self.main_area, textvariable=self.status_msg, font=(FONT_MONO, 11), text_color=COLOR_DIM).pack(side="bottom", anchor="w")

    def show_shredder(self):
         self.set_active_nav("unlocker")
         self.clear_main()
         self.add_header("FILE UNLOCKER", "Force delete stubborn files")
         
         ctk.CTkLabel(self.main_area, text="Select a file that cannot be deleted normally.", font=(FONT_MAIN, 12), text_color=COLOR_DIM).pack(anchor="w", pady=(0, 20))
         
         def _shred():
             path = filedialog.askopenfilename()
             if path:
                 self.run_threaded(lambda: core.force_delete_file(path), "UNLOCKING & DELETING...")
         
         AccentButton(self.main_area, text="📂 SELECT FILE TO DESTROY", command=_shred).pack(fill="x", pady=10)
         
         ctk.CTkLabel(self.main_area, textvariable=self.status_msg, font=(FONT_MONO, 11), text_color=COLOR_DIM).pack(side="bottom", anchor="w")

    def show_force_remove_app(self):
        self.set_active_nav("force_remove")
        self.clear_main()
        self.add_header("FORCE REMOVE APP", "Detect and quarantine-remove application files")
        name_var = tk.StringVar()
        entry = ctk.CTkEntry(self.main_area, textvariable=name_var)
        entry.pack(fill="x", pady=(0, 8))
        actions = ctk.CTkFrame(self.main_area, fg_color="transparent")
        actions.pack(fill="x", pady=(0, 8))
        results = ctk.CTkScrollableFrame(self.main_area, fg_color=COLOR_SURFACE, height=260, border_color=COLOR_BORDER, border_width=1)
        results.pack(fill="both", expand=True, pady=(8, 12))
        def _render_list(items):
            for w in results.winfo_children():
                w.destroy()
            if not items:
                ctk.CTkLabel(results, text="No artifacts found.", font=(FONT_MONO, 12), text_color=COLOR_DIM).pack(pady=12)
                return
            for p in items:
                row = ctk.CTkFrame(results, fg_color="transparent")
                row.pack(fill="x", pady=2)
                ctk.CTkLabel(row, text=p, font=(FONT_MONO, 11), text_color=COLOR_TEXT).pack(anchor="w", padx=8)
        def _scan():
            self.status_msg.set("SCANNING...")
            def run():
                items = core.find_application_artifacts(name_var.get().strip(), include_processes=True)
                def _done():
                    self.status_msg.set(f"FOUND {len(items)} ITEMS")
                    _render_list(items)
                self.ui_enqueue(_done)
            threading.Thread(target=run, daemon=True).start()
        def _delete():
            self.status_msg.set("DELETING (QUARANTINE)...")
            def run():
                res = core.confirm_and_delete_app(name_var.get().strip(), auto_confirm=True, threads=6)
                self.ui_enqueue(self.status_msg.set, f"{res.get('status','OK')}: moved={res.get('moved',0)} deleted={res.get('deleted',0)} scheduled={res.get('scheduled',0)} errors={res.get('errors',0)}")
            threading.Thread(target=run, daemon=True).start()
        def _restore():
            self.status_msg.set("RESTORING...")
            def run():
                r = core.restore_quarantine()
                self.ui_enqueue(self.status_msg.set, f"RESTORE: {r.get('status','?')} restored={r.get('restored',0)} errors={r.get('errors',0)}")
            threading.Thread(target=run, daemon=True).start()
        GothicButton(actions, text="🔎 SCAN ARTIFACTS", command=_scan).pack(side="left", fill="x", expand=True, padx=(0, 6))
        GothicButton(actions, text="🗑 DELETE ALL (QUARANTINE)", command=_delete).pack(side="left", fill="x", expand=True, padx=(6, 6))
        GothicButton(actions, text="↩ RESTORE LAST", command=_restore).pack(side="left", fill="x", expand=True, padx=(6, 0))
        ctk.CTkLabel(self.main_area, textvariable=self.status_msg, font=(FONT_MONO, 11), text_color=COLOR_DIM).pack(side="bottom", anchor="w")
    def show_debloater(self): # Renamed logic
        self.set_active_nav("debloater")
        self.clear_main()
        self.add_header("SYSTEM DEBLOATER", "Remove pre-installed bloatware")

        # Scan Button
        AccentButton(self.main_area, text="🔎 SCAN FOR BLOATWARE", command=lambda: self.scan_bloatware(results_frame)).pack(fill="x", pady=5)

        # Results Area
        results_frame = ctk.CTkScrollableFrame(self.main_area, fg_color=COLOR_SURFACE, height=300, border_color=COLOR_BORDER, border_width=1)
        results_frame.pack(fill="x", pady=20)
        
        ctk.CTkLabel(results_frame, text="Click SCAN to detect bloatware...", font=(FONT_MONO, 12), text_color=COLOR_DIM).pack(pady=20)

        ctk.CTkLabel(self.main_area, textvariable=self.status_msg, font=(FONT_MONO, 11), text_color=COLOR_DIM).pack(side="bottom", anchor="w")

    def scan_bloatware(self, frame):
        for widget in frame.winfo_children():
            widget.destroy()
            
        self.status_msg.set("SCANNING APPS...")
        
        def _scan():
            apps = core.get_installed_bloatware()
            def _render():
                for widget in frame.winfo_children():
                    widget.destroy()
                if not apps:
                    ctk.CTkLabel(frame, text="No common bloatware detected.", font=(FONT_MONO, 12), text_color="#22c55e").pack(pady=20)
                else:
                    for app in apps:
                        row = ctk.CTkFrame(frame, fg_color="transparent")
                        row.pack(fill="x", pady=2)
                        ctk.CTkLabel(row, text=app, font=(FONT_MONO, 12), text_color=COLOR_TEXT).pack(side="left", padx=10)
                        GothicButton(row, text="REMOVE", width=80, height=30, command=lambda a=app, r=row: self.remove_app(a, r)).pack(side="right", padx=10, pady=5)
                self.status_msg.set("SCAN COMPLETE")

            self.ui_enqueue(_render)
            
        threading.Thread(target=_scan, daemon=True).start()

    def remove_app(self, app_name, row_widget):
        self.status_msg.set(f"REMOVING {app_name}...")
        def _rem():
            res = core.remove_bloatware(app_name)
            def _done():
                self.status_msg.set(res)
                row_widget.destroy()
            self.ui_enqueue(_done)
        threading.Thread(target=_rem, daemon=True).start()

    def show_privacy(self):
        self.set_active_nav("privacy")
        self.clear_main()
        self.add_header("PRIVACY SHIELD", "Block telemetry and tracking")
        
        ctk.CTkLabel(self.main_area, text="TELEMETRY & TRACKING", font=(FONT_MAIN, 14, "bold"), text_color=COLOR_DIM).pack(anchor="w", pady=(10, 5))
        GothicButton(self.main_area, text="🛡️ DISABLE WINDOWS TELEMETRY", command=lambda: self.run_threaded(core.apply_privacy_shield, "APPLYING PRIVACY SHIELD...")).pack(fill="x", pady=5)

        ctk.CTkLabel(self.main_area, text="ADVANCED TOOLS", font=(FONT_MAIN, 14, "bold"), text_color=COLOR_DIM).pack(anchor="w", pady=(20, 5))
        GothicButton(self.main_area, text="👼 ENABLE 'GOD MODE' (DESKTOP)", command=lambda: self.run_threaded(core.create_god_mode, "CREATING GOD MODE...")).pack(fill="x", pady=5)
        
        ctk.CTkLabel(self.main_area, textvariable=self.status_msg, font=(FONT_MONO, 11), text_color=COLOR_DIM).pack(side="bottom", anchor="w")

    def show_bsod(self):
        self.set_active_nav("bsod")
        self.clear_main()
        self.add_header("BSOD ANALYZER", "Interpret crash dumps")
        
        # Advanced analysis actions
        actions = ctk.CTkFrame(self.main_area, fg_color="transparent")
        actions.pack(fill="x", pady=(0, 10))
        def _pick_and_analyze():
            file_path = filedialog.askopenfilename(title="Select a Windows dump file",
                                                   filetypes=[("Dump files", "*.dmp;*.mdmp;*.hdmp;*.dmp"), ("All files", "*.*")])
            if file_path:
                self.run_threaded(lambda: core.analyze_dump_file(file_path, timeout=30, open_report=True, sanitize=True), "ANALYZING DUMP...")
        GothicButton(actions, text="🧠 ANALYZE DUMP FILE (ADVANCED)", command=_pick_and_analyze).pack(side="left", fill="x", expand=True, padx=(0, 6))
        GothicButton(actions, text="⚡ REAL-TIME ANALYZE LATEST DUMP", command=lambda: self.run_threaded(core.analyze_latest_dump_realtime, "ANALYZING LATEST DUMP...")).pack(side="left", fill="x", expand=True)
        
        ctk.CTkLabel(self.main_area, text="RECENT CRASH HISTORY", font=(FONT_MAIN, 14, "bold"), text_color=COLOR_DIM).pack(anchor="w", pady=(10, 5))
        
        AccentButton(self.main_area, text="🔍 SCAN BSOD LOGS", command=self.show_bsod).pack(fill="x", pady=(0, 10))
        
        try:
            crashes = core.get_bsod_history()
        except Exception as e:
            crashes = []
            print(f"Error fetching BSOD history: {e}")

        history_frame = ctk.CTkScrollableFrame(self.main_area, fg_color=COLOR_SURFACE, height=150, border_color=COLOR_BORDER, border_width=1)
        history_frame.pack(fill="x", pady=(0, 20))
        
        if not crashes:
            ctk.CTkLabel(history_frame, text="No Recent Blue Screen Events Detected.", font=(FONT_MONO, 12), text_color="#22c55e").pack(pady=20)
        else:
            header = ctk.CTkFrame(history_frame, fg_color="transparent")
            header.pack(fill="x", pady=2)
            ctk.CTkLabel(header, text="DATE/TIME", font=(FONT_MAIN, 10, "bold"), text_color=COLOR_DIM, width=150, anchor="w").pack(side="left", padx=10)
            ctk.CTkLabel(header, text="ERROR CODE", font=(FONT_MAIN, 10, "bold"), text_color=COLOR_DIM, width=120, anchor="w").pack(side="left", padx=10)
            ctk.CTkLabel(header, text="CRASH TYPE", font=(FONT_MAIN, 10, "bold"), text_color=COLOR_DIM, anchor="w").pack(side="left", padx=10)

            detail_frame = ctk.CTkFrame(self.main_area, fg_color=COLOR_SURFACE, border_color=COLOR_BORDER, border_width=1, corner_radius=6)
            detail_frame.pack(fill="x", pady=(0, 20))
            ctk.CTkLabel(detail_frame, text="Select a crash above to view deep analysis and targeted fixes.", font=(FONT_MAIN, 11), text_color=COLOR_DIM, wraplength=800, justify="left").pack(anchor="w", padx=10, pady=10)

            for crash in crashes:
                row = ctk.CTkFrame(history_frame, fg_color="transparent")
                row.pack(fill="x", pady=2)
                
                time_str = crash.get('time', 'Unknown')
                code_str = crash.get('code', 'Unknown')
                insight = core.get_bsod_insight(code_str)
                name_str = insight.get("name", "Unknown")
                
                ctk.CTkLabel(row, text=time_str, font=(FONT_MONO, 11), text_color=COLOR_TEXT, width=150, anchor="w").pack(side="left", padx=10)
                ctk.CTkLabel(row, text=code_str, font=(FONT_MONO, 11, "bold"), text_color=COLOR_ACCENT, width=120, anchor="w").pack(side="left", padx=10)
                ctk.CTkLabel(row, text=name_str, font=(FONT_MAIN, 11), text_color=COLOR_TEXT, anchor="w").pack(side="left", padx=10)

                def _bind_row(widget, c=crash, i=insight):
                    def _on_click(event):
                        self.render_bsod_details(detail_frame, c, i)
                    widget.bind("<Button-1>", _on_click)
                    for child in widget.winfo_children():
                        child.bind("<Button-1>", _on_click)
                _bind_row(row)

        ctk.CTkLabel(self.main_area, text="RECOMMENDED FIXES", font=(FONT_MAIN, 14, "bold"), text_color=COLOR_DIM).pack(anchor="w", pady=(10, 5))
        
        btn_frame = ctk.CTkFrame(self.main_area, fg_color="transparent")
        btn_frame.pack(fill="x")
        
        GothicButton(btn_frame, text="🧠 RUN MEMORY DIAGNOSTIC (RESTART)", command=lambda: self.run_threaded(core.run_memory_diagnostic, "LAUNCHING MEMORY TOOL...")).pack(fill="x", pady=5)
        GothicButton(btn_frame, text="💾 SCAN DISK FOR ERRORS (CHKDSK)", command=lambda: self.run_threaded(core.run_chkdsk_scan, "RUNNING CHKDSK...")).pack(fill="x", pady=5)
        
        ctk.CTkLabel(self.main_area, textvariable=self.status_msg, font=(FONT_MONO, 11), text_color=COLOR_DIM).pack(side="bottom", anchor="w")

    def render_bsod_details(self, container, crash, insight):
        for widget in container.winfo_children():
            widget.destroy()
        time_str = crash.get("time", "Unknown")
        code_str = crash.get("code", "Unknown")
        name = insight.get("name", "Unknown")
        summary = insight.get("summary", "")
        actions = insight.get("actions", [])

        title = f"{name} ({code_str})"
        ctk.CTkLabel(container, text=title, font=(FONT_MAIN, 14, "bold"), text_color=COLOR_TEXT).pack(anchor="w", padx=10, pady=(10, 5))
        ctk.CTkLabel(container, text=f"Crash Time: {time_str}", font=(FONT_MONO, 11), text_color=COLOR_DIM).pack(anchor="w", padx=10)
        if summary:
            ctk.CTkLabel(container, text=summary, font=(FONT_MAIN, 11), text_color=COLOR_TEXT, wraplength=800, justify="left").pack(anchor="w", padx=10, pady=(5, 10))

        if actions:
            ctk.CTkLabel(container, text="Recommended actions:", font=(FONT_MAIN, 11, "bold"), text_color=COLOR_DIM).pack(anchor="w", padx=10)
            for step in actions:
                ctk.CTkLabel(container, text=f"• {step}", font=(FONT_MAIN, 11), text_color=COLOR_TEXT, wraplength=800, justify="left").pack(anchor="w", padx=18, pady=1)

        message = crash.get("message", "")
        if message:
            ctk.CTkLabel(container, text="Raw event message:", font=(FONT_MAIN, 11, "bold"), text_color=COLOR_DIM).pack(anchor="w", padx=10, pady=(8, 2))
            msg_frame = ctk.CTkScrollableFrame(container, fg_color=COLOR_SURFACE, height=120, border_color=COLOR_BORDER, border_width=1)
            msg_frame.pack(fill="x", padx=10, pady=(0, 8))
            ctk.CTkLabel(msg_frame, text=message, font=(FONT_MONO, 10), text_color=COLOR_TEXT, justify="left", anchor="w").pack(fill="x", padx=6, pady=4)

        button_frame = ctk.CTkFrame(container, fg_color="transparent")
        button_frame.pack(fill="x", padx=10, pady=(10, 10))

        GothicButton(button_frame, text="🧬 RUN SFC /SCANNOW", command=lambda: self.run_threaded(core.run_sfc, "RUNNING SFC /SCANNOW...")).pack(side="left", fill="x", expand=True, padx=(0, 5))
        GothicButton(button_frame, text="🩺 RUN DISM HEALTH CHECK", command=lambda: self.run_threaded(core.run_dism, "RUNNING DISM /RESTOREHEALTH...")).pack(side="left", fill="x", expand=True, padx=5)
        GothicButton(button_frame, text="🧾 OPEN MINIDUMP FOLDER", command=lambda: self.run_threaded(core.open_minidump_folder, "OPENING MINIDUMP FOLDER...")).pack(side="left", fill="x", expand=True, padx=5)
        GothicButton(button_frame, text="📤 EXPORT BSOD REPORT", command=lambda: self.run_threaded(core.export_bsod_report, "EXPORTING BSOD REPORT...")).pack(side="left", fill="x", expand=True, padx=(5, 0))
        
        info = ctk.CTkFrame(container, fg_color="transparent")
        info.pack(fill="x", padx=10, pady=(6, 2))
        ctk.CTkLabel(info, text="What these actions do:", font=(FONT_MAIN, 11, "bold"), text_color=COLOR_DIM).pack(anchor="w")
        ctk.CTkLabel(info, text="• SFC scans and repairs protected system files.", font=(FONT_MAIN, 10), text_color=COLOR_DIM).pack(anchor="w")
        ctk.CTkLabel(info, text="• DISM restores the Windows image when SFC isn’t enough.", font=(FONT_MAIN, 10), text_color=COLOR_DIM).pack(anchor="w")
        ctk.CTkLabel(info, text="• Minidump folder opens crash dump files for advanced analysis.", font=(FONT_MAIN, 10), text_color=COLOR_DIM).pack(anchor="w")
        ctk.CTkLabel(info, text="• Export report saves a text summary to your Desktop.", font=(FONT_MAIN, 10), text_color=COLOR_DIM).pack(anchor="w")

    def show_settings(self):
        self.set_active_nav("settings")
        self.clear_main()
        self.add_header("SETTINGS", "Configuration")

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

        GothicButton(sound_frame, text="📂 BROWSE...", width=100, command=_browse_sound).pack(side="right", padx=5)
        GothicButton(sound_frame, text="🔄 RESET", width=80, fg_color=COLOR_BORDER, command=_clear_sound).pack(side="right", padx=5)
        
        GothicButton(self.main_area, text="🔊 TEST PLAY SOUND", command=core.play_startup_sound).pack(fill="x", pady=20)

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
                      progress_color=COLOR_ACCENT, fg_color=COLOR_BORDER).pack(anchor="w")

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
                      progress_color=COLOR_ACCENT, fg_color=COLOR_BORDER).pack(anchor="w")

        ctk.CTkLabel(self.main_area, textvariable=self.status_msg, font=(FONT_MONO, 11), text_color=COLOR_DIM).pack(side="bottom", anchor="w")

    def show_about(self):
        self.set_active_nav("about")
        self.clear_main()
        card = ctk.CTkFrame(self.main_area, fg_color=COLOR_SURFACE, border_color=COLOR_BORDER, border_width=1, corner_radius=14)
        card.pack(fill="x", pady=(20, 0))
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=28, pady=32)
        ctk.CTkLabel(inner, text=f"PCFIX {APP_VERSION}", font=(FONT_DISPLAY, 34, "bold"), text_color=COLOR_ACCENT).pack(anchor="w")
        ctk.CTkLabel(inner, text="NECROMANCER  ·  ALL-IN-ONE WINDOWS TOOLKIT", font=(FONT_MONO, 12), text_color=COLOR_DIM).pack(anchor="w", pady=(6, 16))
        desc = ("Clean, repair, tweak, and diagnose Windows from a single dark UI.\n"
                "Debloat, privacy shield, network tools, and BSOD analysis included.")
        ctk.CTkLabel(inner, text=desc, font=(FONT_MAIN, 13), text_color=COLOR_TEXT, justify="left").pack(anchor="w")
        ctk.CTkLabel(inner, text="Developer  ·  DARKSIDE957", font=(FONT_MAIN, 13, "bold"), text_color=COLOR_TEXT).pack(anchor="w", pady=(22, 2))
        ctk.CTkLabel(inner, text="Discord  ·  _OMV", font=(FONT_MONO, 12), text_color=COLOR_ACCENT).pack(anchor="w")

        def open_link():
            import webbrowser
            webbrowser.open("https://github.com/DARKSIDE957/PCfix")

        GothicButton(inner, text="Open GitHub", command=open_link, width=180).pack(anchor="w", pady=(20, 0))
        ctk.CTkLabel(self.main_area, text="© 2026 DARKSIDE957", font=(FONT_MAIN, 10), text_color=COLOR_DIM).pack(side="bottom", pady=16)

    def show_boost(self):
        self.set_active_nav("boost")
        self.clear_main()
        self.add_header("PERFORMANCE BOOST", "Maximize system speed")
        
        GothicButton(self.main_area, text="🚀 ENABLE HIGH PERFORMANCE PLAN", command=lambda: self.run_threaded(core.enable_ultimate_performance, "ACTIVATING POWER PLAN...")).pack(fill="x", pady=5)
        GothicButton(self.main_area, text="💤 DISABLE HIBERNATION", command=lambda: self.run_threaded(core.disable_hibernation, "DISABLING HIBERNATION...")).pack(fill="x", pady=5)
        GothicButton(self.main_area, text="✨ OPTIMIZE VISUAL EFFECTS", command=lambda: self.run_threaded(core.optimize_visual_fx, "TWEAKING REGISTRY...")).pack(fill="x", pady=5)
        GothicButton(self.main_area, text="🎮 SET GPU HIGH PRIORITY", command=lambda: self.run_threaded(core.optimize_gpu_priority, "SETTING GPU PRIORITY...")).pack(fill="x", pady=5)

        ctk.CTkLabel(self.main_area, textvariable=self.status_msg, font=(FONT_MONO, 11), text_color=COLOR_DIM).pack(side="bottom", anchor="w")

    def monitor_loop(self):
        while self.running:
            try:
                stats = core.get_system_status()
                self.ui_enqueue(self.var_cpu.set, f"{stats['cpu']}%")
                self.ui_enqueue(self.var_ram.set, f"{stats['ram']}%")
                self.ui_enqueue(self.var_disk.set, f"{stats['disk']}%")
                
                if "battery" in stats:
                    plugged = "⚡" if stats.get("plugged") else "🔋"
                    self.ui_enqueue(self.var_battery.set, f"{plugged} {stats['battery']}%")
            except:
                pass
            time.sleep(3) # Optimized interval

    def show_info(self):
        self.set_active_nav("specs")
        self.clear_main()
        self.add_header("SYSTEM SPECIFICATIONS", "Hardware details")
        
        info = core.get_detailed_info()
        
        grid = ctk.CTkFrame(self.main_area, fg_color="transparent")
        grid.pack(fill="x")
        grid.columnconfigure(1, weight=1)
        
        row = 0
        keys = [('os', 'OS BUILD'), ('cpu', 'PROCESSOR'), ('gpu', 'GRAPHICS'), ('ram', 'MEMORY'), ('uptime', 'UPTIME')]
        if "battery" in info:
            keys.append(('battery', 'BATTERY'))

        for key, label in keys:
            ctk.CTkLabel(grid, text=label, font=(FONT_MAIN, 12, "bold"), text_color=COLOR_DIM).grid(row=row, column=0, sticky="nw", pady=5)
            ctk.CTkLabel(grid, text=info.get(key, "N/A"), font=(FONT_MONO, 12), text_color=COLOR_TEXT, wraplength=400, justify="left").grid(row=row, column=1, sticky="w", padx=20, pady=5)
            row += 1

        # Export Button
        GothicButton(self.main_area, text="💾 EXPORT SPECS TO FILE", command=lambda: self.run_threaded(core.export_system_info, "EXPORTING SPECS...")).pack(fill="x", pady=20)

        ctk.CTkLabel(self.main_area, textvariable=self.status_msg, font=(FONT_MONO, 11), text_color=COLOR_DIM).pack(side="bottom", anchor="w")

    def show_tools(self):
        self.set_active_nav("tools")
        self.clear_main()
        self.add_header("SYSTEM TOOLS", "Utilities and tweaks")
        
        # DNS Switcher
        ctk.CTkLabel(self.main_area, text="DNS CONFIGURATION", font=(FONT_MAIN, 14, "bold"), text_color=COLOR_DIM).pack(anchor="w", pady=(10, 5))
        dns_frame = ctk.CTkFrame(self.main_area, fg_color="transparent")
        dns_frame.pack(fill="x")
        
        GothicButton(dns_frame, text="GOOGLE DNS", command=lambda: self.run_threaded(core.set_dns_google, "SETTING GOOGLE DNS...")).pack(side="left", fill="x", expand=True, padx=(0, 2))
        GothicButton(dns_frame, text="CLOUDFLARE", command=lambda: self.run_threaded(core.set_dns_cloudflare, "SETTING CLOUDFLARE...")).pack(side="left", fill="x", expand=True, padx=2)
        GothicButton(dns_frame, text="AUTO (ISP)", command=lambda: self.run_threaded(core.set_dns_auto, "RESETTING DNS...")).pack(side="left", fill="x", expand=True, padx=(2, 0))
        
        # Gaming Mode
        ctk.CTkLabel(self.main_area, text="GAMING OPTIMIZATION", font=(FONT_MAIN, 14, "bold"), text_color=COLOR_DIM).pack(anchor="w", pady=(20, 5))
        GothicButton(self.main_area, text="🎮 ACTIVATE GAMING MODE", command=lambda: self.run_threaded(core.gaming_mode_on, "KILLING BACKGROUND APPS...")).pack(fill="x", pady=5)
        
        # Quick Launchers
        ctk.CTkLabel(self.main_area, text="QUICK ACCESS", font=(FONT_MAIN, 14, "bold"), text_color=COLOR_DIM).pack(anchor="w", pady=(20, 5))
        
        tools_grid = ctk.CTkFrame(self.main_area, fg_color="transparent")
        tools_grid.pack(fill="x")
        tools_grid.columnconfigure((0, 1), weight=1)
        
        GothicButton(tools_grid, text="TASK MANAGER", command=lambda: core.launch_tool("taskmgr")).grid(row=0, column=0, padx=(0, 5), pady=5, sticky="ew")
        GothicButton(tools_grid, text="REGISTRY EDITOR", command=lambda: core.launch_tool("regedit")).grid(row=0, column=1, padx=(5, 0), pady=5, sticky="ew")
        GothicButton(tools_grid, text="DEVICE MANAGER", command=lambda: core.launch_tool("devmgmt")).grid(row=1, column=0, padx=(0, 5), pady=5, sticky="ew")
        GothicButton(tools_grid, text="CONTROL PANEL", command=lambda: core.launch_tool("control")).grid(row=1, column=1, padx=(5, 0), pady=5, sticky="ew")
        
        # Reports
        ctk.CTkLabel(self.main_area, text="REPORTS", font=(FONT_MAIN, 14, "bold"), text_color=COLOR_DIM).pack(anchor="w", pady=(20, 5))
        GothicButton(self.main_area, text="🔋 GENERATE BATTERY HEALTH REPORT", command=lambda: self.run_threaded(core.generate_battery_report, "GENERATING REPORT...")).pack(fill="x", pady=5)
        
        ctk.CTkLabel(self.main_area, textvariable=self.status_msg, font=(FONT_MONO, 11), text_color=COLOR_DIM).pack(side="bottom", anchor="w")

    def show_network(self):
        self.set_active_nav("network")
        self.clear_main()
        self.add_header("NETWORK COMMANDER", "Latency and configuration")
        
        self.net_info = core.get_network_info()
        self.net_hidden = True
        
        # Info Grid
        grid = ctk.CTkFrame(self.main_area, fg_color=COLOR_SURFACE, corner_radius=10)
        grid.pack(fill="x", pady=(0, 20))
        grid.columnconfigure(1, weight=1)
        
        # Interface (Always Visible)
        ctk.CTkLabel(grid, text="INTERFACE", font=(FONT_MAIN, 12, "bold"), text_color=COLOR_DIM).grid(row=0, column=0, sticky="w", pady=10, padx=15)
        ctk.CTkLabel(grid, text=self.net_info.get('iface', 'N/A'), font=(FONT_MONO, 12), text_color=COLOR_TEXT).grid(row=0, column=1, sticky="w", padx=20, pady=10)
        
        self.net_labels = {}
        # Hidden Fields
        fields = [('ip', 'LOCAL IP'), ('gateway', 'GATEWAY'), ('mac', 'MAC ADDR')]
        for i, (key, label) in enumerate(fields, start=1):
            ctk.CTkLabel(grid, text=label, font=(FONT_MAIN, 12, "bold"), text_color=COLOR_DIM).grid(row=i, column=0, sticky="w", pady=5, padx=15)
            lbl = ctk.CTkLabel(grid, text="* HIDDEN *", font=(FONT_MONO, 12), text_color=COLOR_TEXT)
            lbl.grid(row=i, column=1, sticky="w", padx=20, pady=5)
            self.net_labels[key] = lbl
            
        # Toggle Button
        self.btn_toggle_net = GothicButton(self.main_area, text="👁️ SHOW SENSITIVE DATA", width=180, height=30, command=self.toggle_network_details)
        self.btn_toggle_net.pack(anchor="w", pady=(0, 20))
            
        # Ping Test
        ctk.CTkLabel(self.main_area, text="LATENCY TESTS", font=(FONT_MAIN, 14, "bold"), text_color=COLOR_DIM).pack(anchor="w", pady=(10, 5))
        
        ping_frame = ctk.CTkFrame(self.main_area, fg_color="transparent")
        ping_frame.pack(fill="x")
        
        self.lbl_ping_google = ctk.CTkLabel(ping_frame, text="GOOGLE: ...", font=(FONT_MONO, 12), text_color=COLOR_TEXT)
        self.lbl_ping_google.pack(side="left", padx=(0, 20))
        
        self.lbl_ping_cf = ctk.CTkLabel(ping_frame, text="CLOUDFLARE: ...", font=(FONT_MONO, 12), text_color=COLOR_TEXT)
        self.lbl_ping_cf.pack(side="left")
        
        GothicButton(self.main_area, text="📶 RUN PING TEST", command=self.run_ping_check).pack(fill="x", pady=10)
        
        # Reset Adapter
        ctk.CTkLabel(self.main_area, text="ADAPTER CONTROL", font=(FONT_MAIN, 14, "bold"), text_color=COLOR_DIM).pack(anchor="w", pady=(20, 5))
        GothicButton(self.main_area, text="🔄 RESET ADAPTER (RESTART WI-FI)", command=lambda: self.run_threaded(lambda: core.reset_adapter(self.net_info.get('iface', 'Wi-Fi')), "RESETTING ADAPTER...")).pack(fill="x", pady=5)
        
        ctk.CTkLabel(self.main_area, textvariable=self.status_msg, font=(FONT_MONO, 11), text_color=COLOR_DIM).pack(side="bottom", anchor="w")

    def toggle_network_details(self):
        self.net_hidden = not self.net_hidden
        
        if self.net_hidden:
            self.btn_toggle_net.configure(text="👁️ SHOW SENSITIVE DATA")
            for key, lbl in self.net_labels.items():
                lbl.configure(text="* HIDDEN *")
        else:
            self.btn_toggle_net.configure(text="🔒 HIDE SENSITIVE DATA")
            for key, lbl in self.net_labels.items():
                lbl.configure(text=self.net_info.get(key, "N/A"))

    def show_startup(self):
        self.set_active_nav("startup")
        self.clear_main()
        self.add_header("STARTUP MANAGER", "Control apps that start with Windows")
        
        # Scrollable list
        scroll = ctk.CTkScrollableFrame(self.main_area, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        
        apps = core.get_startup_apps()
        
        if not apps:
            ctk.CTkLabel(scroll, text="NO STARTUP APPS FOUND", font=(FONT_MAIN, 14), text_color=COLOR_DIM).pack(pady=20)
            return

        for app in apps:
            row = ctk.CTkFrame(scroll, fg_color=COLOR_SURFACE, border_color=COLOR_BORDER, border_width=1)
            row.pack(fill="x", pady=3)
            
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
            btn_col = COLOR_ACCENT if is_enabled else "#22c55e" # Green
            
            def _toggle(a=app):
                new_state = not a['enabled']
                if core.toggle_startup_app(a, new_state):
                    self.show_startup() # Refresh
                else:
                    self.status_msg.set("ERROR TOGGLING APP")

            GothicButton(row, text=btn_text, width=80, fg_color=btn_col, hover_color=btn_col, command=_toggle).pack(side="right", padx=10, pady=5)

    def run_threaded(self, target_func, start_msg="PROCESSING..."):
        self.status_msg.set(start_msg)
        
        def _wrapper():
            try:
                # Some core funcs return a string message, others print/return None
                # We assume they might return a result string
                res = target_func()
                if res and isinstance(res, str):
                    self.ui_enqueue(self.status_msg.set, res)
                else:
                    self.ui_enqueue(self.status_msg.set, "OPERATION COMPLETE")
            except Exception as e:
                self.ui_enqueue(self.status_msg.set, f"ERROR: {str(e)}")
        
        threading.Thread(target=_wrapper, daemon=True).start()

    def cmd_flush_dns(self):
        self.run_threaded(core.flush_dns, "FLUSHING DNS...")

    def cmd_optimize_ram(self):
        self.run_threaded(core.optimize_ram, "OPTIMIZING RAM...")

    def cmd_purge_temp(self):
        self.run_threaded(core.clean_temp_files, "CLEANING TEMP FILES...")
    
    def cmd_recycle_bin(self):
        self.run_threaded(core.empty_recycle_bin, "EMPTYING RECYCLE BIN...")

    def cmd_kill(self, proc_name):
        self.run_threaded(lambda: core.kill_process(proc_name), f"KILLING {proc_name.upper()}...")

    def run_ping_check(self):
        self.status_msg.set("PINGING...")
        self.lbl_ping_google.configure(text="GOOGLE: ...")
        self.lbl_ping_cf.configure(text="CLOUDFLARE: ...")
        
        def _ping_g():
            p1 = core.run_ping_test("8.8.8.8")
            self.ui_enqueue(self.lbl_ping_google.configure, text=f"GOOGLE: {p1}")

        def _ping_c():
            p2 = core.run_ping_test("1.1.1.1")
            self.ui_enqueue(self.lbl_ping_cf.configure, text=f"CLOUDFLARE: {p2}")
            
        def _check():
            t1 = threading.Thread(target=_ping_g, daemon=True)
            t2 = threading.Thread(target=_ping_c, daemon=True)
            t1.start()
            t2.start()
            t1.join()
            t2.join()
            self.ui_enqueue(self.status_msg.set, "PING TEST COMPLETE")
            
        threading.Thread(target=_check, daemon=True).start()

    def _ensure_tray(self):
        if getattr(self, "_tray", None):
            return True
        try:
            import pystray
            from pystray import MenuItem as item
        except Exception:
            return False
        try:
            img = Image.open(resource_path("icon.ico"))
        except Exception:
            img = Image.new("RGB", (64, 64), color=(220, 38, 38))

        def _show(icon, _item):
            self.after(0, self.deiconify)
            self.after(0, self.lift)

        def _quit(icon, _item):
            self.running = False
            icon.stop()
            self.after(0, self.destroy)

        menu = pystray.Menu(item("Show PCFIX", _show), item("Exit", _quit))
        self._tray = pystray.Icon("pcfix", img, "PCFIX", menu)
        threading.Thread(target=self._tray.run, daemon=True).start()
        return True

    def on_close(self):
        if self.config.get("minimize_to_tray", False):
            if self._ensure_tray():
                self.withdraw()
                self.status_msg.set("MINIMIZED TO TRAY")
                return
        self.running = False
        tray = getattr(self, "_tray", None)
        if tray:
            try:
                tray.stop()
            except Exception:
                pass
        self.destroy()
        sys.exit()

class PCFixWebApi:
    def __init__(self):
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=6)
        self._jobs = {}
        self._log_file = self._resolve_log_file()
        self._log("WEB_APP_START")

    def _resolve_log_file(self):
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        folder = os.path.join(base, "PCFIX")
        os.makedirs(folder, exist_ok=True)
        return os.path.join(folder, "pcfix_web.log")

    def _log(self, message):
        try:
            ts = time.strftime("%Y-%m-%d %H:%M:%S")
            with open(self._log_file, "a", encoding="utf-8") as f:
                f.write(f"[{ts}] {message}\n")
        except Exception:
            pass

    def ping(self):
        return {"ok": True, "version": APP_VERSION}

    def minimize(self):
        try:
            import webview
            webview.windows[0].minimize()
            return True
        except Exception as e:
            self._log(f"MINIMIZE_ERROR {e}")
            return False

    def toggle_maximize(self):
        try:
            import webview
            w = webview.windows[0]
            if getattr(w, "maximized", False):
                w.restore()
                w.maximized = False
            else:
                w.maximize()
                w.maximized = True
            return True
        except Exception as e:
            self._log(f"MAXIMIZE_ERROR {e}")
            return False

    def close(self):
        try:
            import webview
            webview.windows[0].destroy()
            return True
        except Exception as e:
            self._log(f"CLOSE_ERROR {e}")
            return False

    def get_system_status(self):
        return core.get_system_status()

    def get_detailed_info(self):
        return core.get_detailed_info()

    def get_network_info(self):
        return core.get_network_info()

    def get_startup_apps(self):
        return core.get_startup_apps()

    def toggle_startup_app(self, app, enable):
        return core.toggle_startup_app(app, enable)

    def get_bsod_history(self):
        return core.get_bsod_history()

    def run_task(self, task_name, payload=None):
        payload = payload or {}
        task_id = str(uuid.uuid4())

        def _run():
            return self._execute_task(task_name, payload)

        future = self._executor.submit(_run)
        self._jobs[task_id] = future
        self._log(f"TASK_START {task_id} {task_name}")
        return {"task_id": task_id}

    def task_status(self, task_id):
        f = self._jobs.get(task_id)
        if not f:
            return {"done": True, "error": "Unknown task id"}
        if not f.done():
            return {"done": False}
        try:
            res = f.result()
            return {"done": True, "result": res}
        except Exception as e:
            self._log(f"TASK_ERROR {task_id} {e}")
            self._log(traceback.format_exc())
            return {"done": True, "error": str(e)}

    def _execute_task(self, task_name, payload):
        if task_name == "flush_dns":
            return core.flush_dns()
        if task_name == "optimize_ram":
            return core.optimize_ram()
        if task_name == "clean_temp_files":
            return core.clean_temp_files()
        if task_name == "empty_recycle_bin":
            return core.empty_recycle_bin()
        if task_name == "run_sfc":
            return core.run_sfc()
        if task_name == "run_dism":
            return core.run_dism()
        if task_name == "run_smart_scan":
            return core.run_smart_scan()
        if task_name == "reset_network":
            return core.reset_network()
        if task_name == "reset_winsock":
            return core.reset_winsock()
        if task_name == "set_dns_cloudflare":
            return core.set_dns_cloudflare()
        if task_name == "restore_dns_dhcp":
            return core.restore_dns_dhcp()
        if task_name == "run_ping":
            host = payload.get("host", "8.8.8.8")
            return core.run_ping_test(host)
        if task_name == "run_chkdsk_scan":
            return core.run_chkdsk_scan()
        if task_name == "export_bsod_report":
            return core.export_bsod_report()
        if task_name == "analyze_latest_dump":
            return core.analyze_latest_dump_realtime(timeout=int(payload.get("timeout", 30)))
        if task_name == "get_installed_bloatware":
            return core.get_installed_bloatware()
        if task_name == "apply_privacy_shield":
            return core.apply_privacy_shield()
        return f"Unknown task: {task_name}"

def run_chromium_ui():
    if not core.is_admin():
        core.elevate()
        return

    try:
        import webview
    except Exception:
        try:
            messagebox.showerror("Missing Dependency", "pywebview is not installed. Run: python -m pip install pywebview")
        except Exception:
            pass
        app = App()
        app.mainloop()
        return

    html = r"""
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>PCFIX</title>
    <style>
      :root{
        --bg:#09090b;
        --surface:#18181b;
        --border:#27272a;
        --text:#fafafa;
        --muted:#a1a1aa;
        --muted2:#71717a;
        --accent:#dc2626;
        --accent2:#ef4444;
        --good:#22c55e;
        --shadow: 0 12px 34px rgba(0,0,0,.45);
      }
      *{ box-sizing:border-box; }
      html,body{ height:100%; }
      body{
        margin:0;
        font-family: "Segoe UI", system-ui, -apple-system, Arial, sans-serif;
        color:var(--text);
        background: radial-gradient(1200px 700px at 15% 15%, rgba(220,38,38,.16), transparent 55%),
                    radial-gradient(900px 600px at 85% 25%, rgba(239,68,68,.10), transparent 50%),
                    var(--bg);
        overflow:hidden;
      }
      .app{
        height:100%;
        display:grid;
        grid-template-rows: 44px 1fr;
      }
      .titlebar{
        display:flex;
        align-items:center;
        gap:10px;
        padding:0 12px;
        background: rgba(24,24,27,.88);
        border-bottom:1px solid var(--border);
        -webkit-app-region: drag;
        user-select:none;
      }
      .brand{
        display:flex;
        align-items:center;
        gap:10px;
        font-weight:700;
        letter-spacing:.4px;
      }
      .badge{
        font-size:11px;
        padding:3px 8px;
        border:1px solid var(--border);
        border-radius:999px;
        color:var(--muted);
        background: rgba(9,9,11,.35);
      }
      .spacer{ flex:1; }
      .winbtns{
        display:flex;
        gap:8px;
        -webkit-app-region: no-drag;
      }
      .winbtn{
        width:34px;
        height:28px;
        border:1px solid var(--border);
        background: rgba(9,9,11,.25);
        color:var(--text);
        border-radius:8px;
        cursor:pointer;
        transition: transform .12s ease, background .12s ease, border-color .12s ease;
      }
      .winbtn:hover{
        transform: translateY(-1px);
        background: rgba(39,39,42,.55);
        border-color: rgba(255,255,255,.12);
      }
      .winbtn.close:hover{
        background: rgba(220,38,38,.25);
        border-color: rgba(220,38,38,.45);
      }
      .content{
        display:grid;
        grid-template-columns: 250px 1fr;
        height:100%;
      }
      .sidebar{
        background: rgba(24,24,27,.78);
        border-right:1px solid var(--border);
        padding:14px 10px;
      }
      .nav{
        display:flex;
        flex-direction:column;
        gap:6px;
      }
      .nav button{
        border:1px solid transparent;
        background: transparent;
        color: var(--muted);
        text-align:left;
        padding:10px 12px;
        border-radius:10px;
        cursor:pointer;
        font-size:13px;
        letter-spacing:.2px;
        transition: background .14s ease, border-color .14s ease, color .14s ease, transform .14s ease;
      }
      .nav button:hover{
        background: rgba(39,39,42,.45);
        transform: translateX(2px);
      }
      .nav button.active{
        background: rgba(39,39,42,.65);
        border-color: rgba(255,255,255,.08);
        color: var(--text);
      }
      .main{
        padding:18px 18px 14px 18px;
        overflow:hidden;
      }
      .page{
        height:100%;
        display:flex;
        flex-direction:column;
        gap:14px;
        opacity:0;
        transform: translateY(6px);
        transition: opacity .18s ease, transform .18s ease;
      }
      .page.show{
        opacity:1;
        transform: translateY(0);
      }
      .header h1{
        margin:0;
        font-size:22px;
        letter-spacing:.6px;
      }
      .header p{
        margin:6px 0 0 0;
        color: var(--muted2);
        font-size:12px;
      }
      .grid{
        display:grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap:12px;
      }
      .card{
        background: rgba(24,24,27,.72);
        border:1px solid var(--border);
        border-radius:14px;
        padding:14px;
        box-shadow: var(--shadow);
        min-height:94px;
      }
      .card .k{
        color: var(--muted2);
        font-size:11px;
        font-weight:700;
        letter-spacing:.5px;
      }
      .card .v{
        margin-top:10px;
        font-size:26px;
        font-family: Consolas, "SFMono-Regular", Menlo, monospace;
        font-weight:800;
      }
      .actions{
        display:flex;
        gap:10px;
        flex-wrap:wrap;
      }
      .btn{
        border:1px solid var(--border);
        background: rgba(9,9,11,.22);
        color: var(--text);
        padding:10px 12px;
        border-radius:12px;
        cursor:pointer;
        font-weight:700;
        font-size:12px;
        letter-spacing:.3px;
        transition: transform .12s ease, background .12s ease, border-color .12s ease;
      }
      .btn:hover{
        transform: translateY(-1px);
        background: rgba(39,39,42,.55);
        border-color: rgba(255,255,255,.12);
      }
      .btn.primary{
        background: rgba(220,38,38,.88);
        border-color: rgba(220,38,38,.55);
      }
      .btn.primary:hover{
        background: rgba(239,68,68,.92);
        border-color: rgba(239,68,68,.75);
      }
      .panel{
        flex:1;
        overflow:auto;
        border:1px solid var(--border);
        border-radius:14px;
        background: rgba(24,24,27,.60);
        padding:14px;
      }
      .panel pre{
        margin:0;
        white-space:pre-wrap;
        word-break: break-word;
        font-family: Consolas, "SFMono-Regular", Menlo, monospace;
        font-size:11px;
        color: var(--muted);
      }
      .status{
        display:flex;
        align-items:center;
        gap:10px;
        padding:10px 12px;
        border-top:1px solid var(--border);
        color: var(--muted2);
        font-size:11px;
        background: rgba(24,24,27,.55);
      }
      .dot{
        width:8px;
        height:8px;
        border-radius:999px;
        background: var(--good);
        box-shadow: 0 0 0 4px rgba(34,197,94,.14);
      }
      a{ color: var(--accent2); }
    </style>
  </head>
  <body>
    <div class="app">
      <div class="titlebar pywebview-drag-region">
        <div class="brand">
          <div>PCFIX</div>
          <div class="badge">Chromium UI</div>
        </div>
        <div class="spacer"></div>
        <div class="winbtns">
          <button class="winbtn" id="minBtn" title="Minimize">—</button>
          <button class="winbtn" id="maxBtn" title="Maximize">▢</button>
          <button class="winbtn close" id="closeBtn" title="Close">✕</button>
        </div>
      </div>
      <div class="content">
        <aside class="sidebar">
          <div class="nav" id="nav">
            <button data-page="dashboard" class="active">📊 Dashboard</button>
            <button data-page="cleaner">🧹 Cleaner</button>
            <button data-page="repair">🔧 Repair</button>
            <button data-page="network">🌐 Network</button>
            <button data-page="startup">🚦 Startup</button>
            <button data-page="bsod">☠️ BSOD</button>
            <button data-page="settings">⚙️ Settings</button>
            <button data-page="about">ℹ️ About</button>
          </div>
        </aside>
        <main class="main">
          <section class="page show" id="page"></section>
        </main>
      </div>
      <div class="status">
        <div class="dot" id="dot"></div>
        <div id="statusText">READY</div>
      </div>
    </div>
    <script>
      const state = {
        page: 'dashboard',
        task: null
      };

      const $ = (sel) => document.querySelector(sel);
      const pageEl = $('#page');
      const statusText = $('#statusText');

      function setStatus(msg) {
        statusText.textContent = msg;
      }

      async function apiCall(fn, ...args) {
        if (!window.pywebview || !window.pywebview.api || !window.pywebview.api[fn]) {
          throw new Error('pywebview api not available: ' + fn);
        }
        return await window.pywebview.api[fn](...args);
      }

      function renderHeader(title, subtitle) {
        return `
          <div class="header">
            <h1>${title}</h1>
            <p>${subtitle || ''}</p>
          </div>
        `;
      }

      function renderDashboardShell() {
        return `
          ${renderHeader('SYSTEM OVERVIEW', 'Real-time metrics and quick actions')}
          <div class="grid">
            <div class="card"><div class="k">CPU LOAD</div><div class="v" id="cpu">0%</div></div>
            <div class="card"><div class="k">RAM USAGE</div><div class="v" id="ram">0%</div></div>
            <div class="card"><div class="k">DISK USAGE</div><div class="v" id="disk">0%</div></div>
          </div>
          <div class="actions">
            <button class="btn primary" id="smartScanBtn">⚡ RUN SMART SCAN</button>
            <button class="btn" id="flushDnsBtn">🌐 FLUSH DNS</button>
            <button class="btn" id="optRamBtn">🧹 OPTIMIZE RAM</button>
          </div>
          <div class="panel"><pre id="log">Select an action to run.</pre></div>
        `;
      }

      function renderCleaner() {
        return `
          ${renderHeader('CLEANER', 'Space cleanup and quick protocols')}
          <div class="actions">
            <button class="btn primary" id="purgeTempBtn">🗑️ PURGE TEMP FILES</button>
            <button class="btn" id="recycleBtn">♻️ EMPTY RECYCLE BIN</button>
            <button class="btn" id="winsockBtn">🔄 RESET WINSOCK</button>
          </div>
          <div class="panel"><pre id="log">Ready.</pre></div>
        `;
      }

      function renderRepair() {
        return `
          ${renderHeader('REPAIR', 'System repair commands')}
          <div class="actions">
            <button class="btn primary" id="sfcBtn">🧰 RUN SFC /SCANNOW</button>
            <button class="btn" id="dismBtn">🩺 RUN DISM /RESTOREHEALTH</button>
            <button class="btn" id="resetNetBtn">🔌 RESET NETWORK STACK</button>
          </div>
          <div class="panel"><pre id="log">Ready.</pre></div>
        `;
      }

      function renderNetwork() {
        return `
          ${renderHeader('NETWORK', 'Latency and configuration')}
          <div class="actions">
            <button class="btn" id="dnsCfBtn">🌐 SET DNS: CLOUDFLARE</button>
            <button class="btn" id="dnsDhcpBtn">🌐 RESTORE DNS: DHCP</button>
            <button class="btn" id="pingGoogleBtn">📶 PING 8.8.8.8</button>
          </div>
          <div class="panel"><pre id="log">Loading network info…</pre></div>
        `;
      }

      function renderStartup() {
        return `
          ${renderHeader('STARTUP', 'Toggle startup apps')}
          <div class="panel"><pre id="log">Loading startup entries…</pre></div>
        `;
      }

      function renderBsod() {
        return `
          ${renderHeader('BSOD', 'Crash history viewer')}
          <div class="panel"><pre id="log">Loading crash history…</pre></div>
        `;
      }

      function renderSettings() {
        return `
          ${renderHeader('SETTINGS', 'Configuration')}
          <div class="panel"><pre id="log">This Chromium UI is a new shell. Existing settings stay in config.json.</pre></div>
        `;
      }

      function renderAbout() {
        return `
          ${renderHeader('ABOUT', 'PCFIX | Chromium UI')}
          <div class="panel">
            <pre id="log">Modern Chromium interface (WebView2) with Python backend.\n\nLog: %LOCALAPPDATA%\\PCFIX\\pcfix_web.log</pre>
          </div>
        `;
      }

      function setActiveNav(page) {
        document.querySelectorAll('#nav button').forEach(b => {
          b.classList.toggle('active', b.dataset.page === page);
        });
      }

      async function startTask(taskName, payload) {
        setStatus('RUNNING: ' + taskName);
        const logEl = $('#log');
        if (logEl) logEl.textContent = 'Starting…';
        const r = await apiCall('run_task', taskName, payload || {});
        const taskId = r.task_id;
        while (true) {
          const s = await apiCall('task_status', taskId);
          if (!s.done) {
            await new Promise(res => setTimeout(res, 250));
            continue;
          }
          if (s.error) {
            setStatus('ERROR');
            if (logEl) logEl.textContent = s.error;
            return;
          }
          setStatus('DONE');
          if (logEl) logEl.textContent = typeof s.result === 'string' ? s.result : JSON.stringify(s.result, null, 2);
          return;
        }
      }

      async function render(page) {
        state.page = page;
        setActiveNav(page);
        pageEl.classList.remove('show');
        await new Promise(res => setTimeout(res, 90));

        if (page === 'dashboard') pageEl.innerHTML = renderDashboardShell();
        else if (page === 'cleaner') pageEl.innerHTML = renderCleaner();
        else if (page === 'repair') pageEl.innerHTML = renderRepair();
        else if (page === 'network') pageEl.innerHTML = renderNetwork();
        else if (page === 'startup') pageEl.innerHTML = renderStartup();
        else if (page === 'bsod') pageEl.innerHTML = renderBsod();
        else if (page === 'settings') pageEl.innerHTML = renderSettings();
        else if (page === 'about') pageEl.innerHTML = renderAbout();
        else pageEl.innerHTML = renderDashboardShell();

        pageEl.classList.add('show');

        if (page === 'dashboard') {
          $('#smartScanBtn').addEventListener('click', () => startTask('run_smart_scan'));
          $('#flushDnsBtn').addEventListener('click', () => startTask('flush_dns'));
          $('#optRamBtn').addEventListener('click', () => startTask('optimize_ram'));
        }
        if (page === 'cleaner') {
          $('#purgeTempBtn').addEventListener('click', () => startTask('clean_temp_files'));
          $('#recycleBtn').addEventListener('click', () => startTask('empty_recycle_bin'));
          $('#winsockBtn').addEventListener('click', () => startTask('reset_winsock'));
        }
        if (page === 'repair') {
          $('#sfcBtn').addEventListener('click', () => startTask('run_sfc'));
          $('#dismBtn').addEventListener('click', () => startTask('run_dism'));
          $('#resetNetBtn').addEventListener('click', () => startTask('reset_network'));
        }
        if (page === 'network') {
          $('#dnsCfBtn').addEventListener('click', () => startTask('set_dns_cloudflare'));
          $('#dnsDhcpBtn').addEventListener('click', () => startTask('restore_dns_dhcp'));
          $('#pingGoogleBtn').addEventListener('click', () => startTask('run_ping', { host: '8.8.8.8' }));
          const info = await apiCall('get_network_info');
          $('#log').textContent = JSON.stringify(info, null, 2);
        }
        if (page === 'startup') {
          const apps = await apiCall('get_startup_apps');
          $('#log').textContent = JSON.stringify(apps, null, 2);
        }
        if (page === 'bsod') {
          const crashes = await apiCall('get_bsod_history');
          $('#log').textContent = JSON.stringify(crashes, null, 2);
        }
      }

      async function updateStats() {
        if (state.page !== 'dashboard') return;
        try {
          const st = await apiCall('get_system_status');
          const cpu = $('#cpu');
          const ram = $('#ram');
          const disk = $('#disk');
          if (cpu) cpu.textContent = (st.cpu ?? 0) + '%';
          if (ram) ram.textContent = (st.ram ?? 0) + '%';
          if (disk) disk.textContent = (st.disk ?? 0) + '%';
        } catch (e) {
          setStatus('DISCONNECTED');
        }
      }

      function wireWindowButtons() {
        $('#minBtn').addEventListener('click', () => apiCall('minimize'));
        $('#maxBtn').addEventListener('click', () => apiCall('toggle_maximize'));
        $('#closeBtn').addEventListener('click', () => apiCall('close'));
      }

      function wireNavigation() {
        document.querySelectorAll('#nav button').forEach(btn => {
          btn.addEventListener('click', () => render(btn.dataset.page));
        });
      }

      window.addEventListener('load', async () => {
        wireWindowButtons();
        wireNavigation();
        await render('dashboard');
        setInterval(updateStats, 1500);
        setStatus('READY');
      });
    </script>
  </body>
</html>
"""

    api = PCFixWebApi()
    webview.create_window("PCFIX", html=html, js_api=api, width=1200, height=850, min_size=(900, 650), frameless=True, easy_drag=False)
    webview.start(gui="edgechromium")

def _debug_log_ui(mode):
    # #region agent log
    try:
        import json as _json
        _path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug-3a9129.log")
        _entry = {
            "sessionId": "3a9129",
            "runId": os.environ.get("PCFIX_RUN_ID", "app-start"),
            "hypothesisId": "H-ui",
            "location": "main:__main__",
            "message": "ui_launch",
            "data": {"mode": mode, "admin": core.is_admin()},
            "timestamp": int(time.time() * 1000),
        }
        with open(_path, "a", encoding="utf-8") as _f:
            _f.write(_json.dumps(_entry) + "\n")
    except Exception:
        pass
    # #endregion


if __name__ == "__main__":
    use_webview = "--webview" in sys.argv or os.environ.get("PCFIX_UI", "").lower() == "webview"
    if use_webview:
        _debug_log_ui("webview")
        run_chromium_ui()
    else:
        _debug_log_ui("tkinter")
        if not core.is_admin():
            core.elevate()
        app = App()
        app.mainloop()
