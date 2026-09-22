import os
import numpy as np
from faster_whisper import WhisperModel
from core.config import config
from core.logger import get_logger

logger = get_logger("FasterWhisper")

class FasterWhisperEngine:
    def __init__(self):
        logger.info(f"Loading Faster Whisper model: {config.whisper.model_size} on {config.whisper.device}...")
        
        # We explicitly set download_root to avoid any broken HF_HOME environment variables (like a missing F:\ drive)
        model_dir = os.path.join(os.getcwd(), "models")
        os.makedirs(model_dir, exist_ok=True)
        
        self.model = WhisperModel(
            config.whisper.model_size,
            device=config.whisper.device,
            compute_type=config.whisper.compute_type,
            download_root=model_dir
        )
        logger.info("Faster Whisper loaded successfully.")

    def transcribe(self, audio: np.ndarray) -> str:
        """
        Transcribes the given audio chunk.
        audio: 1D float32 numpy array at 16kHz
        """
        # Ensure the array is completely flattened and float32
        audio = audio.flatten().astype(np.float32)
        
        # Whisper model transcribe method natively accepts 1D numpy arrays
        segments, info = self.model.transcribe(
            audio, 
            beam_size=5, 
            language="en", 
            condition_on_previous_text=False
        )
        
        # segments is a generator. We must iterate it to get the text.
        text = "".join([segment.text for segment in segments])
        return text.strip()
