"""
Kaizen AI - Voice Service
===========================
Speech-to-Text (Whisper) and Text-to-Speech (Edge TTS)
Sab kuch English mein bolta hai — numbers bhi.

Requirements:
    pip install openai edge-tts num2words fastapi
"""

import os
import re
import tempfile
import logging
from pathlib import Path

import edge_tts
from num2words import num2words
from openai import AsyncOpenAI
from fastapi import UploadFile, HTTPException

from backend.app.config import settings

logger = logging.getLogger("kaizen.voice_service")


# ------------------------------------------------------------------ #
#  Helper: Convert numbers → English words before TTS                #
# ------------------------------------------------------------------ #

def _convert_number(match: re.Match) -> str:
    """
    Regex match ke andar ka number English words mein convert karta hai.
    Example: "123" → "one hundred and twenty-three"
             "3.14" → "three point one four"
    """
    raw = match.group(0).replace(",", "")  # Remove commas (e.g. 1,000 → 1000)
    try:
        if "." in raw:
            num = float(raw)
        else:
            num = int(raw)
        return num2words(num, lang="en")
    except (ValueError, TypeError):
        return match.group(0)  # Convert fail ho toh original rakhna


def replace_numbers_with_words(text: str) -> str:
    """
    Text ke andar saare numbers ko English words se replace karta hai.
    Yeh SSML ya TTS engine pe depend kiye bina kaam karta hai.
    """
    # Matches integers, decimals aur comma-separated numbers (e.g. 1,000,000)
    return re.sub(r"\d[\d,.]*", _convert_number, text)


# ------------------------------------------------------------------ #
#  VoiceService Class                                                 #
# ------------------------------------------------------------------ #

class VoiceService:
    """Handles audio transcription (Whisper) and speech synthesis (Edge TTS)."""

    def __init__(self) -> None:
        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_BASE,
        )
        self.stt_model = settings.STT_MODEL   # e.g. whisper-1
        self.tts_voice = settings.TTS_VOICE   # e.g. en-IN-PrabhatNeural

    # ---------------------------------------------------------------- #
    #  Speech-to-Text                                                  #
    # ---------------------------------------------------------------- #

    async def speech_to_text(self, audio_file: UploadFile) -> str:
        """
        Uploaded audio file ko Whisper se transcribe karta hai.
        """
        audio_bytes = await audio_file.read()
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Audio file is empty.")

        suffix = Path(audio_file.filename or "audio.webm").suffix or ".webm"
        tmp_path: str | None = None

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name

            with open(tmp_path, "rb") as f:
                transcript = await self.client.audio.transcriptions.create(
                    model=self.stt_model,
                    file=f,
                    response_format="text",
                )

            result = transcript.strip() if isinstance(transcript, str) else transcript.text.strip()
            logger.info("Transcribed %d bytes → %d chars", len(audio_bytes), len(result))
            return result

        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Speech-to-text failed: %s", exc)
            raise HTTPException(status_code=500, detail=f"Speech-to-text failed: {exc}") from exc
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

    # ---------------------------------------------------------------- #
    #  Text-to-Speech                                                  #
    # ---------------------------------------------------------------- #

    async def text_to_speech(self, text: str) -> bytes:
        """
        Text ko English speech mein convert karta hai using Edge TTS.

        Key fix:
            - Pehle saare numbers ko English words mein convert kiya jaata hai
              (num2words library se), taaki TTS engine Hindi mein na bole.
            - SSML mein sirf plain text jaata hai — koi number nahi.

        Args:
            text: Jo text bolna hai.

        Returns:
            Raw MP3 audio bytes.
        """
        if not text or not text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty.")

        try:
            # Step 1: Numbers → English words (e.g. "100" → "one hundred")
            text_no_numbers = replace_numbers_with_words(text)

            # Step 2: SSML special characters escape karo
            escaped = (
                text_no_numbers
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )

            # Step 3: SSML wrap karo (en-IN voice ke saath)
            ssml = (
                f'<speak version="1.0" '
                f'xmlns="http://www.w3.org/2001/10/synthesis" '
                f'xml:lang="en-IN">'
                f'{escaped}'
                f'</speak>'
            )

            # Step 4: Edge TTS se audio generate karo
            communicate = edge_tts.Communicate(ssml, self.tts_voice, rate="+20%")

            audio_data = bytearray()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data.extend(chunk["data"])

            logger.info(
                "Synthesized %d chars → %d bytes audio (Edge TTS)",
                len(text), len(audio_data)
            )
            return bytes(audio_data)

        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Text-to-speech failed: %s", exc)
            raise HTTPException(
                status_code=500,
                detail=f"Text-to-speech failed: {exc}",
            ) from exc


# ------------------------------------------------------------------ #
#  Singleton                                                          #
# ------------------------------------------------------------------ #

voice_service = VoiceService()
