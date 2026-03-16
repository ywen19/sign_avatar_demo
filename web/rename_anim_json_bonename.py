import json
import re
from pathlib import Path


def normalize_bone_name(name: str) -> str:
    return re.sub(r"^mixamorig", "", name)


def main():
    input_path = Path("./Dancing_mixamo_com_frames.json")
    output_path = Path("./Dancing_mixamo_com_frames_nomix.json")

    with input_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if "bones" not in data or not isinstance(data["bones"], dict):
        raise ValueError("JSON 里没有 bones 字典，结构和预期不符。")

    old_bones = data["bones"]
    new_bones = {}

    for old_name, value in old_bones.items():
        new_name = normalize_bone_name(old_name)
        new_bones[new_name] = value

    data["bones"] = new_bones

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Done: {output_path}")
    print("Example keys:")
    for k in list(new_bones.keys())[:10]:
        print(" -", k)


if __name__ == "__main__":
    main()