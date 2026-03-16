from PyQt6.QtCore import QObject, pyqtSignal, pyqtProperty, QTimer

from anim_data import AnimationData


class AnimationController(QObject):
    currentQuatChanged = pyqtSignal()
    currentFrameChanged = pyqtSignal()
    playingChanged = pyqtSignal()

    def __init__(self, json_path: str, bone_name: str = "Hips", parent=None):
        super().__init__(parent)

        self.anim_data = AnimationData(json_path)
        self.bone_name = bone_name

        self._current_frame = 0
        self._playing = False

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._advance_frame)

        interval_ms = max(1, int(1000 / self.anim_data.fps))
        self._timer.setInterval(interval_ms)

    def _advance_frame(self):
        self._current_frame = (self._current_frame + 1) % self.anim_data.get_bone_frame_count(self.bone_name)
        self.currentFrameChanged.emit()
        self.currentQuatChanged.emit()

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

    @pyqtProperty(int, notify=currentFrameChanged)
    def currentFrame(self):
        return self._current_frame

    @pyqtProperty("QVariantList", notify=currentQuatChanged)
    def currentQuat(self):
        return self.anim_data.get_quat(self.bone_name, self._current_frame)

    @pyqtProperty(bool, notify=playingChanged)
    def playing(self):
        return self._playing

    @pyqtProperty(int, constant=True)
    def fps(self):
        return self.anim_data.fps