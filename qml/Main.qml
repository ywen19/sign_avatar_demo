import QtQuick
import QtQuick3D
import QtQuick3D.AssetUtils

Rectangle {
    anchors.fill: parent
    color: "#202020"

    View3D {
        anchors.fill: parent

        environment: SceneEnvironment {
            clearColor: "#202020"
            backgroundMode: SceneEnvironment.Color
        }

        Node {
            id: cameraRig
            position: Qt.vector3d(0, 230, 300)

            PerspectiveCamera {
                id: camera
                position: Qt.vector3d(0, 0, 0)
                eulerRotation.x: -10
            }
        }

        DirectionalLight {
            eulerRotation.x: -35
            eulerRotation.y: -30
            brightness: 1.2
        }

        RuntimeLoader {
            id: avatar
            source: Qt.resolvedUrl("../web/model.glb")
            scale: Qt.vector3d(2000, 2000, 2000)

            onStatusChanged: {
                console.log("RuntimeLoader status:", status)
                if (status === RuntimeLoader.Success) {
                    console.log("GLB loaded successfully")
                } else if (status === RuntimeLoader.Error) {
                    console.log("GLB load error:", errorString)
                }
            }
        }
    }
}