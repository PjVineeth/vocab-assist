import os
import requests
import mimetypes
import base64
import pygame
from io import BytesIO
def query_cred_chat_api(text: str, api_url: str = "http://27.111.72.61:5353/chat") -> str:
    """
    Sends the input text to the CRED chat API and returns the assistant's response.

    Parameters:
    - text (str): User input text.
    - api_url (str): Endpoint URL of the Flask chat API.

    Returns:
    - str: Response from the assistant or error message.
    """
    try:
        response = requests.post(api_url, json={"text": text})
        response.raise_for_status()
        data = response.json()

        if "response" in data:
            return data["response"]
        elif "error" in data:
            return f"API Error: {data['error']}"
        else:
            return "Unexpected API response format."
    except requests.exceptions.RequestException as e:
        return f"Request failed: {e}"

def send_audio_to_server_new(file_path, api_url="http://27.111.72.61:10003/upload_file"):
    """
    Sends an existing WAV audio file to the server for processing and returns the concatenated transcription.

    Args:
        file_path (str): Path to the WAV audio file to send.
        api_url (str): The server API endpoint.

    Returns:
        str: Concatenated transcription text, or None if an error occurs.
    """
    if not os.path.exists(file_path):
        print(f"[ERROR] File not found: {file_path}")
        return None

    try:
        # Guess MIME type
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = 'application/octet-stream'

        with open(file_path, 'rb') as f:
            files = {
                'audio_file': (os.path.basename(file_path), f, mime_type)
            }
            print(f"[INFO] Sending file '{file_path}' with MIME type '{mime_type}' to {api_url}...")
            response = requests.post(api_url, files=files)

        if response.status_code == 200:
            print("[INFO] Server response received successfully.")
            result = response.json()
            print("[INFO] Raw response:", result)

            # Extract and concatenate transcriptions
            transcriptions = result.get('transcriptions', [])
            if not transcriptions:
                print("[WARN] No transcriptions found in response.")
                return None

            concatenated_text = transcriptions
            print(f"[INFO] Concatenated Transcription: {concatenated_text}")
            return concatenated_text
        else:
            print(f"[ERROR] Server returned status {response.status_code}: {response.text}")
            return None

    except Exception as e:
        print(f"[ERROR] Exception during file sending or processing: {e}")
        return None

        

def synthesize_and_play_audio(text, api_url="http://27.111.72.61:9001/tts"):
    """
    Send the text to the API, get the encoded audio, decode it, and play it.
    
    Parameters:
    - text: The text to convert into speech
    - api_url: The API URL to send the request to (default is local Flask API)
    """
    try:
        # Step 1: Send a POST request to the API
        response = requests.post(
            api_url,
            json={"text": text},
            headers={"Content-Type": "application/json"}
        )
        
        # Check if the request was successful
        if response.status_code != 200:
            print(f"Error: Unable to generate audio. Status code {response.status_code}")
            print(response.json())
            return
        
        # Step 2: Get the base64-encoded audio from the API response
        audio_base64 = response.json().get("audio")
        if not audio_base64:
            print("Error: No audio data in the response.")
            return
        
        # Step 3: Decode the base64 audio
        audio_data = base64.b64decode(audio_base64)
        
        # Step 4: Convert the byte data to a playable sound using pygame
        pygame.mixer.init(frequency=22050)  # Ensure the frequency matches the output sample rate
        sound = pygame.mixer.Sound(BytesIO(audio_data))

        # Step 5: Play the audio
        print("Playing audio...")
        sound.play()
        pygame.time.wait(int(sound.get_length() * 1000))  # Wait for the sound to finish playing
    
    except Exception as e:
        print(f"An error occurred: {e}")