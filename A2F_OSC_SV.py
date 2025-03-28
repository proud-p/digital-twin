from gtts import gTTS
from pydub import AudioSegment
from pythonosc import dispatcher, osc_server, udp_client
from audio2face_streaming_utils import main
import threading
import os
import time
import tempfile
import speech_recognition as sr
import subprocess

class VoiceResponder:
    def __init__(self, prim_path='/World/audio2face/PlayerStreaming', wsl_ip="172.30.40.252", wsl_port=5009):
        self.prim_path = prim_path
        self.latest_text = None
        self.playing = False
        self.x = 1.0
        self.y = 1.0
        self.lock = threading.Lock()
        self.chunk_word_count = 8
        self.intro_done = False

        self.wsl_client = udp_client.SimpleUDPClient(wsl_ip, wsl_port)
        self.unreal_client = udp_client.SimpleUDPClient("127.0.0.1", 4444)

        os.makedirs("voices", exist_ok=True)

        threading.Thread(target=self._run_intro_and_listen, daemon=True).start()
        threading.Thread(target=self._stream_loop, daemon=True).start()

    def handle_response(self, address, *args):
        if not args:
            print("⚠️ No text received.")
            return
        new_text = " ".join(map(str, args)).strip()
        print(f"📥 OSC Received ({address}): {new_text}")
        with self.lock:
            if address == "/answer":
                self.latest_text = new_text
            elif address == "/x":
                self.x = round(float(args[0]), 1)
            elif address == "/y":
                self.y = round(float(args[0]), 1)

    def _generate_intro_line(self, message="Ask, and you shall be answered..."):
        try:
            temp_mp3 = os.path.join(tempfile.gettempdir(), "intro.mp3")
            temp_wav = "voices/intro.wav"
            cmd = f'edge-tts --voice "en-GB-RyanNeural" --text "{message}" --write-media "{temp_mp3}"'
            subprocess.run(cmd, shell=True, check=True)
            AudioSegment.from_mp3(temp_mp3).export(temp_wav, format="wav")
            print("🎙️ Streaming intro line...")
            main(temp_wav, self.prim_path)
        except Exception as e:
            print(f"❌ Failed to stream intro line: {e}")

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
        return [" ".join(words[i:i + self.chunk_word_count]) for i in range(0, len(words), self.chunk_word_count)]

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
                for i in range(min(2, len(chunks))):
                    chunk_paths[i] = self._generate_tts_chunk(chunks[i], i)
                for i, chunk_text in enumerate(chunks):
                    with self.lock:
                        if self.latest_text:
                            print("🛑 New OSC message received — interrupting stream")
                            break
                    if not chunk_paths[i] or not os.path.exists(chunk_paths[i]):
                        print(f"⚠️ Chunk {i} not available, skipping...")
                        continue
                    print(f"📤 Streaming chunk {i+1}/{len(chunks)}: {chunk_text}")
                    self.unreal_client.send_message("/trigger", chunk_text)
                    main(chunk_paths[i], self.prim_path)
                    for j in range(i + 1, i + 3):
                        if j < len(chunks) and chunk_paths[j] is None:
                            def _bg_generate(index, text):
                                chunk_paths[index] = self._generate_tts_chunk(text, index)
                            threading.Thread(target=_bg_generate, args=(j, chunks[j]), daemon=True).start()
                print("✅ Finished streaming.")
            except Exception as e:
                print(f"❌ Error during streaming: {e}")
            finally:
                self.playing = False

    def _run_intro_and_listen(self):
        recognizer = sr.Recognizer()
        mic = sr.Microphone()

        # Run intro at startup
        self.unreal_client.send_message("/trigger", "Ask, and you shall be answered....")
        self._generate_intro_line()
        self.intro_done = True

        while True:
            time.sleep(0.2)
            with self.lock:
                if not (self.x == 0.0 and self.y == 0.0 and not self.playing):
                    continue
            try:
                print("🎤 Ready for voice input...")
                with mic as source:
                    recognizer.adjust_for_ambient_noise(source, duration=0.3)
                    audio = recognizer.listen(source, timeout=5)
                    result = recognizer.recognize_google(audio, show_all=True)
                if result:
                    text = result["alternative"][0]["transcript"]
                    print(f"🗣️ Voice Detected: {text}")
                    with self.lock:
                        self.latest_text = text
                    print(f"🗣️ Voice Detected: {text}")
                    self.wsl_client.send_message("/voice_prompt", text)
            except sr.WaitTimeoutError:
                print("🕐 No voice input detected.")
            except sr.UnknownValueError:
                print("❓ Could not understand audio.")
            except sr.RequestError as e:
                print(f"⚠️ Speech recognition error: {e}")

    def start(self, ip="0.0.0.0", port=1234):
        disp = dispatcher.Dispatcher()
        disp.map("/answer", self.handle_response)
        disp.map("/x", self.handle_response)
        disp.map("/y", self.handle_response)
        server = osc_server.BlockingOSCUDPServer((ip, port), disp)
        print(f"🟢 Listening for OSC on {ip}:{port} (addresses: /answer /x /y)")
        server.serve_forever()

responder = VoiceResponder()
responder.start(ip="0.0.0.0", port=1234)
