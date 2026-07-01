import time
import cv2

from perception.real_camera_adapter import RealCameraAdapter


def main():
    camera = RealCameraAdapter(width=640, height=360, fps=20, normalize=False)

    try:
        camera.start()

        print("Camera started.")
        print("Capturing 30 observations...")

        start_time = time.time()

        last_obs = None

        for i in range(30):
            obs = camera.get_observation()
            last_obs = obs

            print(
                f"Frame {i + 1:02d}: "
                f"shape={obs.shape}, "
                f"dtype={obs.dtype}, "
                f"min={obs.min()}, "
                f"max={obs.max()}"
            )

        elapsed = time.time() - start_time
        fps = 30 / elapsed

        print(f"Approx FPS: {fps:.2f}")

        if last_obs is not None:
            cv2.imwrite("real_camera_adapter_test.jpg", last_obs)
            print("Saved real_camera_adapter_test.jpg")

    finally:
        try:
            camera.close()
            print("Camera closed.")
        except Exception as e:
            print(f"Camera close warning: {e}")

if __name__ == "__main__":
    main()
