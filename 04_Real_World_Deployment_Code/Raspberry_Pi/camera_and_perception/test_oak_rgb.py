import depthai as dai
import cv2

# Create device and pipeline using DepthAI v3 style
device = dai.Device()

with dai.Pipeline(device) as pipeline:
    # Build RGB camera from CAM_A, which is the color camera on OAK-D Lite
    camera = pipeline.create(dai.node.Camera).build(dai.CameraBoardSocket.CAM_A)

    # Request output directly from the Camera node
    # We use 640x360 because this matches our planned PPO observation size
    output = camera.requestOutput(
        size=(640, 360),
        type=dai.ImgFrame.Type.BGR888p,
        fps=20
    )

    # Create output queue directly from the requested output
    queue = output.createOutputQueue(maxSize=4, blocking=False)

    pipeline.start()

    print("Capturing one RGB frame from OAK-D Lite...")

    packet = queue.get()
    frame = packet.getCvFrame()

    print("Frame captured.")
    print("Frame shape:", frame.shape)
    print("Frame dtype:", frame.dtype)

    cv2.imwrite("oak_test_frame.jpg", frame)
    print("Saved image as oak_test_frame.jpg")

