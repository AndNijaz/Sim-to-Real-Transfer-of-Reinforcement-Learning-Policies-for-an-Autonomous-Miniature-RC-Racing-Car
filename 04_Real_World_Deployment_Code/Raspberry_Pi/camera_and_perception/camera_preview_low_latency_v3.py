import time
import cv2
import depthai as dai


CAM_WIDTH = 320
CAM_HEIGHT = 180


def create_oak_pipeline_v3():
    pipeline = dai.Pipeline()

    cam = pipeline.create(dai.node.Camera).build()

    rgb_output = cam.requestOutput(
        (CAM_WIDTH, CAM_HEIGHT),
        type=dai.ImgFrame.Type.BGR888p,
    )

    rgb_queue = rgb_output.createOutputQueue()

    return pipeline, rgb_queue


def main():
    pipeline = None

    fps = 0.0
    frame_count = 0
    fps_start = time.time()

    try:
        pipeline, rgb_queue = create_oak_pipeline_v3()
        pipeline.start()

        print("Low-latency OAK-D preview started.")
        print("q = quit")
        print("p = save frame")

        while pipeline.isRunning():
            latest = None

            # Drain old frames and keep only newest frame.
            while rgb_queue.has():
                latest = rgb_queue.get()

            if latest is None:
                time.sleep(0.001)
                continue

            frame = latest.getCvFrame()

            frame_count += 1
            elapsed = time.time() - fps_start

            if elapsed >= 1.0:
                fps = frame_count / elapsed
                frame_count = 0
                fps_start = time.time()

            cv2.putText(
                frame,
                f"OAK-D preview | FPS: {fps:.1f}",
                (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )

            cv2.imshow("OAK-D Low Latency Preview", frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

            if key == ord("p"):
                filename = f"camera_angle_test_{int(time.time())}.jpg"
                cv2.imwrite(filename, frame)
                print(f"Saved frame: {filename}")

    finally:
        print("Closing preview.")

        if pipeline is not None:
            try:
                pipeline.stop()
            except Exception:
                pass

        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
