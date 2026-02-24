import sys
import os
import subprocess
import threading
import time
import json
import csv
import http.server
import socketserver

from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QWidget, QFrame, QVBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineProfile
from PyQt5.QtCore import QUrl, Qt

from camera_widget import CameraWidget

# =========================================================
# TEST SWITCHES (你测试时只改这里)
# =========================================================
ENABLE_RENDER = True     # Render-only / Capture+Render 时设 True
ENABLE_CAPTURE = True    # Render-only 时设 False


# =========================================================
# HTTP Server with FPS logging
# =========================================================
class ReuseTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


class FPSLoggingHandler(http.server.SimpleHTTPRequestHandler):
    """
    GET  : 静态文件服务（index.html / js / glb / json 等）
    POST : /log_fps  -> append 写 fps_log.csv
    """
    fps_csv_path = None  # 在 start_server 里设置

    def do_POST(self):
        if self.path != "/log_fps":
            self.send_response(404)
            self.end_headers()
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length)
            payload = json.loads(raw.decode("utf-8"))

            fps = payload.get("fps", "")
            browser_t_ms = payload.get("t_ms", "")

            # epoch time 用于和 resource_log.csv 对齐
            epoch_sec = time.time()

            with open(self.fps_csv_path, "a", newline="") as f:
                w = csv.writer(f)
                w.writerow([epoch_sec, browser_t_ms, fps])

            self.send_response(204)
            self.end_headers()
        except Exception:
            self.send_response(400)
            self.end_headers()


def start_server(web_dir: str, port: int = 8000):
    """
    启动本地 HTTP 服务器，根目录为 web_dir
    同时支持 POST /log_fps 写 fps_log.csv
    """
    # 把 server 的工作目录切到 web/，这样静态文件路径就是相对路径
    os.chdir(web_dir)

    # fps_log.csv 放在 web_dir（你也可以改成项目根目录）
    fps_csv_path = os.path.join(web_dir, "fps_log.csv")
    if not os.path.exists(fps_csv_path):
        with open(fps_csv_path, "w", newline="") as f:
            csv.writer(f).writerow(["epoch_sec", "browser_time_ms", "fps"])

    FPSLoggingHandler.fps_csv_path = fps_csv_path

    httpd = ReuseTCPServer(("127.0.0.1", port), FPSLoggingHandler)
    print(f"Serving HTTP on 127.0.0.1:{port}, root = {web_dir}")
    httpd.serve_forever()


# =========================================================
# WebEngine debug page
# =========================================================
class DebugWebPage(QWebEnginePage):
    """把 JS 的 console 输出重定向到 Python 终端"""

    def javaScriptConsoleMessage(self, level, msg, line, source_id):
        level_name = {0: "INFO", 1: "WARN", 2: "ERROR"}.get(level, str(level))
        print(f"[JS {level_name}] {msg} ({source_id}:{line})")


# =========================================================
# Main Qt App
# =========================================================
class MyApp(QWidget):
    def __init__(self):
        super(MyApp, self).__init__()

        self.enable_render = ENABLE_RENDER
        self.enable_capture = ENABLE_CAPTURE

        # 加载 Qt Designer UI
        uic.loadUi('../src/signdemo.ui', self)
        self.setWindowTitle("Sign Translator")
        self.show()

        # -------------------------
        # 左边摄像头区域 (Capture)
        # -------------------------
        self.live_frame = self.findChild(QFrame, "live_cap_frame")
        live_layout = QVBoxLayout(self.live_frame)
        live_layout.setContentsMargins(0, 0, 0, 0)

        if self.enable_capture:
            self.camera_widget = CameraWidget(parent=self.live_frame)
            live_layout.addWidget(self.camera_widget)
        else:
            self.camera_widget = None
            print("[TEST] Capture DISABLED")

        # -------------------------
        # 右边 three.js 区域 (Render)
        # -------------------------
        self.motion_frame = self.findChild(QFrame, "motion_frame")
        motion_layout = QVBoxLayout(self.motion_frame)
        motion_layout.setContentsMargins(0, 0, 0, 0)

        if self.enable_render:
            self.web_view = QWebEngineView(self.motion_frame)

            # JS console -> Python stdout
            debug_page = DebugWebPage(self.web_view)
            self.web_view.setPage(debug_page)

            # 关闭缓存 + 清缓存，避免旧页面
            profile: QWebEngineProfile = self.web_view.page().profile()
            profile.setHttpCacheType(QWebEngineProfile.NoCache)
            profile.clearHttpCache()

            # 加 query 强制刷新
            url_str = f"http://127.0.0.1:8000/index.html?v={time.time()}"
            print("Loading index.html with url:", url_str)
            self.web_view.load(QUrl(url_str))

            motion_layout.addWidget(self.web_view)
        else:
            self.web_view = None
            print("[TEST] Render DISABLED")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)


# =========================================================
# Entry
# =========================================================
if __name__ == "__main__":
    main_pid = os.getpid()
    print("PID:", main_pid)

    # 启动监控进程（传主进程 PID；monitor 会递归统计子进程树）
    monitor_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "pc_test",
        "monitor_process.py"
    )
    subprocess.Popen([sys.executable, monitor_path, str(main_pid)])

    # 仅在渲染开启时启动 HTTP server（避免污染 capture-only baseline）
    if ENABLE_RENDER:
        web_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
        threading.Thread(target=start_server, args=(web_dir,), daemon=True).start()

    app = QApplication(sys.argv)
    window = MyApp()
    sys.exit(app.exec_())