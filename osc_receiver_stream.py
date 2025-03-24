from gtts import gTTS
from pydub import AudioSegment
from pydub.utils import make_chunks
import pyaudio
import wave
from pythonosc import dispatcher, osc_server
import threading
import os
import numpy as np

class VoiceResponder:
    def __init__(self, audio_path='voices/audio.wav'):
        self.audio_path = audio_path
        self.temp_path = "voices/temp.mp3"
        self.playback_thread = None
        self.stop_playback = threading.Event()
        self.lock = threading.Lock()
        os.makedirs(os.path.dirname(self.audio_path), exist_ok=True)

    def handle_response(self, address, *args):
        if not args:
            print("⚠️ No text received.")
            return

        text = " ".join(map(str, args)).strip()
        print(f"\n📥 Received OSC text: {text}")

        # Convert to mp3, then to wav
        tts = gTTS(text)
        tts.save(self.temp_path)
        AudioSegment.from_mp3(self.temp_path).export(self.audio_path, format="wav")
        print(f"💾 Saved TTS audio to: {self.audio_path}")

        with self.lock:
            # Signal current playback thread to stop (if running)
            if self.playback_thread and self.playback_thread.is_alive():
                print("⏹️ Interrupting previous playback...")
                self.stop_playback.set()
                self.playback_thread.join()

            # Start new playback thread
            self.stop_playback.clear()
            self.playback_thread = threading.Thread(target=self.play_audio)
            self.playback_thread.start()

    def play_audio(self):
        try:
            wf = wave.open(self.audio_path, 'rb')
            p = pyaudio.PyAudio()

            stream = p.open(
                format=p.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True
            )

            chunk = 1024
            data = wf.readframes(chunk)

            while data and not self.stop_playback.is_set():
                stream.write(data)
                data = wf.readframes(chunk)

            stream.stop_stream()
            stream.close()
            p.terminate()
            wf.close()

            print("✅ Done speaking." if not self.stop_playback.is_set() else "🛑 Playback interrupted.")
        except Exception as e:
            print(f"❌ Error playing audio: {e}")

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
