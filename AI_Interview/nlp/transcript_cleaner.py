import re
from core.logger import get_logger

logger = get_logger("TranscriptCleaner")

class TranscriptCleaner:
    def __init__(self):
        pass
        
    def clean(self, text: str) -> str:
        """
        Cleans the raw transcript from Whisper.
        We preserve filler words ("um", "uh") for the Interview Agent.
        """
        if not text:
            return ""
            
        # 1. Normalise whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # 2. Fix repeated punctuation hallucinated by AI
        text = re.sub(r'([,\.!?])\1+', r'\1', text)
        
        # 3. Trim leading/trailing spaces
        text = text.strip()
        
        # 4. Ensure it starts with a capital letter
        if text:
            text = text[0].upper() + text[1:]
            
        return text
