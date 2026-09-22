import numpy as np
from typing import List

class StreamingBuffer:
    def __init__(self):
        """
        Accumulates audio frames while the user is speaking.
        This provides the growing audio chunk to Whisper for incremental transcription.
        """
        self.frames = []
        
    def add_frame(self, frame: np.ndarray):
        """Appends a new frame to the active speech buffer."""
        self.frames.append(frame.copy())
        
    def get_audio(self) -> np.ndarray:
        """Returns the entire accumulated audio as a single 1D numpy array."""
        if not self.frames:
            return np.array([], dtype=np.float32)
        return np.concatenate(self.frames)
        
    def get_duration_ms(self, sample_rate: int) -> int:
        """Returns the total duration of accumulated audio in milliseconds."""
        audio = self.get_audio()
        if len(audio) == 0:
            return 0
        return int((len(audio) / sample_rate) * 1000)
        
    def clear(self):
        """Clears the streaming buffer."""
        self.frames.clear()
