import sys
import os

from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QWidget, QFrame, QVBoxLayout
from PyQt6.QtQuickWidgets import QQuickWidget
from PyQt6.QtCore import Qt, QCoreApplication, QUrl
from PyQt6.QtQml import QQmlContext

# from camera_widget import CameraWidget
from anim_controller import AnimationController


class MyApp(QWidget):
    def __init__(self):
        super().__init__()

        # 加载 Qt Designer 设计的 UI
        ui_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "src",
            "signdemo.ui"
        )
        uic.loadUi(ui_path, self)
        self.setWindowTitle("Sign Translator")

        # 左边摄像头区域
        self.live_frame = self.findChild(QFrame, "live_cap_frame")
        # self.camera_widget = CameraWidget(parent=self.live_frame)
        live_layout = QVBoxLayout(self.live_frame)
        live_layout.setContentsMargins(0, 0, 0, 0)
        # live_layout.addWidget(self.camera_widget)

        # add quickwidget to gui for 3d content display
        self.display_frame = self.findChild(QFrame, "display_frame")

        if self.display_frame.layout() is None:
            self.display_layout = QVBoxLayout(self.display_frame)
            self.display_layout.setContentsMargins(0, 0, 0, 0)
        else:
            self.display_layout = self.display_frame.layout()

        self.quick_widget = QQuickWidget(self.display_frame)
        self.quick_widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)

        json_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "web",
            "Dancing_mixamo_com_frames_nomix.json"
        )

        mapping_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "web",
            "model_joint_mapping.json"
        )

        self.anim_controller = AnimationController(
            json_path=json_path,
            mapping_path=mapping_path,
            bone_name="Hips"
        )
        
        self.quick_widget.rootContext().setContextProperty(
            "animController",
            self.anim_controller
        )

        qml_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "qml",
            "Main.qml"
        )
        self.quick_widget.setSource(QUrl.fromLocalFile(qml_path))

        self.anim_controller.start()
        self.display_layout.addWidget(self.quick_widget)


        self.show()

    def keyPressEvent(self, event):
        """这里只保留按键事件占位，方便后续你要加别的快捷键"""
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)


if __name__ == "__main__":
    QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_UseDesktopOpenGL)
    QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)

    app = QApplication(sys.argv)
    window = MyApp()
    sys.exit(app.exec())