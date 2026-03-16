from PyQt6.QtCore import QCoreApplication, QTimer
import sys

from anim_controller import AnimationController


def print_frame():
    print("frame:", controller.currentFrame, "quat:", controller.currentQuat)


app = QCoreApplication(sys.argv)

controller = AnimationController(
    json_path="web/Dancing_mixamo_com_frames_nomix.json",
    bone_name="Hips"
)

controller.currentFrameChanged.connect(print_frame)

controller.start()

QTimer.singleShot(500, app.quit)  # 跑半秒看看
sys.exit(app.exec())