from gtts import gTTS
from pythonosc import dispatcher, osc_server
from audio2face_streaming_utils import main  # Your Omniverse streamer
import os
import time

class VoiceResponder:
    def __init__(self, prim_path='/World/audio2face/PlayerStreaming', audio_path='voices/audio.wav'):
        self.prim_path = prim_path
        self.audio_path = audio_path
        self.sleeping = False

        os.makedirs(os.path.dirname(self.audio_path), exist_ok=True)

    def handle_response(self, address, *args):
        if self.sleeping:
            print("⏳ Ignoring message — still sleeping.")
            return
        
        if not args:
            print("⚠️ No text received.")
            return

        text = " ".join(map(str, args)).strip()
        print(f"📥 Received OSC text: {text}")

        # Convert to speech
        tts = gTTS(text)
        tts.save(self.audio_path)
        print(f"🔊 Saved TTS audio to {self.audio_path}")

        # Stream to Omniverse
        main(self.audio_path, self.prim_path)
        print("🚀 Streamed to Omniverse Audio2Face.")

        # Sleep to avoid overlap
        self.sleeping = True
        print("😴 Sleeping for 30s...")
        time.sleep(30)
        self.sleeping = False
        print("✅ Awake and ready again!")

    def start(self, ip="0.0.0.0", port=6006):
        disp = dispatcher.Dispatcher()
        disp.map("/answer", self.handle_response)

        server = osc_server.BlockingOSCUDPServer((ip, port), disp)
        print(f"🟢 Listening for OSC /answer on {ip}:{port}...")
        server.serve_forever()


if __name__ == "__main__":
    #TODO currently if something is being played/sent to omniverse, it blocks everything, make it stream so it's more reactive?
    responder = VoiceResponder()
    ip = "0.0.0.0"  # WSL or local
    port = 1234        # Port you are sending to from WSL
    responder.start(ip, port)
