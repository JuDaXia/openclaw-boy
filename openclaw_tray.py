"""
OpenClaw Gateway Tray Tool
- System tray icon with green/red status
- Popup panel: Start / Stop / Restart / Open Web UI
- Auto-start on Windows boot (optional)
- Windows notifications
- Requires: pystray, Pillow, winotify
- Build: pyinstaller --onefile --windowed --uac-admin openclaw_tray.py
"""

import subprocess
import socket
import threading
import webbrowser
import time
import sys
import os
import tkinter as tk
from tkinter import font as tkfont, scrolledtext, messagebox
import pystray
from PIL import Image, ImageDraw
import winreg

# ── Debug log ─────────────────────────────────────────────────
_log_lines = []
_log_lock  = threading.Lock()

def log(msg):
    """Append a timestamped line to the in-memory log."""
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    with _log_lock:
        _log_lines.append(line)
        if len(_log_lines) > 200:
            _log_lines.pop(0)
    print(line, flush=True)

# ── Windows Notifications (Import after log function) ────────
try:
    from winotify import Notification, audio
    HAS_WINOTIFY = True
    log("winotify loaded - notifications enabled")
except ImportError:
    HAS_WINOTIFY = False
    log("winotify not installed - notifications disabled")

# ── Config ────────────────────────────────────────────────────
GATEWAY_HOST = "127.0.0.1"
GATEWAY_PORT = 18789
WEB_UI_URL   = f"http://{GATEWAY_HOST}:{GATEWAY_PORT}/"
POLL_INTERVAL = 8   # seconds between status checks

