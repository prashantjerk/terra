"""Camera adapters returning OpenCV BGR frames; no preview required."""
import time
import cv2


class Camera:
    def __init__(self, source="pi", width=640, height=480):
        self.pi = None
        self.usb = None
        try:
            if source == "pi":
                try:
                    from picamera2 import Picamera2
                except ImportError as exc:
                    raise RuntimeError("Install python3-picamera2 using setup.sh, or use --camera usb") from exc
                self.pi = Picamera2()
                # Picamera2 RGB888 arrays have BGR byte order, matching OpenCV.
                self.pi.configure(self.pi.create_video_configuration(
                    main={"size": (width, height), "format": "RGB888"}))
                self.pi.start()
            else:
                self.usb = cv2.VideoCapture(int(source))
                self.usb.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                self.usb.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                if not self.usb.isOpened():
                    raise RuntimeError(f"Cannot open USB camera {source}")
            time.sleep(2)
        except Exception:
            self.close()
            raise

    def read(self):
        if self.pi is not None:
            frame = self.pi.capture_array("main")
        else:
            ok, frame = self.usb.read()
            if not ok:
                raise RuntimeError("Camera frame capture failed")
        if frame is None or frame.size == 0:
            raise RuntimeError("Camera returned an empty frame")
        return frame

    def close(self):
        if self.pi is not None:
            self.pi.close()
        if self.usb is not None:
            self.usb.release()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
