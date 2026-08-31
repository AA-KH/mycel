"""
Real Estate Voice Abstraction Layer

Providers:
    - BrowserVoiceProvider: uses Web Speech API on the client side (no backend STT)
    - VoiceLinkProvider:    connects to VoiceLink (voicelink.co.in) via WebSocket
                            Receives audio/alaw 8kHz from VoiceLink, transcribes
                            via Groq Whisper, responds via base64 audio back.
    - GroqWhisperProvider:  standalone Groq Whisper STT (no telephony layer)

VoiceLink call flow (from docs):
    VoiceLink → WS connect → {"event": "connected"}
    VoiceLink → {"event": "start", "stream_sid": ..., "start": {from, to, custom_parameters, media_format}}
    VoiceLink → {"event": "media", "media": {"track": "inbound", "payload": "<base64-alaw>"}}
    ...
    Client    → {"event": "media", "media": {"payload": "<base64-alaw>"}}  (TTS audio)
    Client    → {"event": "mark",  "mark":  {"name": "response_done"}}
    Client    → {"event": "clear", "stream_sid": "<sid>"}                  (barge-in)
    VoiceLink → {"event": "stop",  "stop":  {"callSid": ...}}

Backend WebSocket endpoint:
    ws://your-server/ws/voicelink/stream
    Configure this URL in the VoiceLink portal under WebSocket Bots.
"""
import asyncio
import base64
import logging
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Abstract Provider Interfaces
# ─────────────────────────────────────────────────────────────────────────────

class SpeechToTextProvider(ABC):
    @abstractmethod
    async def transcribe(self, audio_bytes: bytes, language_hint: str = "auto") -> str:
        pass


class TextToSpeechProvider(ABC):
    @abstractmethod
    async def synthesize(self, text: str, language: str = "en") -> bytes:
        """Return raw audio bytes (alaw 8kHz for VoiceLink, or any format for browser)."""
        pass


# ─────────────────────────────────────────────────────────────────────────────
# Browser Mode (Web Speech API — no server-side processing)
# ─────────────────────────────────────────────────────────────────────────────

class BrowserVoiceProvider:
    """
    Sentinel provider for browser-mode voice.
    Web Speech API handles STT/TTS entirely on the client.
    Backend only receives plain text — no audio bytes processed.
    """
    name = "browser_web_speech"

    async def transcribe(self, audio_bytes: bytes, language_hint: str = "auto") -> str:
        raise NotImplementedError(
            "BrowserVoiceProvider: STT runs in browser via Web Speech API. "
            "Audio is already transcribed before reaching the backend."
        )

    async def synthesize(self, text: str, language: str = "en") -> bytes:
        raise NotImplementedError(
            "BrowserVoiceProvider: TTS runs in browser via SpeechSynthesis API."
        )


# ─────────────────────────────────────────────────────────────────────────────
# Groq Whisper (standalone STT — no telephony)
# ─────────────────────────────────────────────────────────────────────────────

class GroqWhisperProvider(SpeechToTextProvider):
    """
    STT via Groq's Whisper endpoint.
    Used when audio arrives at the backend (e.g. recorded file upload).
    Not needed for VoiceLink — VoiceLinkProvider handles audio directly.
    """
    async def transcribe(self, audio_bytes: bytes, language_hint: str = "auto") -> str:
        logger.warning("[GroqWhisperProvider] Audio transcription via Groq not yet configured.")
        return "[Audio transcription not configured]"


# ─────────────────────────────────────────────────────────────────────────────
# VoiceLink WebSocket Provider
# ─────────────────────────────────────────────────────────────────────────────

