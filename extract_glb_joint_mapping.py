import json
import struct
from pathlib import Path


def load_glb_json(glb_path: str) -> dict:
    """
    读取 .glb 文件中的 JSON chunk，返回解析后的 glTF JSON dict
    """
    path = Path(glb_path)
    with path.open("rb") as f:
        data = f.read()

    # GLB header: magic, version, length
    if len(data) < 12:
        raise ValueError("文件太短，不是合法的 GLB。")

    magic, version, length = struct.unpack_from("<III", data, 0)

    if magic != 0x46546C67:  # b'glTF'
        raise ValueError("不是合法的 GLB 文件（magic 不对）。")

    if version != 2:
        raise ValueError(f"只支持 GLB v2，当前 version={version}")

    if length != len(data):
        raise ValueError("GLB header 里的 length 与实际文件长度不一致。")

    offset = 12
    json_chunk = None

    while offset < len(data):
        if offset + 8 > len(data):
            raise ValueError("GLB chunk header 不完整。")

        chunk_length, chunk_type = struct.unpack_from("<II", data, offset)
        offset += 8

        if offset + chunk_length > len(data):
            raise ValueError("GLB chunk 数据越界。")

        chunk_data = data[offset:offset + chunk_length]
        offset += chunk_length

        # JSON chunk type = 0x4E4F534A ('JSON')
        if chunk_type == 0x4E4F534A:
            json_chunk = chunk_data
            break

    if json_chunk is None:
        raise ValueError("GLB 中没有找到 JSON chunk。")

    json_text = json_chunk.decode("utf-8").rstrip("\x00 \t\r\n")
    return json.loads(json_text)


def extract_skin_joint_mapping(gltf: dict, skin_index: int = 0) -> dict:
    """
    提取指定 skin 的 joints 顺序和名称映射
    返回:
    {
        "skin_index": 0,
        "joint_count": ...,
        "joints": [
            {"joint_index": 0, "node_index": 12, "name": "Hips"},
            ...
        ],
        "name_to_joint_index": {
            "Hips": 0,
            ...
        }
    }
    """
    skins = gltf.get("skins", [])
    nodes = gltf.get("nodes", [])

    if not skins:
        raise ValueError("这个 glTF/GLB 里没有 skins。")

    if skin_index < 0 or skin_index >= len(skins):
        raise IndexError(f"skin_index 越界：{skin_index}，总 skins 数量={len(skins)}")

    skin = skins[skin_index]
    joint_node_indices = skin.get("joints", [])

    if not joint_node_indices:
        raise ValueError(f"skin[{skin_index}] 没有 joints。")

    joints = []
    name_to_joint_index = {}

    for joint_index, node_index in enumerate(joint_node_indices):
        if node_index < 0 or node_index >= len(nodes):
            raise IndexError(f"joint[{joint_index}] 的 node_index={node_index} 越界。")

        node = nodes[node_index]
        node_name = node.get("name", f"__unnamed_node_{node_index}")

        joints.append({
            "joint_index": joint_index,
            "node_index": node_index,
            "name": node_name
        })

        # 如果有重名，这里后者会覆盖前者；一般骨骼名应唯一
        name_to_joint_index[node_name] = joint_index

    return {
        "skin_index": skin_index,
        "joint_count": len(joints),
        "joints": joints,
        "name_to_joint_index": name_to_joint_index
    }


def main():
    glb_path = "./web/model.glb"
    output_path = "./web/model_joint_mapping.json"

    gltf = load_glb_json(glb_path)

    print("=== 基本信息 ===")
    print("scenes:", len(gltf.get("scenes", [])))
    print("nodes:", len(gltf.get("nodes", [])))
    print("skins:", len(gltf.get("skins", [])))
    print("animations:", len(gltf.get("animations", [])))

    mapping = extract_skin_joint_mapping(gltf, skin_index=0)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)

    print("\n=== joints 顺序映射（前 20 个）===")
    for item in mapping["joints"][:20]:
        print(
            f'joint[{item["joint_index"]}] -> '
            f'node[{item["node_index"]}] -> {item["name"]}'
        )

    print(f"\n已写出映射文件: {output_path}")


if __name__ == "__main__":
    main()