import queue
import numpy as np
import sounddevice as sd
from core.config import config
from core.logger import get_logger

logger = get_logger("Microphone")

class Microphone:
    def __init__(self):
        self.sample_rate = config.audio.sample_rate
        self.channels = config.audio.channels
        self.chunk_size = config.audio.chunk_size
        
        # We use a thread-safe queue to pass frames from the audio callback
        # to the main processing thread.
        self.frame_queue = queue.Queue()
        self.stream = None

    def _audio_callback(self, indata: np.ndarray, frames: int, time, status: sd.CallbackFlags):
        """
        This callback is called by sounddevice for each new audio frame.
        It runs on a separate high-priority audio thread.
        """
        if status:
            logger.warning(f"Audio Callback Status: {status}")
            
        # indata is shape (frames, channels) as float32 between -1.0 and 1.0
        # We flatten it to a 1D array since we are using mono audio
        frame = indata.flatten()
        self.frame_queue.put(frame)

    def start(self):
        """Starts the microphone audio stream."""
        logger.info(f"Starting audio capture: {self.sample_rate}Hz, {self.channels} channels")
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype='float32',
            blocksize=self.chunk_size,
            callback=self._audio_callback
        )
        self.stream.start()

    def stop(self):
        """Stops the audio stream."""
        if self.stream:
            self.stream.stop()
            self.stream.close()
            logger.info("Audio capture stopped.")
            
    def get_frame(self, block=True, timeout=None) -> np.ndarray:
        """Retrieves the next frame from the queue."""
        try:
            return self.frame_queue.get(block=block, timeout=timeout)
        except queue.Empty:
            return None
