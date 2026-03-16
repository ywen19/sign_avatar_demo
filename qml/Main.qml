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
            position: Qt.vector3d(0, 80, 900)
            eulerRotation.x: -5
            clipNear: 1
            clipFar: 5000
        }

        DirectionalLight {
            eulerRotation.x: -30
            eulerRotation.y: -30
            brightness: 1.5
        }

        // 左边蓝色静态 cube
        Model {
            id: staticCube
            source: "#Cube"
            position: Qt.vector3d(-260, 0, 0)
            scale: Qt.vector3d(1.5, 1.5, 1.5)

            materials: DefaultMaterial {
                diffuseColor: "blue"
            }
        }

        // 中间 avatar
        RuntimeLoader {
            id: avatar
            source: Qt.resolvedUrl("../web/model.glb")
            position: Qt.vector3d(0, -180, 0)
            scale: Qt.vector3d(1000, 1000, 1000)

            onStatusChanged: {
                console.log("RuntimeLoader status:", status)
                if (status === RuntimeLoader.Success) {
                    console.log("GLB loaded successfully")
                } else if (status === RuntimeLoader.Error) {
                    console.log("GLB load error:", errorString)
                }
            }
        }

        // 右边红色动态 cube
        Node {
            id: testNode
            position: Qt.vector3d(260, 0, 0)

            property var q: animController.currentQuat
            rotation: Qt.quaternion(q[3], q[0], q[1], q[2])

            Model {
                source: "#Cube"
                scale: Qt.vector3d(1.5, 1.5, 1.5)

                materials: DefaultMaterial {
                    diffuseColor: "red"
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
}