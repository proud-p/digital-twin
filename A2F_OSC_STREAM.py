from gtts import gTTS
from pydub import AudioSegment
from pydub.utils import make_chunks
from pythonosc import dispatcher, osc_server
from audio2face_streaming_utils import main  # Your unchanged streaming logic
import threading
import os
from queue import Queue, Empty
import time

class VoiceResponder:
    def __init__(self, audio_path='voices/audio.wav', prim_path='/World/audio2face/PlayerStreaming'):
        self.audio_path = audio_path
        self.temp_path = "voices/temp.mp3"
        self.prim_path = prim_path
        self.latest_text = None
        self.playing = False
        self.lock = threading.Lock()
        self.chunk_duration_ms = 5000  # adjust chunk size
        os.makedirs(os.path.dirname(self.audio_path), exist_ok=True)

        # Start a background thread to stream responses
        threading.Thread(target=self._stream_loop, daemon=True).start()

    def handle_response(self, address, *args):
        if not args:
            print("⚠️ No text received.")
            return

        new_text = " ".join(map(str, args)).strip()
        print(f"📥 OSC Received: {new_text}")

        with self.lock:
            self.latest_text = new_text  # Overwrite any ongoing text

    def _stream_loop(self):
        while True:
            if not self.latest_text or self.playing:
                time.sleep(0.1)
                continue

            with self.lock:
                text = self.latest_text
                self.latest_text = None
                self.playing = True

            try:
                print(f"\n🔊 Generating TTS for: {text}")
                tts = gTTS(text)
                tts.save(self.temp_path)
                AudioSegment.from_mp3(self.temp_path).export(self.audio_path, format="wav")
                print("💾 Audio converted to WAV.")

                # Split into chunks
                full_audio = AudioSegment.from_wav(self.audio_path)
                chunks = make_chunks(full_audio, self.chunk_duration_ms)

                for i, chunk in enumerate(chunks):
                    with self.lock:
                        if self.latest_text: #TODO
                            print(f"🛑 Interrupted at chunk {i} — new message received.")
                      

                            chunk_path = f"voices/chunk_{i}.wav"
                            chunk.export(chunk_path, format="wav")
                            print(f"📤 Sending chunk {i+1}/{len(chunks)} → {chunk_path}")
                            main(chunk_path, self.prim_path)
                            
                            break
                        
                        else:
                            chunk_path = f"voices/chunk_{i}.wav"
                            chunk.export(chunk_path, format="wav")
                            print(f"📤 Sending chunk {i+1}/{len(chunks)} → {chunk_path}")
                            main(chunk_path, self.prim_path)
                            
                            


                print("✅ Stream finished.")

            except Exception as e:
                print(f"❌ Error during playback: {e}")

            finally:
                self.playing = False

    def start(self, ip="0.0.0.0", port=1234):
        disp = dispatcher.Dispatcher()
        disp.map("/answer", self.handle_response)

        server = osc_server.BlockingOSCUDPServer((ip, port), disp)
        print(f"🟢 Listening for OSC /answer on {ip}:{port}...")
        server.serve_forever()


if __name__ == "__main__":
    responder = VoiceResponder()
    responder.start(ip="0.0.0.0", port=1234)
