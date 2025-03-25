from gtts import gTTS
from pydub import AudioSegment
from pythonosc import dispatcher, osc_server
from audio2face_streaming_utils import main
import threading
import os
import time
import tempfile

class VoiceResponder:
    def __init__(self, prim_path='/World/audio2face/PlayerStreaming'):
        self.prim_path = prim_path
        self.latest_text = None
        self.playing = False
        self.lock = threading.Lock()
        self.chunk_word_count = 8
        os.makedirs("voices", exist_ok=True)

        threading.Thread(target=self._stream_loop, daemon=True).start()

    def handle_response(self, address, *args):
        if not args:
            print("⚠️ No text received.")
            return
        new_text = " ".join(map(str, args)).strip()
        print(f"📥 OSC Received: {new_text}")
        with self.lock:
            self.latest_text = new_text

    def _generate_tts_chunk(self, text_chunk, index):
        try:
            tts = gTTS(text_chunk)
            temp_mp3 = os.path.join(tempfile.gettempdir(), f"chunk_{index}.mp3")
            temp_wav = f"voices/chunk_{index}.wav"
            tts.save(temp_mp3)
            AudioSegment.from_mp3(temp_mp3).export(temp_wav, format="wav")
            return temp_wav
        except Exception as e:
            print(f"❌ TTS generation failed: {e}")
            return None

    def _split_text_into_chunks(self, text):
        words = text.split()
        return [
            " ".join(words[i:i + self.chunk_word_count])
            for i in range(0, len(words), self.chunk_word_count)
        ]

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
                print(f"\n🔊 Starting speech stream: {text}")
                chunks = self._split_text_into_chunks(text)
                chunk_paths = [None] * len(chunks)

                # Generate first 2 chunks synchronously to prevent delay
                for i in range(min(2, len(chunks))):
                    chunk_paths[i] = self._generate_tts_chunk(chunks[i], i)

                for i, chunk_text in enumerate(chunks):
                    with self.lock:
                        if self.latest_text:
                            print("🛑 New OSC message received — interrupting stream")
                            break

                    # Wait for chunk to exist
                    if not chunk_paths[i] or not os.path.exists(chunk_paths[i]):
                        print(f"⚠️ Chunk {i} not available, skipping...")
                        continue

                    print(f"📤 Streaming chunk {i+1}/{len(chunks)}: {chunk_text}")
                    main(chunk_paths[i], self.prim_path)

                    # Pre-generate next 2 chunks if not already done
                    for j in range(i + 1, i + 3):
                        if j < len(chunks) and chunk_paths[j] is None:
                            def _bg_generate(index, text):
                                path = self._generate_tts_chunk(text, index)
                                chunk_paths[index] = path
                            threading.Thread(target=_bg_generate, args=(j, chunks[j]), daemon=True).start()

                print("✅ Finished streaming.")

            except Exception as e:
                print(f"❌ Error during streaming: {e}")

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
