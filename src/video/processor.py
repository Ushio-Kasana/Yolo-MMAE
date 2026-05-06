# YOLO-MMAE - Video Annotator & Auto-Tracker
# Copyright (C) 2026  Ushio-Kasana
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
import cv2
import numpy as np

class VideoProcessor:
    def __init__(self, video_path: str, load_mode: str = 'ondemand', buffer_size: int = 120):
        self.video_path = video_path
        self.load_mode = load_mode # 'ondemand', 'full', 'buffered'
        self.buffer_size = buffer_size

        self.cap = cv2.VideoCapture(video_path)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)

        self.frames = [] # For full load
        self.frame_buffer = {} # For buffered load: map frame_idx -> frame
        self.buffer_start_idx = -1

        if self.load_mode == 'full':
            self._load_all_frames()
        elif self.load_mode == 'buffered':
            self._load_buffer(0)

        # Background subtractor for motion detection (Option 1) - improved parameters
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=1000, varThreshold=100, detectShadows=False)

    def _load_buffer(self, start_idx: int):
        self.frame_buffer.clear()
        self.buffer_start_idx = start_idx
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, start_idx)
        for i in range(self.buffer_size):
            ret, frame = self.cap.read()
            if not ret:
                break
            self.frame_buffer[start_idx + i] = frame

    def _load_all_frames(self):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            self.frames.append(frame)
        self.cap.release()

    def get_frame(self, frame_idx: int):
        if self.load_mode == 'full':
            if 0 <= frame_idx < len(self.frames):
                return self.frames[frame_idx]
            return None
        elif self.load_mode == 'buffered':
            # Check if we need to load the next buffer
            if frame_idx not in self.frame_buffer:
                # If they jumped somewhere, load a new buffer starting there
                self._load_buffer(frame_idx)
            # If they are near the end of the buffer (e.g. last 20 frames), trigger a background load of next?
            # For simplicity, we just load the next chunk if it's missing.
            # To meet the request "once those frames are used or at the last 20 then load the nest lot"
            # we can eagerly load the next buffer if we are within 20 frames of the end
            max_buffered_idx = max(self.frame_buffer.keys()) if self.frame_buffer else -1
            if max_buffered_idx != -1 and frame_idx >= max_buffered_idx - 20 and max_buffered_idx < self.total_frames - 1:
                # Need to load more frames seamlessly
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, max_buffered_idx + 1)
                for i in range(self.buffer_size):
                    ret, frame = self.cap.read()
                    if not ret:
                        break
                    self.frame_buffer[max_buffered_idx + 1 + i] = frame
                # Keep buffer from growing infinitely
                if len(self.frame_buffer) > self.buffer_size * 2:
                    keys_to_remove = sorted(list(self.frame_buffer.keys()))[:self.buffer_size]
                    for k in keys_to_remove:
                        del self.frame_buffer[k]

            return self.frame_buffer.get(frame_idx, None)
        else: # 'ondemand'
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = self.cap.read()
            return frame if ret else None

    def release(self):
        if not self.load_full and self.cap:
            self.cap.release()

    def detect_motion(self, frame):
        """Returns bounding boxes of moving objects using background subtraction."""
        # Blur frame first to reduce minor noise (leaves, camera grain)
        blurred = cv2.GaussianBlur(frame, (5, 5), 0)
        fg_mask = self.bg_subtractor.apply(blurred)

        # Robust noise removal and filling gaps
        kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))

        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel_open)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel_close)

        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        boxes = []
        min_area = 1000  # Increased minimum size to ignore small noise
        for contour in contours:
            if cv2.contourArea(contour) > min_area:
                x, y, w, h = cv2.boundingRect(contour)
                boxes.append((x, y, w, h))

        # Optional: merge overlapping boxes here if needed
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

class ImageSequenceProcessor:
    """Mimics VideoProcessor but works off a list of image file paths."""
    def __init__(self, image_paths: list):
        self.image_paths = sorted(image_paths)
        self.total_frames = len(self.image_paths)
        self.fps = 0 # No defined FPS for an image sequence

        # Background subtractor for motion detection (Option 1) - improved parameters
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=1000, varThreshold=100, detectShadows=False)

    def get_frame(self, frame_idx: int):
        if 0 <= frame_idx < self.total_frames:
            # Read directly from disk
            return cv2.imread(str(self.image_paths[frame_idx]))
        return None

    def release(self):
        pass # Nothing to release for static images

    def detect_motion(self, frame):
        """Returns bounding boxes of moving objects using background subtraction."""
        # Blur frame first to reduce minor noise (leaves, camera grain)
        blurred = cv2.GaussianBlur(frame, (5, 5), 0)
        fg_mask = self.bg_subtractor.apply(blurred)

        # Robust noise removal and filling gaps
        kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))

        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel_open)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel_close)

        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        boxes = []
        min_area = 1000  # Increased minimum size to ignore small noise
        for contour in contours:
            if cv2.contourArea(contour) > min_area:
                x, y, w, h = cv2.boundingRect(contour)
                boxes.append((x, y, w, h))

        # Optional: merge overlapping boxes here if needed
        return boxes
