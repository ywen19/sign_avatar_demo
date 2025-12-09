import sys
import os

import cv2
from PyQt5 import uic
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QFrame
)
from PyQt5.QtCore import QUrl, QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWebEngineWidgets import QWebEngineView   # 以后右侧用


class CameraWidget(QWidget):
    def __init__(self, camera_index=0, parent=None):
        super().__init__(parent)

        self.label = QLabel("Camera")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("background:#000; color:#fff;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.label)

        # 打开摄像头
        self.cap = cv2.VideoCapture(camera_index)

        # 定时器，约 30fps 刷新
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(33)

    def update_frame(self):
        if not self.cap.isOpened():
            return
        ret, frame = self.cap.read()
        if not ret:
            return

        # 镜像一下，更像“照镜子”
        frame = cv2.flip(frame, 1)

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame_rgb.shape
        bytes_per_line = ch * w

        qimg = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pix = QPixmap.fromImage(qimg)
        self.label.setPixmap(
            pix.scaled(
                self.label.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
            )
        )

    def closeEvent(self, event):
        if self.cap.isOpened():
            self.cap.release()
        super().closeEvent(event)

