import os
from elevenlabs.client import ElevenLabs
from pythonosc import udp_client
from elevenlabs import play, save


def get_speech(answer):
    client = ElevenLabs(
        api_key=os.environ.get("ELEVENLABS_KEY"),
    )
    #elevenlabs.set_api_key(os.environ.get("ELEVENLABS_KEY"))
    audio = client.generate(
        text=answer,
        # need a voice id
        voice="9BWtsMINqrJLrRacOk9x",
        model="eleven_multilingual_v2",
    )
    #play(audio)
    file_path = os.path.join("voices/", "audio.wav")
    save(audio, file_path)