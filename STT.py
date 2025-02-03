import speech_recognition as sr

def convert_speech_text():
    # Initialize recognizer
    r = sr.Recognizer()

    try:
        # Use microphone as the audio source
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source, duration=0.2)  # Adjust for ambient noise
            print("Listening...")
            audio = r.listen(source)  # Listen for audio input

            # Recognize speech using Google Speech Recognition
            result = r.recognize_google(audio, show_all=True)
            if result:
                # Extract transcript and return it
                text = result["alternative"][0]["transcript"]
                return text

    except sr.RequestError as e:
        print(f"Request error: {e}")
    except sr.UnknownValueError:
        print("Could not understand the audio")
    
    return None  # Return None if speech could not be recognized