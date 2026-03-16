import QtQuick
import QtQuick3D
import QtQuick3D.AssetUtils

Rectangle {
    anchors.fill: parent
    color: "#202020"

    View3D {
        anchors.fill: parent
        camera: camera

        environment: SceneEnvironment {
            backgroundMode: SceneEnvironment.Color
            clearColor: "#202020"
        }

        PerspectiveCamera {
            id: camera
            position: Qt.vector3d(0, 0, 300)
            eulerRotation.x: -5
            clipNear: 1
            clipFar: 5000
        }

        DirectionalLight {
            eulerRotation.x: -30
            eulerRotation.y: -30
            brightness: 1.5
        }

        // 中间 avatar
        RuntimeLoader {
            id: avatar
            source: Qt.resolvedUrl("../web/model.glb")
            position: Qt.vector3d(0, -180, 0)
            scale: Qt.vector3d(1000, 1000, 1000)

            property var skinnedModel: null
            property var jointsArray: []
            property int testJointIndex: 0   // Hips -> 0

            function indent(n) {
                var s = ""
                for (var i = 0; i < n; ++i)
                    s += "  "
                return s
            }

            function dumpTree(obj, depth) {
                if (!obj)
                    return

                var name = ""
                try {
                    name = obj.objectName
                } catch(e) {
                }

                console.log(indent(depth) + "obj =", obj, " objectName =", name)

                try {
                    if (obj.skin) {
                        console.log(indent(depth) + "  has skin =", obj.skin)

                        if (obj.skin.joints) {
                            console.log(indent(depth) + "  joints count =", obj.skin.joints.length)

                            if (!skinnedModel) {
                                skinnedModel = obj
                                jointsArray = obj.skin.joints
                                console.log("Captured skinnedModel =", skinnedModel)
                                console.log("Captured jointsArray length =", jointsArray.length)
                            }

                            for (var i = 0; i < obj.skin.joints.length; ++i) {
                                var j = obj.skin.joints[i]
                                var jname = ""
                                try {
                                    jname = j.objectName
                                } catch(e) {
                                }
                                console.log(indent(depth) + "    joint[" + i + "] =", j, " name =", jname)
                            }
                        }
                    }
                } catch(e) {
                    console.log(indent(depth) + "  skin inspect error:", e)
                }

                try {
                    if (obj.children) {
                        for (var c = 0; c < obj.children.length; ++c) {
                            dumpTree(obj.children[c], depth + 1)
                        }
                    }
                } catch(e) {
                    console.log(indent(depth) + "  children inspect error:", e)
                }
            }

            onStatusChanged: {
                console.log("RuntimeLoader status:", status)
                if (status === RuntimeLoader.Success) {
                    console.log("GLB loaded successfully")
                    console.log("=== DUMP avatar tree START ===")
                    dumpTree(avatar, 0)
                    console.log("=== DUMP avatar tree END ===")
                } else if (status === RuntimeLoader.Error) {
                    console.log("GLB load error:", errorString)
                }
            }
        }


        // 用 animController.currentQuat 驱动 avatar 的 joint[0]（Hips）
        Timer {
            interval: 33
            running: avatar.jointsArray.length > 0
            repeat: true

            onTriggered: {
                try {
                    var allQuats = animController.currentJointQuats
                    var n = Math.min(avatar.jointsArray.length, allQuats.length)

                    for (var i = 0; i < n; ++i) {
                        var j = avatar.jointsArray[i]
                        var q = allQuats[i]

                        if (j && q && q.length === 4) {
                            j.rotation = Qt.quaternion(q[3], q[0], q[1], q[2])
                        }
                    }
                } catch(e) {
                    console.log("joint anim error:", e)
                }
            }
        }
    }

    Text {
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.margins: 12
        color: "white"
        font.pixelSize: 20
        text: "frame=" + animController.currentFrame
    }

    Text {
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.topMargin: 44
        anchors.leftMargin: 12
        color: "yellow"
        font.pixelSize: 18
        text: "jointCount=" + avatar.jointsArray.length + "  Hips->0"
    }
}