# openclaw executable - search PATH automatically
def find_openclaw():
    # On Windows, npm packages create .cmd wrappers — check those first
    for candidate in ["openclaw.cmd", "openclaw.ps1", "openclaw"]:
        try:
            result = subprocess.run(
                ["where", candidate],
                capture_output=True, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if result.returncode == 0:
                path = result.stdout.strip().splitlines()[0]
                return path
        except Exception:
            pass
    return "openclaw.cmd"  # fallback

OPENCLAW_CMD = find_openclaw()
log(f"openclaw executable: {OPENCLAW_CMD}")

# ── Auto-start management ─────────────────────────────────────
REGISTRY_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "OpenClawGateway"

def is_autostart_enabled():
    """Check if auto-start is enabled in registry."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRY_KEY, 0, winreg.KEY_READ)
        try:
            value, _ = winreg.QueryValueEx(key, APP_NAME)
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            winreg.CloseKey(key)
            return False
    except Exception as e:
        log(f"Error checking auto-start: {e}")
        return False

def enable_autostart():
    """Add this program to Windows startup."""
    try:
        exe_path = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__)
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRY_KEY, 0, winreg.KEY_WRITE)
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, f'"{exe_path}"')
        winreg.CloseKey(key)
        log("Auto-start enabled")
        return True
    except Exception as e:
        log(f"Failed to enable auto-start: {e}")
        return False

def disable_autostart():
    """Remove this program from Windows startup."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRY_KEY, 0, winreg.KEY_WRITE)
        try:
            winreg.DeleteValue(key, APP_NAME)
            log("Auto-start disabled")
            result = True
        except FileNotFoundError:
            result = False
        winreg.CloseKey(key)
        return result
    except Exception as e:
        log(f"Failed to disable auto-start: {e}")
        return False

# ── Windows Notifications ─────────────────────────────────────
def show_notification(title, message, icon_path=None):
    """Show Windows toast notification."""
    if not HAS_WINOTIFY:
        log(f"Notification (disabled): {title} - {message}")
        return
    try:
        toast = Notification(
            app_id="OpenClaw Gateway",
            title=title,
            msg=message,
            duration="short"
        )
        if icon_path and os.path.exists(icon_path):
            toast.set_audio(audio.Default, loop=False)
        toast.show()
        log(f"Notification shown: {title}")
    except Exception as e:
        log(f"Failed to show notification: {e}")

# ── Gateway control ───────────────────────────────────────────
def run_cmd(args, timeout=30):
    """Run a command, return (returncode, stdout, stderr)."""
    try:
        if OPENCLAW_CMD.endswith(".ps1"):
            full_args = ["powershell", "-ExecutionPolicy", "Bypass",
                         "-File", OPENCLAW_CMD] + args
        elif OPENCLAW_CMD.endswith(".cmd") or OPENCLAW_CMD.endswith(".bat"):
            full_args = ["cmd", "/c", OPENCLAW_CMD] + args
        else:
            full_args = [OPENCLAW_CMD] + args

        log(f"Running: {' '.join(full_args)}")
        result = subprocess.run(
            full_args,
            capture_output=True,
            encoding='utf-8', errors='replace',
            timeout=timeout,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        log(f"rc={result.returncode}")
        if result.stdout.strip():
            log(f"stdout: {result.stdout.strip()[:400]}")
        if result.stderr.strip():
            log(f"stderr: {result.stderr.strip()[:400]}")
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        log("Command timed out")
        return -1, "", "timeout"
    except Exception as e:
        log(f"Exception: {e}")
        return -1, "", str(e)

def is_gateway_running():
    """Check if port 18789 is actually listening."""
    try:
        with socket.create_connection((GATEWAY_HOST, GATEWAY_PORT), timeout=2):
            return True
    except Exception:
        return False

def _service_missing(stdout):
    """Return True if openclaw says the service is not installed."""
    return "gateway service missing" in stdout.lower()

def _access_denied(stderr):
    """Return True if schtasks failed due to permission denied."""
    s = stderr.lower()
    # Node.js replaces CJK chars with U+FFFD; check both patterns
    return ("schtasks create failed" in s and
            ("access" in s or "\ufffd" in s or "denied" in s))

# ── Direct-process fallback ────────────────────────────────────
# When schtasks install fails (no admin), we run openclaw gateway
# as a child process and manage it ourselves.
_direct_proc = None   # subprocess.Popen handle

def _build_openclaw_args(args):
    if OPENCLAW_CMD.endswith(".ps1"):
        return ["powershell", "-ExecutionPolicy", "Bypass", "-File", OPENCLAW_CMD] + args
    elif OPENCLAW_CMD.endswith(".cmd") or OPENCLAW_CMD.endswith(".bat"):
        return ["cmd", "/c", OPENCLAW_CMD] + args
    return [OPENCLAW_CMD] + args

def kill_port():
    """Kill any process occupying GATEWAY_PORT."""
    try:
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True, encoding='utf-8', errors='replace',
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        for line in result.stdout.splitlines():
            if f":{GATEWAY_PORT}" in line and "LISTENING" in line:
                pid = line.split()[-1]
                log(f"Port {GATEWAY_PORT} occupied by PID {pid}, killing...")
                subprocess.run(
                    ["taskkill", "/F", "/PID", pid],
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                time.sleep(1)
                return True
    except Exception as e:
        log(f"kill_port error: {e}")
    return False

def _start_direct():
    """Start gateway as a direct child process (no admin needed)."""
    global _direct_proc
    _stop_direct()
    try:
        args = _build_openclaw_args(["gateway"])
        log(f"Starting direct process: {' '.join(args)}")
        _direct_proc = subprocess.Popen(
            args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        log(f"Direct process PID: {_direct_proc.pid}")
        # Wait up to 8s for port to open
        for _ in range(8):
            time.sleep(1)
            if is_gateway_running():
                log("Direct process: gateway is up")
                return 0, "", ""
        log("Direct process: gateway did not start in time")
        return -1, "", "Gateway did not start within 8 seconds"
    except Exception as e:
        log(f"Direct start error: {e}")
        return -1, "", str(e)

def _stop_direct():
    """Stop the direct child process."""
    global _direct_proc
    if _direct_proc and _direct_proc.poll() is None:
        log(f"Terminating direct process PID {_direct_proc.pid}")
        _direct_proc.terminate()
        try:
            _direct_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _direct_proc.kill()
        _direct_proc = None

def gateway_start():
    global _direct_proc
    # First try the official start command
    rc, out, err = run_cmd(["gateway", "start"])

    # Service not installed — try to install
    if rc == 0 and _service_missing(out):
        log("Service missing, trying install...")
        rc2, out2, err2 = run_cmd(["gateway", "install"], timeout=60)

        if rc2 == 0:
            # Install succeeded, retry start
            log("Install succeeded, retrying start...")
            rc, out, err = run_cmd(["gateway", "start"])
        elif _access_denied(err2):
            # No admin rights — fall back to direct process
            log("Install requires admin, falling back to direct process mode...")
            rc, out, err = _start_direct()
            if rc == 0:
                show_notification("OpenClaw Gateway", "Gateway 已启动")
                return 0, out, err
            else:
                show_notification("OpenClaw Gateway", "Gateway 启动失败")
                return -1, out, err
        else:
            log(f"Install failed: {err2}")
            show_notification("OpenClaw Gateway", "安装失败，请查看调试日志")
            return rc2, out2, err2

    if rc == 0 and not _service_missing(out):
        show_notification("OpenClaw Gateway", "Gateway 已启动")
    else:
        show_notification("OpenClaw Gateway", "Gateway 启动失败")
        rc = -1
    return rc, out, err

def gateway_stop():
    _stop_direct()
    rc, out, err = run_cmd(["gateway", "stop"])
    # Also kill port in case of zombie
    if is_gateway_running():
        kill_port()
    show_notification("OpenClaw Gateway", "Gateway 已停止")
    return 0, out, err

def gateway_restart():
    """Stop everything, clean up port, then start fresh."""
    log("Restart: stopping...")
    _stop_direct()
    run_cmd(["gateway", "stop"], timeout=15)
    time.sleep(1)
    if is_gateway_running():
        log("Port still occupied, force-killing...")
        kill_port()
        time.sleep(1)
    log("Restart: starting...")
    return gateway_start()

# ── Tray icon images ──────────────────────────────────────────
def make_icon(color):
    """Create a 64x64 circle icon in the given color."""
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, 60, 60], fill=color)
    return img

ICON_GREEN  = make_icon("#2ecc71")
ICON_RED    = make_icon("#e74c3c")
ICON_YELLOW = make_icon("#f39c12")

# ── Main App ──────────────────────────────────────────────────
class OpenClawTray:
    def __init__(self):
        self.running = True
        self.status  = False   # True = gateway up
        self.busy    = False   # True = operation in progress
        self.panel   = None    # tkinter window reference

        # Build tray icon
        self.tray = pystray.Icon(
            name="OpenClaw Gateway",
            icon=ICON_RED,
            title="OpenClaw Gateway",
            menu=pystray.Menu(
                pystray.MenuItem("打开控制面板", self.show_panel, default=True),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("启动 Gateway",   self.action_start),
                pystray.MenuItem("停止 Gateway",   self.action_stop),
                pystray.MenuItem("重启 Gateway",   self.action_restart),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("打开网页控制台", self.action_open_web),
                pystray.MenuItem("查看调试日志",   self.action_show_log),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(
                    "开机自动启动",
                    self.action_toggle_autostart,
                    checked=lambda item: is_autostart_enabled()
                ),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("退出",           self.action_exit),
            )
        )

        # Start background poller
        self.poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.poll_thread.start()

    # ── Status polling ────────────────────────────────────────
    def _poll_loop(self):
        while self.running:
            self._refresh_status()
            time.sleep(POLL_INTERVAL)

    def _refresh_status(self):
        if self.busy:
            return
        up = is_gateway_running()
        if up != self.status:
            self.status = up
            self._update_tray_icon()
            self._update_panel_status()

    def _update_tray_icon(self):
        if self.busy:
            self.tray.icon  = ICON_YELLOW
            self.tray.title = "OpenClaw Gateway - 处理中..."
        elif self.status:
            self.tray.icon  = ICON_GREEN
            self.tray.title = "OpenClaw Gateway - 运行中"
        else:
            self.tray.icon  = ICON_RED
            self.tray.title = "OpenClaw Gateway - 已停止"

    # ── Panel window ──────────────────────────────────────────
    def show_panel(self, icon=None, item=None):
        """Open or bring the panel to front."""
        if self.panel and self.panel.winfo_exists():
            self.panel.lift()
            self.panel.focus_force()
            return
        self._build_panel()

    def _build_panel(self):
        win = tk.Tk()
        self.panel = win
        win.title("OpenClaw Gateway 控制面板")
        win.resizable(False, False)
        win.attributes("-topmost", True)

        # ── Styling ──
        BG       = "#1a1a2e"
        SURFACE  = "#16213e"
        ACCENT   = "#e94560"
        GREEN    = "#2ecc71"
        RED      = "#e74c3c"
        YELLOW   = "#f39c12"
        FG       = "#eaeaea"
        MUTED    = "#8892b0"

        win.configure(bg=BG)
        win.geometry("320x280")

        title_font  = tkfont.Font(family="Segoe UI", size=13, weight="bold")
        label_font  = tkfont.Font(family="Segoe UI", size=10)
        status_font = tkfont.Font(family="Segoe UI", size=11, weight="bold")
        btn_font    = tkfont.Font(family="Segoe UI", size=9, weight="bold")

        # ── Header ──
        header = tk.Frame(win, bg=SURFACE, pady=12)
        header.pack(fill="x")

        tk.Label(header, text="🦞  OpenClaw Gateway",
                 font=title_font, bg=SURFACE, fg=FG).pack()

        tk.Label(header, text=f"ws://{GATEWAY_HOST}:{GATEWAY_PORT}",
                 font=label_font, bg=SURFACE, fg=MUTED).pack()

        # ── Status indicator ──
        status_frame = tk.Frame(win, bg=BG, pady=16)
        status_frame.pack(fill="x", padx=20)

        tk.Label(status_frame, text="当前状态",
                 font=tkfont.Font(family="Segoe UI", size=8),
                 bg=BG, fg=MUTED).pack(anchor="w")

        self._status_label = tk.Label(
            status_frame, text="检测中...",
            font=status_font, bg=BG, fg=YELLOW
        )
        self._status_label.pack(anchor="w")

        # ── Buttons ──
        btn_frame = tk.Frame(win, bg=BG)
        btn_frame.pack(fill="x", padx=20)

        def make_btn(parent, text, cmd, color=SURFACE, fg=FG):
            b = tk.Button(
                parent, text=text, command=cmd,
                font=btn_font,
                bg=color, fg=fg,
                activebackground=ACCENT, activeforeground="white",
                relief="flat", bd=0,
                padx=10, pady=7,
                cursor="hand2"
            )
            return b

        row1 = tk.Frame(btn_frame, bg=BG)
        row1.pack(fill="x", pady=(0, 6))

        self._btn_start   = make_btn(row1, "▶  启动",   self.action_start,   "#27ae60", "white")
        self._btn_stop    = make_btn(row1, "■  停止",   self.action_stop,    "#c0392b", "white")
        self._btn_restart = make_btn(row1, "↺  重启",   self.action_restart, "#2980b9", "white")

        self._btn_start.pack(  side="left", expand=True, fill="x", padx=(0,4))
        self._btn_stop.pack(   side="left", expand=True, fill="x", padx=(0,4))
        self._btn_restart.pack(side="left", expand=True, fill="x")

        row2 = tk.Frame(btn_frame, bg=BG)
        row2.pack(fill="x", pady=(0, 6))

        make_btn(row2, "🌐  打开网页控制台", self.action_open_web,
                 ACCENT, "white").pack(fill="x")

        row3 = tk.Frame(btn_frame, bg=BG)
        row3.pack(fill="x", pady=(0, 6))
        make_btn(row3, "📋  查看调试日志", self.action_show_log,
                 "#2c3e50", MUTED).pack(fill="x")

        # Auto-start checkbox
        autostart_frame = tk.Frame(btn_frame, bg=BG)
        autostart_frame.pack(fill="x", pady=(8, 0))

        self._autostart_var = tk.BooleanVar(value=is_autostart_enabled())
        autostart_check = tk.Checkbutton(
            autostart_frame,
            text="  开机自动启动",
            variable=self._autostart_var,
            command=self._toggle_autostart_from_panel,
            font=label_font,
            bg=BG, fg=FG,
            selectcolor=SURFACE,
            activebackground=BG,
            activeforeground=ACCENT,
            cursor="hand2",
            relief="flat"
        )
        autostart_check.pack(anchor="w")

        # ── Footer ──
        footer = tk.Frame(win, bg=BG)
        footer.pack(fill="x", padx=20, pady=(8, 12))

        self._msg_label = tk.Label(
            footer, text="", font=label_font, bg=BG, fg=MUTED, wraplength=280
        )
        self._msg_label.pack(anchor="w")

        # Initial status update
        self._update_panel_status()

        win.protocol("WM_DELETE_WINDOW", win.destroy)
        win.mainloop()

    def _update_panel_status(self):
        if not self.panel:
            return
        try:
            if not self.panel.winfo_exists():
                return
        except Exception:
            return

        if self.busy:
            color, text = "#f39c12", "处理中..."
        elif self.status:
            color, text = "#2ecc71", "● 运行中"
        else:
            color, text = "#e74c3c", "● 已停止"

        def _update():
            try:
                self._status_label.config(text=text, fg=color)
            except Exception:
                pass
        self.panel.after(0, _update)

    def _set_msg(self, msg):
        if not self.panel:
            return
        try:
            if self.panel.winfo_exists():
                self.panel.after(0, lambda: self._msg_label.config(text=msg))
        except Exception:
            pass

    # ── Actions ──────────────────────────────────────────────
    def _run_action(self, label, fn):
        """Run a gateway action in a background thread."""
        if self.busy:
            self._set_msg("有操作正在进行中，请稍候...")
            return
        self.busy = True
        self._update_tray_icon()
        self._update_panel_status()
        self._set_msg(f"{label}...")
        self._disable_buttons()

        def _work():
            try:
                rc, out, err = fn()
                time.sleep(2)
                self.busy = False
                self._refresh_status()
                self._update_tray_icon()
                self._update_panel_status()

                if rc == 0:
                    msg = f"✓ {label}成功"
                else:
                    error_detail = err.strip()[:100] if err.strip() else f"错误码 {rc}"
                    msg = f"✗ {label}失败：{error_detail}"
                    log(f"ERROR: {label} failed with code {rc}")
                    log(f"STDERR: {err}")

                log(msg)
                self._set_msg(msg)
                self._enable_buttons()
            except Exception as e:
                log(f"Exception in action: {e}")
                self.busy = False
                self._set_msg(f"✗ {label}异常：{str(e)}")
                self._enable_buttons()
                self._refresh_status()

        threading.Thread(target=_work, daemon=True).start()

    def _disable_buttons(self):
        """Disable action buttons during operations."""
        if not self.panel:
            return
        try:
            if hasattr(self, '_btn_start'):
                self.panel.after(0, lambda: self._btn_start.config(state="disabled"))
                self.panel.after(0, lambda: self._btn_stop.config(state="disabled"))
                self.panel.after(0, lambda: self._btn_restart.config(state="disabled"))
        except Exception:
            pass

    def _enable_buttons(self):
        """Enable action buttons after operations."""
        if not self.panel:
            return
        try:
            if hasattr(self, '_btn_start'):
                self.panel.after(0, lambda: self._btn_start.config(state="normal"))
                self.panel.after(0, lambda: self._btn_stop.config(state="normal"))
                self.panel.after(0, lambda: self._btn_restart.config(state="normal"))
        except Exception:
            pass

    def action_start(self,   icon=None, item=None): self._run_action("启动", gateway_start)
    def action_stop(self,    icon=None, item=None): self._run_action("停止", gateway_stop)
    def action_restart(self, icon=None, item=None): self._run_action("重启", gateway_restart)

    def action_open_web(self, icon=None, item=None):
        webbrowser.open(WEB_UI_URL)

    def action_show_log(self, icon=None, item=None):
        """Open a window showing the debug log."""
        win = tk.Toplevel(self.panel) if (self.panel and self.panel.winfo_exists()) else tk.Tk()
        win.title("OpenClaw 调试日志")
        win.geometry("620x400")
        win.configure(bg="#0d0d0d")

        txt = scrolledtext.ScrolledText(
            win, bg="#0d0d0d", fg="#00ff88",
            font=("Consolas", 9), wrap="word",
            relief="flat", bd=0
        )
        txt.pack(fill="both", expand=True, padx=8, pady=8)

        def refresh():
            txt.configure(state="normal")
            txt.delete("1.0", "end")
            with _log_lock:
                txt.insert("end", "\n".join(_log_lines))
            txt.configure(state="disabled")
            txt.see("end")

        refresh()

        bf = tk.Frame(win, bg="#0d0d0d")
        bf.pack(fill="x", padx=8, pady=(0, 8))
        tk.Button(bf, text="刷新", command=refresh,
                  bg="#1a1a2e", fg="#eaeaea", relief="flat",
                  padx=12, pady=4).pack(side="left")
        tk.Button(bf, text="关闭", command=win.destroy,
                  bg="#1a1a2e", fg="#eaeaea", relief="flat",
                  padx=12, pady=4).pack(side="right")

    def action_toggle_autostart(self, icon=None, item=None):
        """Toggle auto-start from tray menu."""
        if is_autostart_enabled():
            if disable_autostart():
                show_notification("OpenClaw Gateway", "已关闭开机自动启动")
            else:
                show_notification("OpenClaw Gateway", "关闭开机自动启动失败")
        else:
            if enable_autostart():
                show_notification("OpenClaw Gateway", "已开启开机自动启动")
            else:
                show_notification("OpenClaw Gateway", "开启开机自动启动失败")

    def _toggle_autostart_from_panel(self):
        """Toggle auto-start from panel checkbox."""
        enabled = self._autostart_var.get()
        if enabled:
            if not enable_autostart():
                self._autostart_var.set(False)
                self._set_msg("✗ 开启开机自动启动失败")
            else:
                self._set_msg("✓ 已开启开机自动启动")
        else:
            if not disable_autostart():
                self._autostart_var.set(True)
                self._set_msg("✗ 关闭开机自动启动失败")
            else:
                self._set_msg("✓ 已关闭开机自动启动")

    def action_exit(self, icon=None, item=None):
        self.running = False
        if self.panel:
            try:
                self.panel.destroy()
            except Exception:
                pass
        self.tray.stop()

    def run(self):
        self.tray.run()


# ── Entry point ───────────────────────────────────────────────
if __name__ == "__main__":
    app = OpenClawTray()
    app.run()
