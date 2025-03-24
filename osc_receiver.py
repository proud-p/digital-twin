# test getting gpt response messages osc from wsl

from gtts import gTTS
from pythonosc import dispatcher, osc_server
import os
import playsound
from time import sleep

class VoiceResponder:
    def __init__(self, audio_path='voices/audio.wav'):
        self.audio_path = audio_path
        os.makedirs(os.path.dirname(self.audio_path), exist_ok=True)

    def handle_response(self, address, *args):
        if not args:
            print("⚠️ No text received.")
            return

        text = " ".join(map(str, args)).strip()
        print(f"📥 Received OSC text: {text}")

        # Convert to speech
        tts = gTTS(text)
        tts.save(self.audio_path)
        sleep(30)
        print(f"🔊 Saved TTS audio to {self.audio_path}, sleeping for 30s")

        # Play the audio
        playsound.playsound(self.audio_path)
        print("✅ Finished playing audio.")

    def start(self, ip="0.0.0.0", port=6006):
        disp = dispatcher.Dispatcher()
        disp.map("/answer", self.handle_response)

        server = osc_server.BlockingOSCUDPServer((ip, port), disp)
        print(f"🟢 Listening for OSC /answer on {ip}:{port}...")
        server.serve_forever()


if __name__ == "__main__":
    responder = VoiceResponder()
    ip = "192.168.0.2"       
    port = 1234
    responder.start(ip,port)

