import time
from collections import deque
from typing import Optional, Tuple

import cv2
import depthai as dai
import numpy as np


class RealCameraAdapter:
    """
    Real OAK-D Lite camera adapter for sim-to-real RL inference.

    Main purpose:
    - Capture the newest RGB frame from OAK-D Lite
    - Resize it to the model input size
    - Convert it into the same observation format expected by the RL policy

    Supported output formats:
    - HWC uint8:  (height, width, 3)
    - CHW uint8:  (3, height, width)
    - CHW float32 normalized: values in [0, 1]
    - stacked CHW: (frame_stack * 3, height, width)

    Recommended first test:
        width=160, height=120, channels_first=True, normalize=False, frame_stack=4

    Later we will match this exactly to the Webots model observation shape.
    """

    def __init__(
        self,
        width: int = 160,
        height: int = 120,
        fps: Optional[int] = None,
        channels_first: bool = True,
        normalize: bool = False,
        convert_bgr_to_rgb: bool = True,
        frame_stack: int = 1,
    ):
        self.width = width
        self.height = height
        self.fps = fps

        self.channels_first = channels_first
        self.normalize = normalize
        self.convert_bgr_to_rgb = convert_bgr_to_rgb

        self.frame_stack = max(1, int(frame_stack))
        self.frames = deque(maxlen=self.frame_stack)

        self.pipeline = None
        self.rgb_queue = None
        self.started = False

        self.frame_count = 0
        self.start_time = None
        self.last_frame_time = None

    def _create_pipeline(self):
        """
        DepthAI v3 pipeline.

        This uses the newer Camera node API.
        It avoids XLinkOut because DepthAI v3 removed the old manual XLinkOut style.
        """
        pipeline = dai.Pipeline()

        cam = pipeline.create(dai.node.Camera).build()

        # Request BGR output because OpenCV uses BGR naturally.
        rgb_output = cam.requestOutput(
            (self.width, self.height),
            type=dai.ImgFrame.Type.BGR888p,
        )

        rgb_queue = rgb_output.createOutputQueue()

        return pipeline, rgb_queue

    def start(self):
        if self.started:
            return

        self.pipeline, self.rgb_queue = self._create_pipeline()
        self.pipeline.start()

        self.started = True
        self.frame_count = 0
        self.start_time = time.time()
        self.last_frame_time = None

        print("RealCameraAdapter started.")
        print(f"Output size: {self.width}x{self.height}")
        print(f"channels_first: {self.channels_first}")
        print(f"normalize: {self.normalize}")
        print(f"convert_bgr_to_rgb: {self.convert_bgr_to_rgb}")
        print(f"frame_stack: {self.frame_stack}")

    def stop(self):
        if self.pipeline is not None:
            try:
                self.pipeline.stop()
            except Exception:
                pass

        self.pipeline = None
        self.rgb_queue = None
        self.started = False

        print("RealCameraAdapter stopped.")

    def _get_latest_raw_frame(self, timeout_seconds: float = 2.0) -> Optional[np.ndarray]:
        """
        Gets the newest available frame and skips old buffered frames.

        This is important for low latency:
        we do NOT want old frames from the queue.
        """
        if not self.started:
            raise RuntimeError("Camera is not started. Call start() first.")

        start_wait = time.time()
        latest = None

        while time.time() - start_wait < timeout_seconds:
            # Drain queue, keep only newest frame.
            while self.rgb_queue.has():
                latest = self.rgb_queue.get()

            if latest is not None:
                frame = latest.getCvFrame()
                self.frame_count += 1
                self.last_frame_time = time.time()
                return frame

            time.sleep(0.001)

        return None

    def _preprocess_single_frame(self, frame_bgr: np.ndarray) -> np.ndarray:
        """
        Converts raw camera frame into model-ready single-frame observation.
        """
        frame = frame_bgr

        # Safety resize. Usually DepthAI already gives requested size,
        # but this ensures exact shape.
        if frame.shape[1] != self.width or frame.shape[0] != self.height:
            frame = cv2.resize(frame, (self.width, self.height), interpolation=cv2.INTER_AREA)

        # Convert BGR to RGB if the model expects RGB-like Webots camera input.
        if self.convert_bgr_to_rgb:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        if self.normalize:
            frame = frame.astype(np.float32) / 255.0
        else:
            frame = frame.astype(np.uint8)

        if self.channels_first:
            # HWC -> CHW
            frame = np.transpose(frame, (2, 0, 1))

        return frame

    def get_observation(self, timeout_seconds: float = 2.0) -> np.ndarray:
        """
        Returns one RL observation.

        If frame_stack == 1:
            returns one frame.

        If frame_stack > 1:
            returns stacked frames along channel axis if channels_first=True.
            Example:
                4 RGB frames -> shape (12, H, W)
        """
        raw_frame = self._get_latest_raw_frame(timeout_seconds=timeout_seconds)

        if raw_frame is None:
            raise TimeoutError("No camera frame received from OAK-D Lite.")

        processed = self._preprocess_single_frame(raw_frame)

        # Fill frame stack at startup with the first frame.
        if len(self.frames) == 0:
            for _ in range(self.frame_stack):
                self.frames.append(processed.copy())
        else:
            self.frames.append(processed.copy())

        if self.frame_stack == 1:
            return processed

        if self.channels_first:
            # Each frame: (3, H, W)
            # Stacked:    (3 * frame_stack, H, W)
            return np.concatenate(list(self.frames), axis=0)

        # Each frame: (H, W, 3)
        # Stacked:    (H, W, 3 * frame_stack)
        return np.concatenate(list(self.frames), axis=2)

    def get_raw_frame_for_preview(self, timeout_seconds: float = 2.0) -> np.ndarray:
        """
        Returns raw BGR frame for preview/debug only.
        Do not use this for model inference.
        """
        raw_frame = self._get_latest_raw_frame(timeout_seconds=timeout_seconds)

        if raw_frame is None:
            raise TimeoutError("No camera frame received from OAK-D Lite.")

        return raw_frame

    def get_average_fps(self) -> float:
        if self.start_time is None:
            return 0.0

        elapsed = time.time() - self.start_time

        if elapsed <= 0:
            return 0.0

        return self.frame_count / elapsed

    def get_info(self) -> dict:
        return {
            "width": self.width,
            "height": self.height,
            "channels_first": self.channels_first,
            "normalize": self.normalize,
            "convert_bgr_to_rgb": self.convert_bgr_to_rgb,
            "frame_stack": self.frame_stack,
            "average_fps": self.get_average_fps(),
            "last_frame_time": self.last_frame_time,
        }

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()

