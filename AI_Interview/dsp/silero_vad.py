import torch
import numpy as np
import warnings
from core.config import config
from core.logger import get_logger

logger = get_logger("SileroVAD")

class VoiceActivityDetector:
    def __init__(self):
        self.threshold = config.vad.threshold
        self.sample_rate = config.audio.sample_rate
        
        # Suppress warnings from torch hub
        warnings.filterwarnings("ignore")
        
        logger.info("Loading Silero VAD model from Torch Hub...")
        # Load the VAD model. It runs efficiently on CPU.
        self.model, utils = torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            force_reload=False,
            onnx=False,
            trust_repo=True
        )
        self.model.eval() # Set to evaluation mode
        logger.info("Silero VAD loaded successfully.")

    def is_speech(self, frame: np.ndarray) -> bool:
        """
        Determines if the given audio frame contains speech.
        frame: float32 numpy array, typically 512 samples.
        """
        # Silero expects a torch tensor of shape (batch, samples)
        tensor_frame = torch.from_numpy(frame).float().unsqueeze(0)
        
        with torch.no_grad():
            # Get speech probability
            speech_prob = self.model(tensor_frame, self.sample_rate).item()
            
        return speech_prob > self.threshold
