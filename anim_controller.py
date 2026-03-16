from PyQt6.QtCore import QObject, pyqtSignal, pyqtProperty, QTimer
import json

from anim_data import AnimationData


class AnimationController(QObject):
    currentQuatChanged = pyqtSignal()
    currentFrameChanged = pyqtSignal()
    currentJointQuatsChanged = pyqtSignal()
    playingChanged = pyqtSignal()

    def __init__(
        self,
        json_path: str,
        mapping_path: str,
        bone_name: str = "Hips",
        parent=None
    ):
        super().__init__(parent)

        self.anim_data = AnimationData(json_path)
        self.bone_name = bone_name

        with open(mapping_path, "r", encoding="utf-8") as f:
            self.mapping = json.load(f)

        self.name_to_joint_index = self.mapping.get("name_to_joint_index", {})
        self.joint_count = int(self.mapping.get("joint_count", 0))

        self._current_frame = 0
        self._playing = False

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._advance_frame)

        interval_ms = max(1, int(1000 / self.anim_data.fps))
        self._timer.setInterval(interval_ms)

    def _advance_frame(self):
        total = self.anim_data.get_total_frames()
        if total <= 0:
            return

        self._current_frame = (self._current_frame + 1) % total
        self.currentFrameChanged.emit()
        self.currentQuatChanged.emit()
        self.currentJointQuatsChanged.emit()

    def start(self):
        if not self._playing:
            self._playing = True
            self._timer.start()
            self.playingChanged.emit()

    def stop(self):
        if self._playing:
            self._playing = False
            self._timer.stop()
            self.playingChanged.emit()

    def reset(self):
        self._current_frame = 0
        self.currentFrameChanged.emit()
        self.currentQuatChanged.emit()
        self.currentJointQuatsChanged.emit()

    @pyqtProperty(int, notify=currentFrameChanged)
    def currentFrame(self):
        return self._current_frame

    @pyqtProperty("QVariantList", notify=currentQuatChanged)
    def currentQuat(self):
        return self.anim_data.get_quat(self.bone_name, self._current_frame)

    @pyqtProperty("QVariantList", notify=currentJointQuatsChanged)
    def currentJointQuats(self):
        """
        返回长度 = joint_count 的列表
        每个元素要么是 [x, y, z, w]，要么是 []
        index 直接对应 avatar.jointsArray[index]
        """
        result = [[] for _ in range(self.joint_count)]

        for bone_name in self.anim_data.get_bone_names():
            joint_index = self.name_to_joint_index.get(bone_name)
            if joint_index is None:
                continue

            try:
                quat = self.anim_data.get_quat(bone_name, self._current_frame)
                result[joint_index] = quat
            except Exception:
                pass

        return result

    @pyqtProperty(bool, notify=playingChanged)
    def playing(self):
        return self._playing

    @pyqtProperty(int, constant=True)
    def fps(self):
        return self.anim_data.fps