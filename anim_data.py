import json
from pathlib import Path
from typing import Dict, List, Any


class AnimationData:
    def __init__(self, json_path: str):
        self.json_path = Path(json_path)

        self.name: str = ""
        self.fps: int = 30
        self.bones: Dict[str, List[Dict[str, Any]]] = {}

        self._load()

    def _load(self) -> None:
        with self.json_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        self.name = data.get("name", "")
        self.fps = int(data.get("fps", 30))
        self.bones = data.get("bones", {})

        if not isinstance(self.bones, dict):
            raise ValueError("Invalid JSON format: 'bones' must be a dictionary.")

        if not self.bones:
            raise ValueError("No bones found in animation JSON.")

    def has_bone(self, bone_name: str) -> bool:
        return bone_name in self.bones

    def get_bone_names(self) -> List[str]:
        return list(self.bones.keys())

    def get_bone_frames(self, bone_name: str) -> List[Dict[str, Any]]:
        if bone_name not in self.bones:
            raise KeyError(f"Bone '{bone_name}' not found.")
        return self.bones[bone_name]

    def get_bone_frame_count(self, bone_name: str) -> int:
        return len(self.get_bone_frames(bone_name))

    def get_total_frames(self) -> int:
        if not self.bones:
            return 0
        return max(len(frames) for frames in self.bones.values())

    def get_quat(self, bone_name: str, frame_index: int) -> List[float]:
        """
        Return quaternion in JSON order: [x, y, z, w]
        """
        frames = self.get_bone_frames(bone_name)

        if not frames:
            raise ValueError(f"Bone '{bone_name}' has no frames.")

        frame_index = frame_index % len(frames)
        frame_data = frames[frame_index]

        quat = frame_data.get("rot")
        if quat is None or len(quat) != 4:
            raise ValueError(
                f"Invalid quaternion for bone '{bone_name}', frame {frame_index}"
            )

        return quat

    def get_frame_number(self, bone_name: str, frame_index: int) -> int:
        frames = self.get_bone_frames(bone_name)
        frame_index = frame_index % len(frames)
        return int(frames[frame_index].get("f", frame_index))