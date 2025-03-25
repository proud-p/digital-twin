from gtts import gTTS
from pydub import AudioSegment
from pydub.utils import make_chunks
from pythonosc import dispatcher, osc_server
from audio2face_streaming_utils import main  # This is your custom function to stream to Omniverse
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

        # Convert text to TTS (mp3 → wav)
        tts = gTTS(text)
        tts.save(self.temp_path)
        AudioSegment.from_mp3(self.temp_path).export(self.audio_path, format="wav")
        print(f"💾 Saved TTS audio to: {self.audio_path}")

        # Handle streaming with interruption between chunks
        with self.lock:
            if self.stream_thread and self.stream_thread.is_alive():
                print("⏹️ Interrupting previous Omniverse stream...")
                self.stop_signal.set()
                self.stream_thread.join()

            self.stop_signal.clear()
            self.stream_thread = threading.Thread(target=self.stream_to_omniverse_in_chunks, args=(self.audio_path,))
            self.stream_thread.start()

    def stream_to_omniverse_in_chunks(self, path):
        try:
            print("🚀 Starting chunked stream to Omniverse...")
            audio = AudioSegment.from_wav(path)
            chunks = make_chunks(audio, 500)  # 500ms chunks

            for i, chunk in enumerate(chunks):
                if self.stop_signal.is_set():
                    print(f"🛑 Stopped before chunk {i}")
                    break

                chunk_path = f"voices/chunk_{i}.wav"
                chunk.export(chunk_path, format="wav")
                main(chunk_path, self.prim_path)
                print(f"📤 Sent chunk {i+1}/{len(chunks)}")

            print("✅ Finished Omniverse stream.")
        except Exception as e:
            print(f"❌ Error during chunked streaming: {e}")

    def start(self, ip="0.0.0.0", port=1234):
        disp = dispatcher.Dispatcher()
        disp.map("/answer", self.handle_response)

        server = osc_server.BlockingOSCUDPServer((ip, port), disp)
        print(f"🟢 Listening for OSC /answer on {ip}:{port}...")
        server.serve_forever()


if __name__ == "__main__":
    responder = VoiceResponder()
    ip = "0.0.0.0"
    port = 1234
    responder.start(ip, port)
