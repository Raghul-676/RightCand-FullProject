from enum import Enum
from core.config import config
from core.logger import get_logger

logger = get_logger("UtteranceDetector")

class UtteranceState(Enum):
    SILENCE = 0
    SPEECH_ACTIVE = 1

class UtteranceDetector:
    def __init__(self):
        self.state = UtteranceState.SILENCE
        self.silence_frames_count = 0
        self.speech_frames_count = 0
        
        # Calculate how many frames make up the pause threshold
        # If threshold is 1500ms and frame is 32ms: 1500 / 32 = ~46 frames
        self.pause_threshold_frames = config.vad.pause_threshold_ms // config.audio.frame_duration_ms
        
        logger.info(f"Utterance Detector initialized. Pause threshold: {config.vad.pause_threshold_ms}ms ({self.pause_threshold_frames} frames)")

    def process_vad_result(self, is_speech: bool) -> str:
        """
        State machine to determine speech boundaries based on VAD.
        Returns:
            "START" if speech just started
            "END" if speech just ended
            "CONTINUE" if status is unchanged
        """
        if is_speech:
            self.silence_frames_count = 0
            if self.state == UtteranceState.SILENCE:
                self.state = UtteranceState.SPEECH_ACTIVE
                return "START"
            else:
                self.speech_frames_count += 1
                return "CONTINUE"
        else:
            if self.state == UtteranceState.SPEECH_ACTIVE:
                self.silence_frames_count += 1
                
                # Check if we've been silent long enough to mark the end of utterance
                if self.silence_frames_count >= self.pause_threshold_frames:
                    self.state = UtteranceState.SILENCE
                    self.silence_frames_count = 0
                    self.speech_frames_count = 0
                    return "END"
                else:
                    return "CONTINUE"
            else:
                return "CONTINUE"