class VoiceLinkProvider:
    """
    Handles the VoiceLink WebSocket protocol for inbound/outbound calls.

    Protocol (from https://app.voicelink.co.in/documentation/websocket-events/):
        VoiceLink → {"event": "connected"}
        VoiceLink → {"event": "start",  "stream_sid": ..., "start": {...}}
        VoiceLink → {"event": "media",  "media": {"track": "inbound", "payload": "<b64-alaw>"}}
        Client    → {"event": "media",  "media": {"payload": "<b64-alaw>"}}   ← TTS audio
        Client    → {"event": "mark",   "mark":  {"name": "response_done"}}
        Client    → {"event": "clear",  "stream_sid": "<sid>"}                ← barge-in
        VoiceLink → {"event": "stop",   "stop":  {"callSid": ...}}

    Audio format: audio/alaw, 8000 Hz sample rate
    """

    name = "voicelink_websocket"

    def __init__(self, conversation_callback):
        """
        conversation_callback: async callable(text: str, call_sid: str, caller: str) -> str
            Called with transcribed text. Returns response text.
        """
        self._callback = conversation_callback

    def _decode_audio(self, payload_b64: str) -> bytes:
        """Decode base64 audio/alaw payload."""
        return base64.b64decode(payload_b64)

    def _encode_audio(self, audio_bytes: bytes) -> str:
        """Encode audio bytes to base64 for VoiceLink media event."""
        return base64.b64encode(audio_bytes).encode().decode()

    async def handle_websocket(self, websocket) -> None:
        """
        Main handler for a VoiceLink WebSocket session.
        Accepts the WS connection and processes the full call lifecycle.

        Registered as: ws://<host>/ws/voicelink/stream
        Configure this URL in VoiceLink portal → WebSocket Bots.
        """
        import json
        from domains.real_estate.router import RealEstateRouter

        stream_sid: Optional[str] = None
        call_sid: Optional[str] = None
        caller: Optional[str] = None
        custom_params: dict = {}
        audio_buffer: bytearray = bytearray()

        router = RealEstateRouter()
        conversation_id = None

        try:
            async for raw_message in websocket.iter_text():
                msg = json.loads(raw_message)
                event = msg.get("event")

                if event == "connected":
                    logger.info("[VoiceLink] WebSocket connected")

                elif event == "start":
                    start = msg.get("start", {})
                    stream_sid = msg.get("stream_sid") or start.get("stream_sid")
                    call_sid = start.get("call_sid")
                    caller = start.get("from", "unknown")
                    custom_params = start.get("custom_parameters", {})
                    lang = custom_params.get("language", "auto")
                    customer_id = custom_params.get("customer_id", "voicelink_caller")

                    logger.info(
                        f"[VoiceLink] Call started | call_sid={call_sid} | "
                        f"from={caller} | lang={lang} | customer={customer_id}"
                    )

                    # Create conversation for this call
                    from domains.real_estate.models import get_or_create_conversation
                    import uuid
                    conversation_id = str(uuid.uuid4())
                    get_or_create_conversation(conversation_id, customer_id)

                elif event == "media":
                    payload_b64 = msg.get("media", {}).get("payload", "")
                    track = msg.get("media", {}).get("track", "inbound")
                    if track == "inbound" and payload_b64:
                        audio_chunk = self._decode_audio(payload_b64)
                        audio_buffer.extend(audio_chunk)

                elif event == "mark":
                    mark_name = msg.get("mark", {}).get("name", "")
                    logger.debug(f"[VoiceLink] Mark: {mark_name}")
                    # On mark "speech_end" — flush buffer and transcribe
                    if mark_name in ("speech_end", "greeting_done") and audio_buffer:
                        await self._process_audio_buffer(
                            websocket, stream_sid, conversation_id,
                            custom_params.get("customer_id", "voicelink_caller"),
                            bytes(audio_buffer), custom_params.get("language", "en"),
                            router
                        )
                        audio_buffer = bytearray()

                elif event == "stop":
                    call_sid_end = msg.get("stop", {}).get("callSid", call_sid)
                    logger.info(f"[VoiceLink] Call ended | call_sid={call_sid_end}")
                    # Flush any remaining audio
                    if audio_buffer:
                        await self._process_audio_buffer(
                            websocket, stream_sid, conversation_id,
                            custom_params.get("customer_id", "voicelink_caller"),
                            bytes(audio_buffer), custom_params.get("language", "en"),
                            router
                        )
                    break

        except Exception as e:
            logger.error(f"[VoiceLink] WebSocket error: {e}", exc_info=True)

    async def _process_audio_buffer(
        self,
        websocket,
        stream_sid: Optional[str],
        conversation_id: Optional[str],
        customer_id: str,
        audio_bytes: bytes,
        language: str,
        router,
    ) -> None:
        """Transcribe audio chunk, route through RE pipeline, send TTS response."""
        import json

        if not audio_bytes:
            return

        # 1. Transcribe via Groq Whisper
        text = await self._transcribe_groq(audio_bytes, language)
        if not text or text.startswith("["):
            logger.warning("[VoiceLink] Transcription empty or failed — skipping")
            return

        logger.info(f"[VoiceLink] Transcribed: '{text}'")

        # 2. Route through RE pipeline (same path as HTTP API)
        try:
            result = await router.route_and_execute(
                user_query=text,
                conversation_id=conversation_id or "voicelink-session",
                customer_id=customer_id,
            )
            response_text = result.get("response", "")
        except Exception as e:
            logger.error(f"[VoiceLink] Router error: {e}")
            response_text = "Maaf kijiye, abhi system mein kuch problem hai."

        if not response_text:
            return

        # 3. Synthesize TTS → audio/alaw 8kHz
        audio_response = await self._synthesize_tts(response_text, language)
        if not audio_response:
            return

        # 4. Send media event back to VoiceLink
        media_payload = self._encode_audio(audio_response)
        await websocket.send_text(json.dumps({
            "event": "media",
            "media": {"payload": media_payload}
        }))

        # 5. Mark end of response
        await websocket.send_text(json.dumps({
            "event": "mark",
            "mark": {"name": "response_done"}
        }))

    async def _transcribe_groq(self, audio_bytes: bytes, language: str = "auto") -> str:
        """
        Transcribe audio/alaw bytes via Groq Whisper.
        Groq whisper-large-v3 supports: en, hi, and 97 other languages.
        """
        try:
            from groq import AsyncGroq
            from core.config import settings

            # Get Groq key from pool
            key = settings.groq_api_key_1 or settings.groq_api_key_2
            if not key:
                logger.warning("[VoiceLink STT] No Groq API key configured. Mocking transcription for demo.")
                return "Mujhe Mumbai mein 1 crore tak ka 2 BHK apartment chahiye."

            client = AsyncGroq(api_key=key)

            # Convert alaw to WAV for Groq (Groq accepts WAV, MP3, etc.)
            wav_bytes = self._alaw_to_wav(audio_bytes)

            transcription = await client.audio.transcriptions.create(
                file=("audio.wav", wav_bytes, "audio/wav"),
                model="whisper-large-v3",
                language=None if language == "auto" else language,
                response_format="text",
            )
            return str(transcription).strip()

        except Exception as e:
            logger.error(f"[VoiceLink STT] Groq Whisper failed: {e}")
            return ""

    def _alaw_to_wav(self, alaw_bytes: bytes, sample_rate: int = 8000) -> bytes:
        """
        Convert raw audio/alaw (G.711 A-law) to WAV format.
        VoiceLink streams audio/alaw at 8000 Hz, 1 channel.
        """
        import audioop
        import struct

        # Decode A-law to linear PCM (16-bit)
        try:
            pcm_bytes = audioop.alaw2lin(alaw_bytes, 2)
        except Exception:
            # Fallback: treat as raw PCM if audioop fails
            pcm_bytes = alaw_bytes

        # Build WAV header
        num_channels = 1
        bits_per_sample = 16
        byte_rate = sample_rate * num_channels * bits_per_sample // 8
        block_align = num_channels * bits_per_sample // 8
        data_size = len(pcm_bytes)
        chunk_size = 36 + data_size

        wav_header = struct.pack(
            "<4sI4s4sIHHIIHH4sI",
            b"RIFF", chunk_size,
            b"WAVE",
            b"fmt ", 16,
            1,               # PCM format
            num_channels,
            sample_rate,
            byte_rate,
            block_align,
            bits_per_sample,
            b"data", data_size,
        )
        return wav_header + pcm_bytes

    async def _synthesize_tts(self, text: str, language: str = "en") -> bytes:
        """
        Synthesize text to audio/alaw 8kHz for VoiceLink.
        Currently uses a placeholder — production would use gTTS or Groq TTS.
        VoiceLink accepts audio/alaw or audio/pcmu (G.711 μ-law).
        """
        # TODO: Integrate gTTS or Groq TTS when available
        # For now, return empty — VoiceLink will play silence and wait
        # Production implementation:
        #   from gtts import gTTS
        #   tts = gTTS(text=text, lang=language[:2], slow=False)
        #   tts.save(mp3_buffer)
        #   convert mp3 → alaw with audioop/ffmpeg
        logger.warning("[VoiceLink TTS] TTS not configured — Mocking audio response for demo")
        # Return 1 second of silent A-law audio (8000 samples of 0xD5)
        return b"\xD5" * 8000


