from gtts import gTTS
from pydub import AudioSegment
import simpleaudio as sa
from pythonosc import dispatcher, osc_server
import os
import threading

class VoiceResponder:
    def __init__(self, audio_path='voices/audio.wav'):
        self.audio_path = audio_path
        self.temp_path = "voices/temp.mp3"
        self.playback_thread = None
        self.lock = threading.Lock()

        os.makedirs(os.path.dirname(self.audio_path), exist_ok=True)

    def handle_response(self, address, *args):
        if not args:
            print("⚠️ No text received.")
            return

        text = " ".join(map(str, args)).strip()
        print(f"\n📥 Received OSC text: {text}")

        # Convert to speech (mp3 → wav)
        tts = gTTS(text)
        tts.save(self.temp_path)
        AudioSegment.from_mp3(self.temp_path).export(self.audio_path, format="wav")
        print(f"💾 Converted and saved WAV to: {self.audio_path}")

        # Play latest audio in a separate thread
        with self.lock:
            if self.playback_thread and self.playback_thread.is_alive():
                print("⏹️ Stopping current playback...")
                # NOTE: simpleaudio has no stop method, so we wait for current to finish
                # If you want instant interrupts, switch to pyaudio or pygame

            self.playback_thread = threading.Thread(target=self.play_audio)
            self.playback_thread.start()

    def play_audio(self):
        try:
            wave_obj = sa.WaveObject.from_wave_file(self.audio_path)
            play_obj = wave_obj.play()
            play_obj.wait_done()
            print("✅ Finished playback.")
        except Exception as e:
            print(f"❌ Error during playback: {e}")

    def start(self, ip="0.0.0.0", port=1234):
        disp = dispatcher.Dispatcher()
        disp.map("/answer", self.handle_response)

        server = osc_server.BlockingOSCUDPServer((ip, port), disp)
        print(f"🟢 Listening for OSC /answer on {ip}:{port}...")
        server.serve_forever()


if __name__ == "__main__":
    responder = VoiceResponder()
    ip = "0.0.0.0"  # Listen on all interfaces (WSL-safe)
    port = 1234
    responder.start(ip, port)
