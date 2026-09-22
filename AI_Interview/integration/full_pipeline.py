import asyncio
import time
import json
import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from audio.microphone import Microphone
from dsp.noise_suppression import NoiseSuppressor
from dsp.silero_vad import VoiceActivityDetector
from orchestration.utterance_detector import UtteranceDetector
from speech_to_text.faster_whisper_engine import FasterWhisperEngine
from nlp.transcript_cleaner import TranscriptCleaner
from core.config import config
from core.logger import get_logger

from resume_analyser.infrastructure.llm_extractor import MockLLMExtractor
from resume_analyser.application.use_cases.analyze_resume_use_case import AnalyzeResumeUseCase

from interview_brain.infrastructure.llm_agents import GroqQuestionGenerator, GroqTechnicalEvaluator
from interview_brain.application.orchestrator import InterviewOrchestrator
from interview_brain.domain.state import InterviewState, InterviewStatus
from interview_brain.infrastructure.state_update_engine import StateUpdateEngine
from interview_brain.infrastructure.adaptive_difficulty_engine import AdaptiveDifficultyEngine

logger = get_logger("FullInterviewPipeline")

class FullInterviewPipeline:
    def __init__(self):
        logger.info("Initializing Final Integrated AI Interview Coach...")
        # Phase 1 Audio Components
        self.mic = Microphone()
        self.noise_suppressor = NoiseSuppressor()
        self.vad = VoiceActivityDetector()
        self.whisper_engine = FasterWhisperEngine()
        self.utterance_detector = UtteranceDetector()
        self.cleaner = TranscriptCleaner()
        
        # Phase 3 Orchestration Components (Now using Groq!)
        self.q_gen = GroqQuestionGenerator()
        self.tech_eval = GroqTechnicalEvaluator()
        self.orchestrator = InterviewOrchestrator(self.q_gen, self.tech_eval)
        
    def _capture_utterance_blocking(self) -> str:
        """Runs the blocking audio capture loop until a single utterance is complete."""
        
        # We recreate the detector and buffers to ensure a clean slate per question
        from orchestration.utterance_detector import UtteranceDetector, UtteranceState
        from audio.circular_buffer import CircularBuffer
        from speech_to_text.streaming_buffer import StreamingBuffer
        
        detector = UtteranceDetector()
        circular_buffer = CircularBuffer(max_frames=config.audio.pre_roll_frames)
        streaming_buffer = StreamingBuffer()
        
        last_whisper_run = time.time()
        
        while True:
            frame = self.mic.get_frame(timeout=0.1)
            if frame is None:
                continue
                
            circular_buffer.add_frame(frame)
                
            clean_frame = self.noise_suppressor.process(frame)
            is_speech = self.vad.is_speech(clean_frame)
            state = detector.process_vad_result(is_speech)
            
            if state == "START":
                logger.info("[Event] Candidate Started Speaking")
                streaming_buffer.clear()
                
                preroll_frames = circular_buffer.get_all_frames()
                for pr_frame in preroll_frames:
                    streaming_buffer.add_frame(pr_frame)
                    
            elif state == "CONTINUE" and detector.state.name == "SPEECH_ACTIVE":
                streaming_buffer.add_frame(frame)
                
                # Live Transcript every 1 second
                if time.time() - last_whisper_run > 1.0:
                    current_audio = streaming_buffer.get_audio()
                    if len(current_audio) > config.audio.sample_rate * 0.5:
                        partial_text = self.whisper_engine.transcribe(current_audio)
                        logger.info(f"[Live Transcript]: {partial_text}")
                        last_whisper_run = time.time()
                        
            elif state == "END":
                logger.info("[Event] Candidate Stopped Speaking. Processing final transcript...")
                final_audio = streaming_buffer.get_audio()
                final_text = self.whisper_engine.transcribe(final_audio)
                cleaned_text = self.cleaner.clean(final_text)
                
                return cleaned_text

    async def run(self):
        """The main async loop of the AI Interview Coach."""
        try:
            # 1. Boot up Phase 2 (Resume Analyser)
            with open("sample_resume.json", "r") as f:
                raw_data = json.load(f)
                
            analyser = AnalyzeResumeUseCase(MockLLMExtractor())
            intelligence_payload = analyser.execute(raw_data)
            
            # 2. Boot up Phase 3 (State Initialization)
            state = self.orchestrator.initialize_session("SESSION_LIVE", intelligence_payload)
            
            logger.info("Starting Audio Hardware...")
            self.mic.start()
            
            # 3. The Interview Loop
            logger.info("=== INTERVIEW LIVE ===")
            
            # Run 3 real interactions
            for turn in range(3):
                if state.timers.elapsed_time_seconds > state.timers.total_allowed_mins * 60:
                    logger.info("Interview time has expired.")
                    break
                    
                # A. Generate Next Question
                state.status = InterviewStatus.GENERATING
                q_data = await self.q_gen.generate_next_question(state)
                
                # Text-to-Speech happens here. We just print.
                print("\n" + "="*80)
                print(f"🤖 AGENT: {q_data['question_text']}")
                print("="*80 + "\n")
                
                # B. Listen for Candidate Answer (Offload to prevent blocking asyncio loop)
                state.status = InterviewStatus.IN_PROGRESS
                logger.info("Listening to microphone...")
                
                # Run the blocking microphone capture in a background thread
                loop = asyncio.get_running_loop()
                candidate_answer = await loop.run_in_executor(None, self._capture_utterance_blocking)
                
                print("\n" + "="*80)
                print(f"🗣️ CANDIDATE: {candidate_answer}")
                print("="*80 + "\n")
                
                # C. Evaluate Answer
                state.status = InterviewStatus.EVALUATING
                eval_data = await self.tech_eval.evaluate_answer(state, candidate_answer)
                
                # D. Update State & Adapt
                StateUpdateEngine.log_qa_turn(state, q_data, candidate_answer, eval_data)
                StateUpdateEngine.recalculate_topic_scores(state)
                AdaptiveDifficultyEngine.adapt(state)
                
            state.status = InterviewStatus.COMPLETED
            print("\n" + "="*80)
            print("FINAL INTEGRATED INTERVIEW STATE DUMP:")
            print("="*80)
            print(state.model_dump_json(indent=2, exclude={"intelligence_payload"}))
            print("="*80 + "\n")

        except KeyboardInterrupt:
            logger.info("Interrupted by user.")
        finally:
            logger.info("Shutting down integrated pipeline...")
            self.mic.stop()
