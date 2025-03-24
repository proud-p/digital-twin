from gtts import gTTS
from pythonosc import dispatcher, osc_server
from audio2face_streaming_utils import main  # Assumed to stream audio to Omniverse
import os

class VoiceResponder:
    def __init__(self, prim_path='/World/audio2face/PlayerStreaming'):
        self.prim_path = prim_path

    def handle_response(self, *args):
        # Join args if it's a multi-part OSC string
        if not args:
            print("No response text received.")
            return

        text = " ".join(map(str, args)).strip()
        print(f"📥 Received OSC text: {text}")

        # Convert to speech
        tts = gTTS(text)
        tts.save("voices/audio.wav")
        print("🔊 Saved TTS audio.")

        # Stream audio to Omniverse
        main("voices/audio.wav", self.prim_path)
        print("🚀 Streamed to Audio2Face.")

    def start(self, ip="0.0.0.0", port=6006):
        disp = dispatcher.Dispatcher()
        # address == "answer"
        disp.map("/answer", self.handle_response)
        server = osc_server.BlockingOSCUDPServer((ip, port), disp)
        print(f"🟢 Listening for OSC responses on {ip}:{port}...")
        server.serve_forever()


if __name__ == "__main__":
    os.makedirs("voices", exist_ok=True)
    responder = VoiceResponder()
    ip = "192.168.0.2"        
    port = 5009
    responder.start(ip,port)
