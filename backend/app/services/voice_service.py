"""
Kaizen AI - Voice Service
===========================
Speech-to-Text (Whisper) and Text-to-Speech (TTS-1-HD)
using the OpenAI Python client directly (not LangChain).
"""

import os
import tempfile
import logging
from pathlib import Path

from openai import AsyncOpenAI
from fastapi import UploadFile, HTTPException

from backend.app.config import settings

logger = logging.getLogger("kaizen.voice_service")


class VoiceService:
    """Handles audio transcription and speech synthesis via OpenAI."""

    def __init__(self) -> None:
        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_BASE,
        )
        self.stt_model = settings.STT_MODEL      # whisper-1
        self.tts_model = settings.TTS_MODEL       # tts-1-hd
        self.tts_voice = settings.TTS_VOICE       # nova

    # ------------------------------------------------------------------ #
    #  Speech-to-Text                                                     #
    # ------------------------------------------------------------------ #

    async def speech_to_text(self, audio_file: UploadFile) -> str:
        """
        Transcribe an uploaded audio file using OpenAI Whisper.

        Supported formats: mp3, mp4, mpeg, mpga, m4a, wav, webm, ogg.

        Args:
            audio_file: The uploaded audio file from the request.

        Returns:
            Transcribed text string.
        """
        # Read the raw audio bytes
        audio_bytes = await audio_file.read()
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Audio file is empty.")

        # Write to a temporary file (Whisper API requires a file-like object)
        suffix = Path(audio_file.filename or "audio.webm").suffix or ".webm"
        tmp_path: str | None = None

        try:
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=suffix
            ) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name

            # Call OpenAI Whisper API
            with open(tmp_path, "rb") as f:
                transcript = await self.client.audio.transcriptions.create(
                    model=self.stt_model,
                    file=f,
                    response_format="text",
                )

            logger.info("Transcribed audio (%d bytes) → %d chars", len(audio_bytes), len(transcript))
            return transcript.strip() if isinstance(transcript, str) else transcript.text.strip()

        except HTTPException:
            raise  # re-raise our own validation errors
        except Exception as exc:
            logger.error("Speech-to-text failed: %s", exc)
            raise HTTPException(
                status_code=500,
                detail=f"Speech-to-text failed: {exc}",
            ) from exc
        finally:
            # Always clean up the temp file
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

    # ------------------------------------------------------------------ #
    #  Text-to-Speech                                                     #
    # ------------------------------------------------------------------ #

    async def text_to_speech(self, text: str) -> bytes:
        """
        Convert text to natural-sounding speech using OpenAI TTS.

        Uses the HD model (tts-1-hd) with the 'nova' voice for
        a warm, human-like output.

        Args:
            text: The text to synthesize.

        Returns:
            Raw MP3 audio bytes.
        """
        if not text or not text.strip():
            raise HTTPException(status_code=400, detail="Text for synthesis cannot be empty.")

        try:
            response = await self.client.audio.speech.create(
                model=self.tts_model,
                voice=self.tts_voice,
                input=text,
                response_format="mp3",
            )

            # Read the binary content from the streaming response
            audio_bytes = response.content
            logger.info("Synthesized %d chars → %d bytes of audio", len(text), len(audio_bytes))
            return audio_bytes

        except Exception as exc:
            logger.error("Text-to-speech failed: %s", exc)
            raise HTTPException(
                status_code=500,
                detail=f"Text-to-speech failed: {exc}",
            ) from exc


# Singleton instance
voice_service = VoiceService()
