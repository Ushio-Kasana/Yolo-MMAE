import cv2
import numpy as np

class VideoProcessor:
    def __init__(self, video_path: str, load_full: bool = False):
        self.video_path = video_path
        self.load_full = load_full

        self.cap = cv2.VideoCapture(video_path)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)

        self.frames = []
        if self.load_full:
            self._load_all_frames()

        # Background subtractor for motion detection (Option 1)
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=50, detectShadows=False)

    def _load_all_frames(self):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            self.frames.append(frame)
        self.cap.release()

    def get_frame(self, frame_idx: int):
        if self.load_full:
            if 0 <= frame_idx < len(self.frames):
                return self.frames[frame_idx]
            return None
        else:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = self.cap.read()
            return frame if ret else None

    def release(self):
        if not self.load_full and self.cap:
            self.cap.release()

    def detect_motion(self, frame):
        """Returns bounding boxes of moving objects using background subtraction."""
        fg_mask = self.bg_subtractor.apply(frame)

        # Noise removal
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)

        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        boxes = []
        min_area = 500  # Minimum size to be considered an object
        for contour in contours:
            if cv2.contourArea(contour) > min_area:
                x, y, w, h = cv2.boundingRect(contour)
                boxes.append((x, y, w, h))
        return boxes


class ObjectTracker:
    def __init__(self):
        # We'll use CSRT as it's more accurate than KCF
        self.trackers = []

    def init_trackers(self, frame, boxes):
        """Initializes trackers with multiple bounding boxes.
        boxes is a list of (x, y, w, h)
        """
        self.trackers = []
        for box in boxes:
            tracker = cv2.TrackerCSRT_create()
            tracker.init(frame, tuple(box))
            self.trackers.append(tracker)

    def update(self, frame):
        """Updates all trackers on the new frame. Returns list of new bounding boxes."""
        new_boxes = []
        for tracker in self.trackers:
            success, box = tracker.update(frame)
            if success:
                new_boxes.append(tuple(map(int, box)))
            else:
                # Tracker failed, return None for this object
                new_boxes.append(None)
        return new_boxes
