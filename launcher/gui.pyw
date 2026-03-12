"""
Autify Engine V1 - Desktop Launcher GUI
Standalone tkinter application for managing all services.
Zero additional dependencies -- ships with Python 3.11+.

Features:
  - Start / Stop / Restart all services (backend, dashboard, LLM)
  - Real-time service status indicators (green/red/yellow)
  - NoBrowser & Docker-mode toggle
  - Opens dashboard in Edge/Chrome app mode
  - Auto-refreshes status every 3 seconds
"""

import os
import sys
import subprocess
import threading
import socket
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

# ── Paths & Config ────────────────────────────────────────────────────

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAUNCHER_DIR = os.path.dirname(os.path.abspath(__file__))

BACKEND_PORT = int(os.environ.get("BACKEND_PORT", "18080"))
DASHBOARD_PORT = int(os.environ.get("DASHBOARD_PORT", "18300"))
LLM_PORT = int(os.environ.get("LLM_PORT", "11434"))

PYTHON_BASE = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Python", "Python311")
NODE_BASE = os.path.join(os.environ.get("ProgramFiles", ""), "nodejs")

# Ensure PATH includes Python + Node for all subprocess calls
for p in [PYTHON_BASE, os.path.join(PYTHON_BASE, "Scripts"), NODE_BASE]:
    if os.path.exists(p) and p not in os.environ.get("Path", ""):
        os.environ["Path"] = p + ";" + os.environ["Path"]


def _find_python_exe():
    """Resolve python.exe (NOT pythonw.exe) for launching subprocesses.
    pythonw.exe suppresses stdout/stderr which breaks uvicorn and other tools."""
    # 1. Check alongside this interpreter
    base = os.path.dirname(sys.executable)
    candidate = os.path.join(base, "python.exe")
    if os.path.exists(candidate):
        return candidate
    # 2. Known install path
    candidate = os.path.join(PYTHON_BASE, "python.exe")
    if os.path.exists(candidate):
        return candidate
    # 3. PATH search
    import shutil
    found = shutil.which("python")
    if found:
        return found
    # 4. Fall back to sys.executable (may be pythonw)
    return sys.executable


def _find_npm():
    """Resolve npm.cmd path for launching dashboard."""
    # 1. Known Node.js install path
    candidate = os.path.join(NODE_BASE, "npm.cmd")
    if os.path.exists(candidate):
        return candidate
    # 2. PATH search
    import shutil
    found = shutil.which("npm")
    if found:
        return found
    return "npm"  # Hope it's in PATH


PYTHON_EXE = _find_python_exe()
NPM_CMD = _find_npm()


# ── Service Management ────────────────────────────────────────────────

def is_port_listening(port):
    """Check if a port has a listener (tries IPv4 then IPv6)."""
    for host in ("127.0.0.1", "::1"):
        try:
            family = socket.AF_INET if host == "127.0.0.1" else socket.AF_INET6
            with socket.socket(family, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                if s.connect_ex((host, port)) == 0:
                    return True
        except Exception:
            continue
    return False


def kill_port(port):
    """Kill process listening on a given port (Windows)."""
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             f"Get-NetTCPConnection -LocalPort {port} -State Listen -ErrorAction SilentlyContinue | "
             f"ForEach-Object {{ Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }}"],
            capture_output=True, timeout=10
        )
    except Exception:
        pass


def check_health(port, path="/health"):
    """HTTP health check."""
    try:
        import urllib.request
        url = f"http://127.0.0.1:{port}{path}"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.status == 200
    except Exception:
        return False


