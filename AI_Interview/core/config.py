import os
import logging
from pydantic import BaseModel

class AudioConfig(BaseModel):
    sample_rate: int = 16000
    channels: int = 1
    # Frame duration in ms. 32ms = 512 samples at 16kHz
    frame_duration_ms: int = 32
    
    @property
    def chunk_size(self) -> int:
        """Returns the number of samples per frame."""
        return int(self.sample_rate * self.frame_duration_ms / 1000)
    
    # Pre-roll buffer size (in milliseconds)
    pre_roll_ms: int = 300
    # Number of frames to keep in pre-roll buffer
    @property
    def pre_roll_frames(self) -> int:
        return self.pre_roll_ms // self.frame_duration_ms

class VADConfig(BaseModel):
    threshold: float = 0.5
    # Minimum silence duration (in ms) to trigger End-of-Utterance
    pause_threshold_ms: int = 1500

class WhisperConfig(BaseModel):
    model_size: str = "large-v3-turbo" # Excellent balance of speed/accuracy for RTX 4060
    device: str = "cuda" # Use RTX 4060
    compute_type: str = "float16" # Optimal for RTX 4000 series

class SystemConfig(BaseModel):
    audio: AudioConfig = AudioConfig()
    vad: VADConfig = VADConfig()
    whisper: WhisperConfig = WhisperConfig()

config = SystemConfig()
