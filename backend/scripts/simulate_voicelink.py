import asyncio
import base64
import json
import logging
import wave
import audioop
import sys
import os
try:
    import websockets
except ImportError:
    print("Installing websockets...")
    os.system(f"{sys.executable} -m pip install websockets gTTS")
    import websockets

import pyttsx3

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

WS_URL = "ws://localhost:8000/ws/voicelink/stream"

def generate_alaw_audio(text: str, lang: str = "hi") -> bytes:
    """Generate TTS audio and convert to 8kHz A-law (VoiceLink format)"""
    logging.info(f"Generating TTS for simulation: '{text}'")
    
    wav_path = "temp_sim.wav"
    
    # Generate WAV natively on Windows using SAPI5
    engine = pyttsx3.init()
    engine.save_to_file(text, wav_path)
    engine.runAndWait()
    
    # Read the generated WAV file
    with wave.open(wav_path, 'rb') as wf:
        pcm_data = wf.readframes(wf.getnframes())
        channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        
        # We need it in 8000Hz mono. If pyttsx3 generated something else (usually 22kHz or 44kHz),
        # we need to resample it. audioop.ratecv can do this.
        if channels == 2:
            pcm_data = audioop.tomono(pcm_data, sampwidth, 1, 1)
        
        if framerate != 8000:
            pcm_data, _ = audioop.ratecv(pcm_data, sampwidth, 1, framerate, 8000, None)
            
        # Convert the resampled PCM to A-law
        alaw_data = audioop.lin2alaw(pcm_data, sampwidth)
        
    # Cleanup
    try:
        os.remove(wav_path)
    except:
        pass
        
    return alaw_data


async def simulate_call(text_to_say: str, language: str = "hi"):
    logging.info(f"Connecting to VoiceLink endpoint at {WS_URL}...")
    
    try:
        alaw_bytes = generate_alaw_audio(text_to_say, language)
    except Exception as e:
        logging.error(f"Failed to generate audio (ffmpeg might be missing): {e}")
        logging.info("Sending raw text bypass to test flow (if supported) or failing.")
        return

    async with websockets.connect(WS_URL) as ws:
        # 1. VoiceLink Connected
        await ws.send(json.dumps({"event": "connected"}))
        logging.info("Sent: connected")
        
        # 2. VoiceLink Start
        await ws.send(json.dumps({
            "event": "start",
            "stream_sid": "sim_stream_123",
            "start": {
                "call_sid": "sim_call_999",
                "from": "+919876543210",
                "custom_parameters": {
                    "customer_id": "kaushal",
                    "language": language
                }
            }
        }))
        logging.info("Sent: start")
        
        # 3. VoiceLink Media (Stream Audio Chunks)
        chunk_size = 8000 # 1 second chunks
        for i in range(0, len(alaw_bytes), chunk_size):
            chunk = alaw_bytes[i:i+chunk_size]
            b64_chunk = base64.b64encode(chunk).decode('utf-8')
            await ws.send(json.dumps({
                "event": "media",
                "media": {
                    "track": "inbound",
                    "payload": b64_chunk
                }
            }))
            await asyncio.sleep(0.5) # simulate streaming time
        
        logging.info("Sent: media (Audio stream finished)")
        
        # 4. VoiceLink Mark (Speech End)
        await ws.send(json.dumps({
            "event": "mark",
            "mark": {"name": "speech_end"}
        }))
        logging.info("Sent: mark (speech_end) - Waiting for AI response...")

        # 5. Listen for AI Response
        while True:
            try:
                response = await ws.recv()
                data = json.loads(response)
                event = data.get("event")
                
                if event == "media":
                    payload = data.get("media", {}).get("payload", "")
                    logging.info(f"Received AI Audio Response Chunk: {len(payload)} bytes (base64)")
                elif event == "mark":
                    mark_name = data.get("mark", {}).get("name")
                    logging.info(f"Received Mark: {mark_name}")
                    if mark_name == "response_done":
                        logging.info("AI finished speaking.")
                        break
            except Exception as e:
                logging.error(f"Error receiving: {e}")
                break

        # 6. Stop
        await ws.send(json.dumps({"event": "stop", "stop": {"callSid": "sim_call_999"}}))
        logging.info("Call ended successfully.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", type=str, default="Mujhe Mumbai mein 1 crore tak ka 2 BHK apartment chahiye.", help="What to say on the call")
    parser.add_argument("--lang", type=str, default="hi", help="Language code (en, hi, pa)")
    args = parser.parse_args()
    
    asyncio.run(simulate_call(args.query, args.lang))