def find_browser():
    """Find Edge or Chrome for app-mode launch."""
    candidates = [
        os.path.join(os.environ.get("ProgramFiles", ""), "Microsoft", "Edge", "Application", "msedge.exe"),
        os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Microsoft", "Edge", "Application", "msedge.exe"),
        os.path.join(os.environ.get("ProgramFiles", ""), "Google", "Chrome", "Application", "chrome.exe"),
        os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Google", "Chrome", "Application", "chrome.exe"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


# ── GUI Application ──────────────────────────────────────────────────

class AutifyLauncherApp:
    """Main GUI application for Autify Engine service management."""

    # Color palette matching brand
    BG          = "#0f172a"   # brand-950
    BG_CARD     = "#1e293b"   # brand-900
    FG          = "#f8fafc"   # white
    FG_DIM      = "#94a3b8"   # brand-400
    ACCENT      = "#3b82f6"   # brand-500
    ACCENT_HOVER= "#2563eb"   # brand-600
    GREEN       = "#22c55e"
    RED         = "#ef4444"
    AMBER       = "#f59e0b"
    BORDER      = "#334155"   # brand-700

    def __init__(self, root):
        self.root = root
        self.root.title("Autify Engine V1")
        self.root.geometry("520x680")
        self.root.resizable(False, False)
        self.root.configure(bg=self.BG)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Try to set icon
        ico_path = os.path.join(LAUNCHER_DIR, "autify.ico")
        if os.path.exists(ico_path):
            try:
                self.root.iconbitmap(ico_path)
            except Exception:
                pass

        # State
        self._running = True
        self._backend_pid = None
        self._dashboard_pid = None
        self._log_lines = []

        # Build UI
        self._build_header()
        self._build_status_panel()
        self._build_controls()
        self._build_options()
        self._build_log_panel()
        self._build_footer()

        # Start status polling
        self._poll_status()

    # ── Header ────────────────────────────────────────────────

    def _build_header(self):
        frame = tk.Frame(self.root, bg=self.BG)
        frame.pack(fill="x", padx=20, pady=(18, 0))

        # Logo + Title row
        logo = tk.Label(frame, text=" AE ", bg=self.ACCENT, fg="white",
                        font=("Segoe UI", 14, "bold"), padx=6, pady=2)
        logo.pack(side="left")

        title_frame = tk.Frame(frame, bg=self.BG)
        title_frame.pack(side="left", padx=(10, 0))

        tk.Label(title_frame, text="Autify Engine V1", bg=self.BG, fg=self.FG,
                 font=("Segoe UI", 16, "bold")).pack(anchor="w")
        tk.Label(title_frame, text="Zero-Cloud  |  Draft-Only  |  Secure",
                 bg=self.BG, fg=self.FG_DIM, font=("Segoe UI", 9)).pack(anchor="w")

    # ── Status Panel ──────────────────────────────────────────

    def _build_status_panel(self):
        outer = tk.Frame(self.root, bg=self.BG)
        outer.pack(fill="x", padx=20, pady=(16, 0))

        tk.Label(outer, text="SERVICE STATUS", bg=self.BG, fg=self.FG_DIM,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(0, 6))

        card = tk.Frame(outer, bg=self.BG_CARD, highlightbackground=self.BORDER,
                        highlightthickness=1, padx=16, pady=12)
        card.pack(fill="x")

        self.status_indicators = {}
        services = [
            ("backend",   f"Backend API",        f"Port {BACKEND_PORT}"),
            ("dashboard", f"React Dashboard",    f"Port {DASHBOARD_PORT}"),
            ("llm",       f"Local LLM (Ollama)", f"Port {LLM_PORT}"),
        ]

        for i, (key, name, detail) in enumerate(services):
            row = tk.Frame(card, bg=self.BG_CARD)
            row.pack(fill="x", pady=(0 if i == 0 else 6, 0))

            indicator = tk.Canvas(row, width=12, height=12, bg=self.BG_CARD,
                                  highlightthickness=0)
            indicator.pack(side="left", padx=(0, 10))
            dot = indicator.create_oval(1, 1, 11, 11, fill=self.RED, outline="")

            tk.Label(row, text=name, bg=self.BG_CARD, fg=self.FG,
                     font=("Segoe UI", 10, "bold")).pack(side="left")
            status_label = tk.Label(row, text="Stopped", bg=self.BG_CARD,
                                    fg=self.RED, font=("Segoe UI", 9))
            status_label.pack(side="right")
            tk.Label(row, text=f"  {detail}", bg=self.BG_CARD, fg=self.FG_DIM,
                     font=("Segoe UI", 9)).pack(side="left")

            self.status_indicators[key] = {
                "canvas": indicator, "dot": dot, "label": status_label
            }

    # ── Control Buttons ───────────────────────────────────────

    def _build_controls(self):
        outer = tk.Frame(self.root, bg=self.BG)
        outer.pack(fill="x", padx=20, pady=(16, 0))

        tk.Label(outer, text="CONTROLS", bg=self.BG, fg=self.FG_DIM,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(0, 6))

        btn_frame = tk.Frame(outer, bg=self.BG)
        btn_frame.pack(fill="x")

        btn_style = {
            "font": ("Segoe UI", 10, "bold"),
            "relief": "flat",
            "cursor": "hand2",
            "padx": 16, "pady": 8,
            "borderwidth": 0,
        }

        self.btn_start = tk.Button(btn_frame, text="  Start All  ",
                                   bg=self.GREEN, fg="white",
                                   activebackground="#16a34a",
                                   command=self._start_all, **btn_style)
        self.btn_start.pack(side="left", padx=(0, 8))

        self.btn_stop = tk.Button(btn_frame, text="  Stop All  ",
                                  bg=self.RED, fg="white",
                                  activebackground="#dc2626",
                                  command=self._stop_all, **btn_style)
        self.btn_stop.pack(side="left", padx=(0, 8))

        self.btn_restart = tk.Button(btn_frame, text="  Restart  ",
                                     bg=self.AMBER, fg="white",
                                     activebackground="#d97706",
                                     command=self._restart_all, **btn_style)
        self.btn_restart.pack(side="left", padx=(0, 8))

        self.btn_dashboard = tk.Button(btn_frame, text="  Open Dashboard  ",
                                       bg=self.ACCENT, fg="white",
                                       activebackground=self.ACCENT_HOVER,
                                       command=self._open_dashboard, **btn_style)
        self.btn_dashboard.pack(side="left")

    # ── Options ───────────────────────────────────────────────

    def _build_options(self):
        outer = tk.Frame(self.root, bg=self.BG)
        outer.pack(fill="x", padx=20, pady=(16, 0))

        tk.Label(outer, text="OPTIONS", bg=self.BG, fg=self.FG_DIM,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(0, 6))

        opts = tk.Frame(outer, bg=self.BG_CARD, highlightbackground=self.BORDER,
                        highlightthickness=1, padx=16, pady=10)
        opts.pack(fill="x")

        self.var_no_browser = tk.BooleanVar(value=False)
        self.var_docker_mode = tk.BooleanVar(value=False)

        cb_style = {"bg": self.BG_CARD, "fg": self.FG, "selectcolor": self.BG,
                     "activebackground": self.BG_CARD, "activeforeground": self.FG,
                     "font": ("Segoe UI", 9)}

        tk.Checkbutton(opts, text="Don't open browser on start (NoBrowser)",
                       variable=self.var_no_browser, **cb_style).pack(anchor="w")
        tk.Checkbutton(opts, text="Use Docker containers instead of local processes",
                       variable=self.var_docker_mode, **cb_style).pack(anchor="w", pady=(4, 0))

    # ── Log Panel ─────────────────────────────────────────────

    def _build_log_panel(self):
        outer = tk.Frame(self.root, bg=self.BG)
        outer.pack(fill="both", expand=True, padx=20, pady=(16, 0))

        tk.Label(outer, text="ACTIVITY LOG", bg=self.BG, fg=self.FG_DIM,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(0, 6))

        self.log_text = tk.Text(outer, bg=self.BG_CARD, fg=self.FG_DIM,
                                font=("Consolas", 8), height=6, wrap="word",
                                relief="flat", borderwidth=0, padx=8, pady=8,
                                state="disabled", highlightbackground=self.BORDER,
                                highlightthickness=1)
        self.log_text.pack(fill="both", expand=True)

        # Tag for colored log entries
        self.log_text.tag_configure("ok", foreground=self.GREEN)
        self.log_text.tag_configure("warn", foreground=self.AMBER)
        self.log_text.tag_configure("err", foreground=self.RED)
        self.log_text.tag_configure("info", foreground=self.FG_DIM)

        self._log("Autify Engine Launcher ready.", "info")
        self._log(f"Python: {PYTHON_EXE}", "info")
        self._log(f"npm:    {NPM_CMD}", "info")

    # ── Footer ────────────────────────────────────────────────

    def _build_footer(self):
        footer = tk.Frame(self.root, bg=self.BG)
        footer.pack(fill="x", padx=20, pady=(8, 12))

        tk.Label(footer, text="Autify Engine V1.0.0  --  Local Deployment  --  All data stays on this machine",
                 bg=self.BG, fg=self.FG_DIM, font=("Segoe UI", 7)).pack()

    # ── Logging ───────────────────────────────────────────────

    def _log(self, msg, tag="info"):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"[{ts}] {msg}\n", tag)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    # ── Status Polling ────────────────────────────────────────

    def _poll_status(self):
        if not self._running:
            return

        def check():
            statuses = {
                "backend":   is_port_listening(BACKEND_PORT),
                "dashboard": is_port_listening(DASHBOARD_PORT),
                "llm":       is_port_listening(LLM_PORT),
            }
            if self._running:
                self.root.after(0, lambda: self._update_indicators(statuses))

        threading.Thread(target=check, daemon=True).start()
        self.root.after(3000, self._poll_status)

    def _update_indicators(self, statuses):
        for key, running in statuses.items():
            ind = self.status_indicators[key]
            if running:
                ind["canvas"].itemconfig(ind["dot"], fill=self.GREEN)
                ind["label"].config(text="Running", fg=self.GREEN)
            else:
                ind["canvas"].itemconfig(ind["dot"], fill=self.RED)
                ind["label"].config(text="Stopped", fg=self.RED)

    # ── Start / Stop / Restart ────────────────────────────────

    def _start_all(self):
        self._log("Starting services...", "info")
        self._disable_buttons()
        threading.Thread(target=self._do_start, daemon=True).start()

    def _do_start(self):
        docker = self.var_docker_mode.get()
        no_browser = self.var_no_browser.get()

        if docker:
            self._start_docker()
        else:
            self._start_local()

        if not no_browser:
            self.root.after(500, self._open_dashboard)

        self.root.after(0, self._enable_buttons)

    def _start_docker(self):
        self._log("Starting Docker containers...", "info")
        try:
            result = subprocess.run(
                ["docker-compose", "up", "-d"],
                cwd=ROOT_DIR, capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0:
                self._log_safe("Docker containers started successfully.", "ok")
            else:
                self._log_safe(f"Docker error: {result.stderr[:200]}", "err")
        except FileNotFoundError:
            self._log_safe("docker-compose not found. Install Docker Desktop.", "err")
        except Exception as e:
            self._log_safe(f"Docker start failed: {e}", "err")

    def _start_local(self):
        # Start backend
        if not is_port_listening(BACKEND_PORT):
            self._log_safe("Starting FastAPI backend...", "info")
            os.makedirs(os.path.join(ROOT_DIR, "data"), exist_ok=True)
            env = os.environ.copy()
            env["BACKEND_PORT"] = str(BACKEND_PORT)
            env["DASHBOARD_PORT"] = str(DASHBOARD_PORT)
            try:
                proc = subprocess.Popen(
                    [PYTHON_EXE, "-m", "uvicorn", "api.main:app",
                     "--host", "127.0.0.1", "--port", str(BACKEND_PORT)],
                    cwd=ROOT_DIR, env=env,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                self._backend_pid = proc.pid
                # Wait for ready
                for i in range(15):
                    import time; time.sleep(1)
                    if is_port_listening(BACKEND_PORT):
                        self._log_safe(f"Backend ready ({i+1}s)", "ok")
                        break
                else:
                    self._log_safe("Backend may still be starting...", "warn")
            except Exception as e:
                self._log_safe(f"Backend start failed: {e}", "err")
        else:
            self._log_safe("Backend already running.", "info")

        # Start dashboard
        if not is_port_listening(DASHBOARD_PORT):
            self._log_safe("Starting React dashboard...", "info")
            # Ensure port is truly free (TIME_WAIT can linger)
            kill_port(DASHBOARD_PORT)
            import time; time.sleep(1)
            env = os.environ.copy()
            env["BACKEND_PORT"] = str(BACKEND_PORT)
            env["DASHBOARD_PORT"] = str(DASHBOARD_PORT)
            # Guarantee Node.js is on PATH so npm.cmd can find node
            if NODE_BASE not in env.get("PATH", "") and NODE_BASE not in env.get("Path", ""):
                env["PATH"] = NODE_BASE + ";" + env.get("PATH", env.get("Path", ""))
            try:
                proc = subprocess.Popen(
                    [NPM_CMD, "run", "dev"],
                    cwd=os.path.join(ROOT_DIR, "dashboard"), env=env,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
                self._dashboard_pid = proc.pid
                import time
                for i in range(20):
                    time.sleep(1)
                    if is_port_listening(DASHBOARD_PORT):
                        self._log_safe(f"Dashboard ready ({i+1}s)", "ok")
                        break
                else:
                    self._log_safe("Dashboard may still be starting...", "warn")
            except Exception as e:
                self._log_safe(f"Dashboard start failed: {e}", "err")
        else:
            self._log_safe("Dashboard already running.", "info")

        self._log_safe("All services started.", "ok")

    def _stop_all(self):
        self._log("Stopping services...", "warn")
        self._disable_buttons()
        threading.Thread(target=self._do_stop, daemon=True).start()

    def _do_stop(self):
        docker = self.var_docker_mode.get()

        if docker:
            self._stop_docker()
        else:
            self._stop_local()

        self.root.after(0, self._enable_buttons)

    def _stop_docker(self):
        self._log_safe("Stopping Docker containers...", "info")
        try:
            subprocess.run(
                ["docker-compose", "down"],
                cwd=ROOT_DIR, capture_output=True, text=True, timeout=60
            )
            self._log_safe("Docker containers stopped.", "ok")
        except Exception as e:
            self._log_safe(f"Docker stop failed: {e}", "err")

    def _stop_local(self):
        for port, name in [(BACKEND_PORT, "Backend"), (DASHBOARD_PORT, "Dashboard")]:
            if is_port_listening(port):
                self._log_safe(f"Stopping {name} on port {port}...", "warn")
                kill_port(port)
            else:
                self._log_safe(f"{name} not running.", "info")

        import time; time.sleep(1)
        self._log_safe("All services stopped.", "ok")

    def _restart_all(self):
        self._log("Restarting services...", "warn")
        self._disable_buttons()
        threading.Thread(target=self._do_restart, daemon=True).start()

    def _do_restart(self):
        self._do_stop()
        import time; time.sleep(1)
        self._do_start()

    # ── Dashboard Launch ──────────────────────────────────────

    def _open_dashboard(self):
        url = f"http://localhost:{DASHBOARD_PORT}"
        browser = find_browser()
        if browser:
            try:
                subprocess.Popen([browser, f"--app={url}",
                                  "--window-size=1400,900",
                                  "--disable-infobars", "--no-first-run"],
                                 creationflags=subprocess.CREATE_NO_WINDOW)
                name = "Edge" if "edge" in browser.lower() else "Chrome"
                self._log(f"Dashboard opened in {name} app mode.", "ok")
            except Exception:
                os.startfile(url)
        else:
            os.startfile(url)
            self._log("Dashboard opened in default browser.", "ok")

    # ── Helpers ───────────────────────────────────────────────

    def _log_safe(self, msg, tag="info"):
        """Thread-safe log to UI."""
        self.root.after(0, lambda: self._log(msg, tag))

    def _disable_buttons(self):
        for btn in [self.btn_start, self.btn_stop, self.btn_restart]:
            btn.config(state="disabled")

    def _enable_buttons(self):
        for btn in [self.btn_start, self.btn_stop, self.btn_restart]:
            btn.config(state="normal")

    def _on_close(self):
        self._running = False
        self.root.destroy()


# ── Entry Point ───────────────────────────────────────────────────────

def main():
    root = tk.Tk()
    app = AutifyLauncherApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
