import re

with open('src/video/processor.py', 'r') as f:
    content = f.read()

# Update VideoProcessor __init__
init_old = """    def __init__(self, video_path: str, load_full: bool = False):
        self.video_path = video_path
        self.load_full = load_full

        self.cap = cv2.VideoCapture(video_path)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)

        self.frames = []
        if self.load_full:
            self._load_all_frames()

        # Background subtractor for motion detection (Option 1) - improved parameters
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=1000, varThreshold=100, detectShadows=False)"""

init_new = """    def __init__(self, video_path: str, load_mode: str = 'ondemand', buffer_size: int = 120):
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
            self.frame_buffer[start_idx + i] = frame"""

content = content.replace(init_old, init_new)

# Update _load_all_frames slightly if needed, but it's fine.

# Update get_frame
get_frame_old = """    def get_frame(self, frame_idx: int):
        if self.load_full:
            if 0 <= frame_idx < len(self.frames):
                return self.frames[frame_idx]
            return None
        else:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = self.cap.read()
            return frame if ret else None"""

get_frame_new = """    def get_frame(self, frame_idx: int):
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
            return frame if ret else None"""

content = content.replace(get_frame_old, get_frame_new)

with open('src/video/processor.py', 'w') as f:
    f.write(content)
