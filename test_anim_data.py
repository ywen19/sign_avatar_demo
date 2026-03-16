from anim_data import AnimationData

anim = AnimationData("web/Dancing_mixamo_com_frames_nomix.json")

print("name:", anim.name)
print("fps:", anim.fps)
print("bones:", anim.get_bone_names()[:10])
print("has Hips:", anim.has_bone("Hips"))
print("Hips frame count:", anim.get_bone_frame_count("Hips"))
print("Hips frame 0 quat:", anim.get_quat("Hips", 0))