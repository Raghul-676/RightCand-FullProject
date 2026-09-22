import time
import json
import threading
from datetime import datetime
from queue import Empty

from core.config import config
from core.logger import get_logger
from audio.microphone import Microphone
from audio.circular_buffer import CircularBuffer
from dsp.noise_suppression import NoiseSuppressor
from dsp.silero_vad import VoiceActivityDetector
from speech_to_text.streaming_buffer import StreamingBuffer
from speech_to_text.faster_whisper_engine import FasterWhisperEngine
from nlp.transcript_cleaner import TranscriptCleaner
from orchestration.utterance_detector import UtteranceDetector

logger = get_logger("PipelineManager")

class PipelineManager:
    def __init__(self):
        # Initialize modules
        self.mic = Microphone()
        self.circular_buffer = CircularBuffer(max_frames=config.audio.pre_roll_frames)
        self.noise_suppressor = NoiseSuppressor()
        self.vad = VoiceActivityDetector()
        self.streaming_buffer = StreamingBuffer()
        self.whisper_engine = FasterWhisperEngine()
        self.cleaner = TranscriptCleaner()
        self.detector = UtteranceDetector()
        
        self.is_running = False
        self.worker_thread = None
        
    def start(self):
        """Starts the audio pipeline."""
        self.is_running = True
        self.mic.start()
        
        # Run processing in a separate thread so it doesn't block
        self.worker_thread = threading.Thread(target=self._processing_loop)
        self.worker_thread.start()
        logger.info("Pipeline processing started. Speak into the microphone.")

    def stop(self):
        """Stops the audio pipeline."""
        self.is_running = False
        self.mic.stop()
        if self.worker_thread:
            self.worker_thread.join()
        logger.info("Pipeline stopped.")

    def _processing_loop(self):
        """Main loop that constantly processes audio frames."""
        last_whisper_run = time.time()
        
        while self.is_running:
            # 1. Get audio frame from Microphone
            frame = self.mic.get_frame(timeout=0.1)
            if frame is None:
                continue
                
            # 2. Add to Circular Buffer (Pre-roll time machine)
            self.circular_buffer.add_frame(frame)
            
            # 3. Noise Suppression
            clean_frame = self.noise_suppressor.process(frame)
            
            # 4. Voice Activity Detection
            is_speech = self.vad.is_speech(clean_frame)
            
            # 5. Utterance State Machine
            state = self.detector.process_vad_result(is_speech)
            
            if state == "START":
                logger.info("[Event] Speech Started")
                self.streaming_buffer.clear()
                
                # Push the pre-roll from circular buffer into the streaming buffer
                preroll_frames = self.circular_buffer.get_all_frames()
                for pr_frame in preroll_frames:
                    self.streaming_buffer.add_frame(pr_frame)
                    
            elif state == "CONTINUE" and self.detector.state.name == "SPEECH_ACTIVE":
                # User is actively speaking. Add current frame.
                self.streaming_buffer.add_frame(frame)
                
                # Every 1.0 second of new active speech, we can run Whisper for a partial transcript
                if time.time() - last_whisper_run > 1.0:
                    current_audio = self.streaming_buffer.get_audio()
                    # To avoid blocking the VAD loop, in a true production system 
                    # Whisper inference should run in its own sub-thread.
                    # For this implementation, we run it directly here to demonstrate flow.
                    if len(current_audio) > config.audio.sample_rate * 0.5: # At least 0.5s
                        partial_text = self.whisper_engine.transcribe(current_audio)
                        logger.info(f"[Live Transcript]: {partial_text}")
                        last_whisper_run = time.time()

            elif state == "END":
                logger.info("[Event] Speech Ended")
                self._handle_end_of_utterance()
                
    def _handle_end_of_utterance(self):
        """Called when the user finishes answering."""
        # 1. Get full accumulated audio
        audio = self.streaming_buffer.get_audio()
        duration_ms = self.streaming_buffer.get_duration_ms(config.audio.sample_rate)
        
        # 2. Final Whisper Inference
        logger.info("Running final Whisper inference...")
        raw_text = self.whisper_engine.transcribe(audio)
        
        # 3. Cleanup transcript
        clean_text = self.cleaner.clean(raw_text)
        
        # 4. Calculate metrics
        words = clean_text.split()
        word_count = len(words)
        duration_mins = duration_ms / 60000.0
        wpm = int(word_count / duration_mins) if duration_mins > 0 else 0
        
        # 5. Generate Output JSON
        output = {
            "question_id": "Q_DEMO",
            "transcript": clean_text,
            "transcript_confidence": 0.95, # Placeholder, Whisper can provide this per-token
            "speaking_duration_ms": duration_ms,
            "average_speech_rate_wpm": wpm,
            "average_pause_duration_ms": config.vad.pause_threshold_ms,
            "language": "en",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "audio_quality_score": 0.90 # Placeholder
        }
        
        print("\n" + "="*50)
        print("FINAL INTERVIEW AGENT PAYLOAD:")
        print(json.dumps(output, indent=2))
        print("="*50 + "\n")
        
        # Clear buffer for next utterance
        self.streaming_buffer.clear()
