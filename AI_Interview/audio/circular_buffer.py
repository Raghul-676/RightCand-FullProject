import collections
import numpy as np
from typing import List

class CircularBuffer:
    def __init__(self, max_frames: int):
        """
        A ring buffer to keep the last 'max_frames' of audio in memory.
        This provides the 'pre-roll' needed to prevent speech clipping.
        """
        self.buffer = collections.deque(maxlen=max_frames)
        
    def add_frame(self, frame: np.ndarray):
        """Adds a new audio frame to the buffer. Drops oldest if full."""
        self.buffer.append(frame.copy())
        
    def get_all_frames(self) -> List[np.ndarray]:
        """Returns all currently buffered frames (the pre-roll)."""
        return list(self.buffer)
    
    def clear(self):
        """Clears the buffer."""
        self.buffer.clear()
