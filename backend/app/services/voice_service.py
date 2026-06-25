"""
Kaizen AI - Voice Service
===========================
Speech-to-Text (Whisper) and Text-to-Speech (TTS-1-HD)
using the OpenAI Python client directly (not LangChain).
"""

import os
import tempfile
import logging
import re
from pathlib import Path

from num2words import num2words

from openai import AsyncOpenAI
from fastapi import UploadFile, HTTPException

from backend.app.config import settings

logger = logging.getLogger("kaizen.voice_service")


import edge_tts

# Singleton instance will be created at the end

class VoiceService:
    """Handles audio transcription (Whisper) and speech synthesis (Edge TTS)."""

    def __init__(self) -> None:
        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_BASE,
        )
        self.stt_model = settings.STT_MODEL      # whisper-1
        self.tts_voice = settings.TTS_VOICE      # en-IN-PrabhatNeural

    # ------------------------------------------------------------------ #
    #  Speech-to-Text                                                     #
    # ------------------------------------------------------------------ #

    async def speech_to_text(self, audio_file: UploadFile) -> str:
        """
        Transcribe an uploaded audio file using OpenAI Whisper.
        """
        # Read the raw audio bytes
        audio_bytes = await audio_file.read()
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Audio file is empty.")

        suffix = Path(audio_file.filename or "audio.webm").suffix or ".webm"
        tmp_path: str | None = None

        try:
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=suffix
            ) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name

            with open(tmp_path, "rb") as f:
                transcript = await self.client.audio.transcriptions.create(
                    model=self.stt_model,
                    file=f,
                    response_format="text",
                )

            logger.info("Transcribed audio (%d bytes) → %d chars", len(audio_bytes), len(transcript))
            return transcript.strip() if isinstance(transcript, str) else transcript.text.strip()

        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Speech-to-text failed: %s", exc)
            raise HTTPException(status_code=500, detail=f"Speech-to-text failed: {exc}") from exc
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

    # ------------------------------------------------------------------ #
    #  Text-to-Speech (Edge TTS)                                          #
    # ------------------------------------------------------------------ #

    def _normalize_text_for_english(self, text: str) -> str:
        """
        Converts numbers in text to their English word equivalents.
        Handles standard numbers, currencies, percentages, and years.
        This prevents bilingual TTS models (like en-IN) from defaulting to Hindi pronunciation.
        """
        if not text:
            return text
            
        # Replace rupees
        text = re.sub(r'₹\s*([0-9,.]+)', r'\1 rupees', text)
        # Replace dollars
        text = re.sub(r'\$\s*([0-9,.]+)', r'\1 dollars', text)
        # Replace percentages
        text = re.sub(r'([0-9,.]+)\s*%', r'\1 percent', text)

        def replace_num(match):
            num_str = match.group(0).replace(',', '')
            try:
                # Simple heuristic for years
                if len(num_str) == 4 and num_str.isdigit() and 1900 <= int(num_str) <= 2099:
                    return num2words(int(num_str), to='year')
                
                # General numbers
                if '.' in num_str:
                    return num2words(float(num_str))
                else:
                    return num2words(int(num_str))
            except:
                return match.group(0)

        # Find all standalone numbers or numbers with commas/decimals
        normalized = re.sub(r'\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\b|\b\d+(?:\.\d+)?\b', replace_num, text)
        
        return normalized

    async def text_to_speech(self, text: str) -> bytes:
        """
        Convert text to natural-sounding speech using Microsoft Edge TTS.

        Args:
            text: The text to synthesize.

        Returns:
            Raw MP3 audio bytes.
        """
        if not text or not text.strip():
            raise HTTPException(status_code=400, detail="Text for synthesis cannot be empty.")

        try:
            # Normalize the text so the TTS doesn't fall back to Hindi for digits
            normalized_text = self._normalize_text_for_english(text)
            
            # The user requested to increase the voice speed by 0.2 (20%)
            communicate = edge_tts.Communicate(normalized_text, self.tts_voice, rate="+20%")
            
            audio_data = bytearray()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data.extend(chunk["data"])
                    
            logger.info("Synthesized %d chars → %d bytes of audio via Edge TTS", len(text), len(audio_data))
            return bytes(audio_data)

        except Exception as exc:
            logger.error("Text-to-speech failed: %s", exc)
            raise HTTPException(
                status_code=500,
                detail=f"Text-to-speech failed: {exc}",
            ) from exc

# Singleton instance
voice_service = VoiceService()