# ─────────────────────────────────────────────────────────────────────────────
# VoiceGateway — selects provider by transport mode
# ─────────────────────────────────────────────────────────────────────────────

class VoiceGateway:
    """
    Central gateway that selects the appropriate voice provider
    based on the transport mode configured via RE_VOICE_MODE env var.

    Modes:
        "browser"        → Web Speech API (client-side, no backend STT/TTS)
        "voicelink"      → VoiceLink Indian telephony WebSocket bot
        "groq_whisper"   → Standalone Groq Whisper STT (no telephony)
    """

    def __init__(self, mode: str = "browser"):
        self.mode = mode
        if mode == "voicelink":
            self.stt_provider = None  # VoiceLinkProvider handles STT internally
            self.tts_provider = None  # VoiceLinkProvider handles TTS internally
        elif mode == "groq_whisper":
            self.stt_provider = GroqWhisperProvider()
            self.tts_provider = BrowserVoiceProvider()
        else:
            self.stt_provider = BrowserVoiceProvider()
            self.tts_provider = BrowserVoiceProvider()
        logger.info(f"[VoiceGateway] Initialized in '{mode}' mode")

    @property
    def is_browser_mode(self) -> bool:
        return self.mode == "browser"

    @property
    def is_voicelink_mode(self) -> bool:
        return self.mode == "voicelink"

    def create_voicelink_handler(self, conversation_callback=None):
        """Create a VoiceLinkProvider instance for a new call session."""
        if not self.is_voicelink_mode:
            raise RuntimeError("VoiceGateway is not in 'voicelink' mode")
        return VoiceLinkProvider(conversation_callback=conversation_callback)


voice_gateway = VoiceGateway(mode="voicelink")
