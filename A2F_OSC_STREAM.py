from gtts import gTTS
from pydub import AudioSegment
from pythonosc import dispatcher, osc_server
from audio2face_streaming_utils import main  # Omniverse streamer
import threading
import os

class VoiceResponder:
    def __init__(self, audio_path='voices/audio.wav', prim_path='/World/audio2face/PlayerStreaming'):
        self.audio_path = audio_path
        self.temp_path = "voices/temp.mp3"
        self.prim_path = prim_path
        self.stream_thread = None
        self.stop_signal = threading.Event()
        self.lock = threading.Lock()

        os.makedirs(os.path.dirname(self.audio_path), exist_ok=True)

    def handle_response(self, address, *args):
        if not args:
            print("⚠️ No text received.")
            return

        text = " ".join(map(str, args)).strip()
        print(f"\n📥 Received OSC text: {text}")

        # Convert text to TTS
        tts = gTTS(text)
        tts.save(self.temp_path)
        AudioSegment.from_mp3(self.temp_path).export(self.audio_path, format="wav")
        print(f"💾 Saved TTS audio to: {self.audio_path}")

        # Handle streaming — ensure no overlap
        with self.lock:
            if self.stream_thread and self.stream_thread.is_alive():
                print("⏹️ Interrupting previous Omniverse stream...")
                self.stop_signal.set()
                self.stream_thread.join()

            self.stop_signal.clear()
            self.stream_thread = threading.Thread(target=self.stream_to_omniverse, args=(self.audio_path,))
            self.stream_thread.start()

    def stream_to_omniverse(self, path):
        try:
            print("🚀 Starting stream to Omniverse...")
            main(path, self.prim_path)  # This will run until finished
            print("✅ Finished Omniverse stream.")
        except Exception as e:
            print(f"❌ Error streaming to Omniverse: {e}")

    def start(self, ip="0.0.0.0", port=1234):
        disp = dispatcher.Dispatcher()
        disp.map("/answer", self.handle_response)

        server = osc_server.BlockingOSCUDPServer((ip, port), disp)
        print(f"🟢 Listening for OSC /answer on {ip}:{port}...")
        server.serve_forever()


if __name__ == "__main__":
    responder = VoiceResponder()
    ip = "0.0.0.0"  # WSL-safe
    port = 1234
    responder.start(ip, port)
