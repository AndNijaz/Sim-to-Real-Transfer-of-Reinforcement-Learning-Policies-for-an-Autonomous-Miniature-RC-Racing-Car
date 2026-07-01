import time
import sys
import cv2
import depthai as dai
from datetime import datetime


# =========================
# SETTINGS
# =========================

CAM_WIDTH = 640
CAM_HEIGHT = 360

# Change this if you want longer/shorter recording.
# You can also pass duration from terminal:
# python camera_record_v3.py 20
DEFAULT_RECORD_SECONDS = 60

# MJPG AVI is usually the most reliable OpenCV format on Raspberry Pi.
OUTPUT_FPS = 20.0


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
    record_seconds = DEFAULT_RECORD_SECONDS

    if len(sys.argv) > 1:
        try:
            record_seconds = float(sys.argv[1])
        except ValueError:
            print("Invalid duration argument. Using default duration.")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"oak_record_{timestamp}.avi"

    pipeline = None
    writer = None

    frame_count = 0
    start_time = None

    print("Starting OAK-D Lite recording...")
    print(f"Resolution: {CAM_WIDTH}x{CAM_HEIGHT}")
    print(f"Duration: {record_seconds} seconds")
    print(f"Output file: {output_path}")

    try:
        pipeline, rgb_queue = create_oak_pipeline_v3()
        pipeline.start()

        fourcc = cv2.VideoWriter_fourcc(*"MJPG")
        writer = cv2.VideoWriter(
            output_path,
            fourcc,
            OUTPUT_FPS,
            (CAM_WIDTH, CAM_HEIGHT),
        )

        if not writer.isOpened():
            raise RuntimeError("Could not open video writer. Try changing codec or output format.")

        start_time = time.time()
        last_print = start_time

        while pipeline.isRunning():
            now = time.time()
            elapsed = now - start_time

            if elapsed >= record_seconds:
                break

            latest = None

            # Keep only newest frame, skip old buffered frames.
            while rgb_queue.has():
                latest = rgb_queue.get()

            if latest is None:
                time.sleep(0.001)
                continue

            frame = latest.getCvFrame()

            # Optional overlay
            cv2.putText(
                frame,
                f"OAK-D Lite recording | t={elapsed:.1f}s",
                (15, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )

            writer.write(frame)
            frame_count += 1

            if now - last_print >= 1.0:
                current_fps = frame_count / elapsed if elapsed > 0 else 0
                print(f"Recording... {elapsed:.1f}s / {record_seconds}s | avg FPS: {current_fps:.2f}")
                last_print = now

        total_time = time.time() - start_time
        avg_fps = frame_count / total_time if total_time > 0 else 0

        print("\nRecording finished.")
        print(f"Saved file: {output_path}")
        print(f"Frames recorded: {frame_count}")
        print(f"Average FPS: {avg_fps:.2f}")

    finally:
        if writer is not None:
            writer.release()

        if pipeline is not None:
            try:
                pipeline.stop()
            except Exception:
                pass


if __name__ == "__main__":
    main()
