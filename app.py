import sys
import os
import subprocess
import threading
import http.server
import socketserver
import time  # ★ 新增：用来生成不重复的 query

from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QWidget, QFrame, QVBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineProfile  # ★ 新增 QWebEngineProfile
from PyQt5.QtCore import QUrl, Qt

from camera_widget import CameraWidget


def start_server(web_dir):
    """启动本地 HTTP 服务器，根目录为 web_dir"""
    Handler = http.server.SimpleHTTPRequestHandler
    os.chdir(web_dir)  # 在 server 线程里修改当前目录
    httpd = socketserver.TCPServer(("127.0.0.1", 8000), Handler)
    print(f"Serving HTTP on 127.0.0.1:8000, root = {web_dir}")
    httpd.serve_forever()


class DebugWebPage(QWebEnginePage):
    """把 JS 的 console 输出重定向到 Python 终端"""

    def javaScriptConsoleMessage(self, level, msg, line, source_id):
        # level: 0=Info, 1=Warning, 2=Error
        level_name = {0: "INFO", 1: "WARN", 2: "ERROR"}.get(level, str(level))
        print(f"[JS {level_name}] {msg} ({source_id}:{line})")


class MyApp(QWidget):
    def __init__(self):
        super(MyApp, self).__init__()
        # 加载 Qt Designer 设计的 UI
        uic.loadUi('../src/signdemo.ui', self)
        self.setWindowTitle("Sign Translator")
        self.show()

        # 左边摄像头区域
        self.live_frame = self.findChild(QFrame, "live_cap_frame")
        self.camera_widget = CameraWidget(parent=self.live_frame)
        live_layout = QVBoxLayout(self.live_frame)
        live_layout.setContentsMargins(0, 0, 0, 0)
        live_layout.addWidget(self.camera_widget)

        # 右边 three.js 区域
        self.motion_frame = self.findChild(QFrame, "motion_frame")

        self.web_view = QWebEngineView(self.motion_frame)
        # 使用自定义的 DebugWebPage，这样 JS console 会打印到终端
        debug_page = DebugWebPage(self.web_view)
        self.web_view.setPage(debug_page)

        # ★★ 关键：关闭 WebEngine 缓存，避免一直用旧的 index.html ★★
        profile: QWebEngineProfile = self.web_view.page().profile()
        profile.setHttpCacheType(QWebEngineProfile.NoCache)
        profile.clearHttpCache()

        # 每次加载 index.html 时加一个不同的 query，强制绕过所有缓存
        url_str = f"http://127.0.0.1:8000/index.html?v={time.time()}"
        print("Loading index.html with url:", url_str)
        self.web_view.load(QUrl(url_str))

        motion_layout = QVBoxLayout(self.motion_frame)
        motion_layout.setContentsMargins(0, 0, 0, 0)
        motion_layout.addWidget(self.web_view)

    def keyPressEvent(self, event):
        """这里只保留按键事件占位，方便后续你要加别的快捷键"""
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)


if __name__ == "__main__":
    main_pid = os.getpid()
    print("PID:", main_pid)
    monitor_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "pc_test",
        "monitor_process.py"
    )
    subprocess.Popen([
        sys.executable,  # 当前 python
        monitor_path,  # 监控脚本
        str(main_pid)
    ])
    # 启动本地 HTTP 服务器，目录为当前文件所在目录下的 web/
    web_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
    threading.Thread(target=start_server, args=(web_dir,), daemon=True).start()

    app = QApplication(sys.argv)
    window = MyApp()
    sys.exit(app.exec_())
