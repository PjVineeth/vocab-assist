# Mapping TTS engine names to their API URLs
TTS_API_URLS = {
    "google": "http://27.111.72.61:9001/google_tts",
    "dia": "http://27.111.72.61:4000/tts_dia",
    "indictts": "http://27.111.72.61:3000/indictts"
}

def synthesize_and_play_audio(text, tts_engine="google"):
    """
    Send text to the specified TTS engine API, get encoded audio, decode, and play it.

    Parameters:
    - text: The text to convert into speech
    - tts_engine: The TTS engine to use ('google', 'dia', 'indictts')
    """
    api_url = TTS_API_URLS.get(tts_engine)
    if not api_url:
        print(f"Invalid TTS engine: {tts_engine}. Choose from {list(TTS_API_URLS.keys())}")
        return
    try:
        response = requests.post(
            api_url,
            json={"text": text},
            headers={"Content-Type": "application/json"}
        )
        if response.status_code != 200:
            print(f"Error: Unable to generate audio. Status code {response.status_code}")
            print(response.json())
            return

        audio_base64 = response.json().get("audio")
        if not audio_base64:
            print("Error: No audio data in the response.")
            return

        audio_data = base64.b64decode(audio_base64)
        pygame.mixer.init(frequency=22050)
        sound = pygame.mixer.Sound(BytesIO(audio_data))

        print("Playing audio...")
        sound.play()
        pygame.time.wait(int(sound.get_length() * 1000))

    except Exception as e:
        print(f"An error occurred: {e}")
