import numpy as np
import noisereduce as nr
from core.config import config
from core.logger import get_logger

logger = get_logger("NoiseSuppression")

class NoiseSuppressor:
    def __init__(self):
        self.sample_rate = config.audio.sample_rate
        logger.info("Initialized Noise Suppressor (noisereduce)")

    def process(self, frame: np.ndarray) -> np.ndarray:
        """
        Applies spectral gating noise reduction on the frame.
        NOTE: noisereduce on 32ms (512 sample) chunks can cause aggressive gating
        that mutes the signal completely. Silero VAD is incredibly robust to noise
        on its own, so we will bypass this for now to ensure audio reaches the VAD.
        """
        return frame
