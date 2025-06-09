try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    print("Warning: speech_recognition not available - microphone features disabled")

import time
import os
from gtts import gTTS
import pygame
import google.generativeai as genai
from dotenv import load_dotenv
import faiss
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import numpy as np
import requests
import mimetypes
import base64
import pygame
import tempfile

from io import BytesIO
# Load API Key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("ERROR: GEMINI_API_KEY environment variable not found!")
    print("Please set GEMINI_API_KEY in your environment variables.")
    # You can uncomment the line below to see what env vars are available
    # print("Available env vars:", list(os.environ.keys()))

# Configure Gemini
genai.configure(api_key=api_key)

# Initialize pygame for audio playback
pygame.mixer.init()

def listen_for_speech(timeout=3):
    """Continuously listens for speech and returns transcription when silence is detected."""
    if not SPEECH_RECOGNITION_AVAILABLE:
        print("Speech recognition not available - microphone disabled in deployment")
        return None, None
    
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()

    with microphone as source:
        print("Adjusting for ambient noise...")
        recognizer.adjust_for_ambient_noise(source)
        print("Listening...")

        while True:
            try:
                # Listen to the audio
                audio = recognizer.listen(source, phrase_time_limit=None, timeout=None)
                print("Processing speech...")

                # Convert speech to text (Try English first)
                text = recognizer.recognize_google(audio, language="en-US")
                print(f"Recognized (English): {text}")
                return text, 'en'
            
            except sr.UnknownValueError:
                # If English recognition fails, try Hindi
                try:
                    text = recognizer.recognize_google(audio, language="hi-IN")
                    print(f"Recognized (Hindi): {text}")
                    return text, 'hi'
                except sr.UnknownValueError:
                    print("Could not understand speech.")
                    return None, None


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



def send_audio_to_server(api_url="http://27.111.72.61:10003/upload"):
    """Records audio and sends it to server for processing."""
    if not SPEECH_RECOGNITION_AVAILABLE:
        print("Speech recognition not available - microphone disabled in deployment")
        return None

    recognizer = sr.Recognizer()
    microphone = sr.Microphone()

    with microphone as source:
        print("Adjusting for ambient noise...")
        recognizer.adjust_for_ambient_noise(source)
        print("Recording audio...")

        try:
            # Record audio from the microphone
            audio = recognizer.listen(source, phrase_time_limit=None, timeout=None)
            print("Recording complete.")

            # Create a temporary path manually
            temp_dir = tempfile.gettempdir()
            temp_audio_path = os.path.join(temp_dir, "temp_audio.wav")

            # Write WAV data to that path
            with open(temp_audio_path, "wb") as f:
                f.write(audio.get_wav_data())

            # Now send the file
            with open(temp_audio_path, 'rb') as f:
                files = {'file': f}
                print(f"Sending {temp_audio_path} to server...")
                response = requests.post(api_url, files=files)

            # Clean up temp file
            os.remove(temp_audio_path)

            # Check server response
            if response.status_code == 200:
                print("Server response received successfully.")
                result = response.json()
                # Concatenate all 'transcription' values
                concatenated_text = ' '.join(item['transcription'] for item in result if 'transcription' in item)
                print(f"Concatenated Transcription: {concatenated_text}")
                return concatenated_text 
            else:
                print(f"Error from server: {response.status_code} {response.text}")
                return None

        except Exception as e:
            print(f"Error during listening or processing: {e}")
            return None
        


def retrieve_relevant_chunks(query, faiss_index, text_chunks, top_k=5):
    """Retrieve the most relevant text chunks for a given query."""
    try:
        query_embedding = genai.embed_content(
            model="models/embedding-001", content=query, task_type="retrieval_query"
        )["embedding"]

        query_embedding_np = np.array(query_embedding, dtype=np.float32).reshape(1, -1)

        distances, indices = faiss_index.search(query_embedding_np, top_k)

        relevant_chunks = [
            text_chunks[i].page_content for i in indices[0] if i < len(text_chunks)
        ]
        return relevant_chunks
    except Exception as e:
        print(f"Error during retrieval: {e}")
        return []

# You can configure the LLM in app.py and pass it here
def load_and_chunk_pdf(pdf_path):
    """Load PDF and split into text chunks."""
    try:
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200
        )
        return text_splitter.split_documents(documents)
    except Exception as e:
        print(f"Error loading PDF: {e}")
        return []

def get_embeddings(texts):
    """Generate embeddings for text chunks."""
    embeddings = []
    for doc in texts:
        try:
            response = genai.embed_content(
                model="models/embedding-001",
                content=doc.page_content,
                task_type="retrieval_document",
            )
            if response and "embedding" in response:
                embeddings.append(response["embedding"])
        except Exception as e:
            print(f"Error generating embedding for text chunk: {e}")
            continue
    return embeddings


def initialize_faiss(pdf_file_path):
    """Initialize FAISS index with document embeddings."""
    text_chunks = load_and_chunk_pdf(pdf_file_path)

    if not text_chunks:
        print("Warning: No text chunks found. Check the PDF file.")
        return None, None

    embeddings = get_embeddings(text_chunks)
    if not embeddings:
        print("Error: No embeddings generated. Check the document content.")
        return None, None

    embeddings_np = np.array(embeddings, dtype=np.float32)
    faiss_index = faiss.IndexFlatL2(embeddings_np.shape[1])
    faiss_index.add(embeddings_np)
    print(f"FAISS index initialized successfully for {pdf_file_path}!")
    return faiss_index, text_chunks


def generate_response(
    query, guidelines_index, guidelines_chunks, llm, conversation_history, top_k=5
):
    """Generate a response to the user query using the guidelines and example PDFs."""
    relevant_guidelines = retrieve_relevant_chunks(
        query, guidelines_index, guidelines_chunks, top_k
    )

    if not relevant_guidelines:
        return "Sorry, I couldn't find any relevant information in the guidelines."

    guidelines_context = "\n\n".join(relevant_guidelines)

    is_first_interaction = len(conversation_history) <= 1

    history = "\n".join(
        [
            f"User: {entry['user']}\nAgent: {entry['agent']}"
            for entry in conversation_history
        ]
    )

    try:
        input_text = f"""
            You are a customer care agent for CRED-Help responding directly to a customer.
            The customer has come to you specifically for an issue related to CRED and not just a normal query. 
            Use these guidelines to inform your response:
            {guidelines_context}

            User's query: {query}

            Previous conversation history:
            {history}

            {"" if is_first_interaction else "IMPORTANT: DO NOT use greetings like Good Morning/Afternoon/Evening again as you've already greeted the customer."}

            IMPORTANT INSTRUCTIONS:
            1. Respond DIRECTLY to the user as if in a conversation
            2. DO NOT include meta-commentary like "Here's my response" or "Following the guidelines" 
            3. DO NOT narrate your actions or thought process
            4. Keep responses helpful and concise
            5. Follow the guidelines provided
            6. Do not repeat information from previous messages
            """

        response = llm.invoke(input=input_text)

        agent_response = response.content

        conversation_history.append({"user": query, "agent": agent_response})
        return agent_response
    except Exception as e:
        print(f"Error generating response: {e}")
        return "Sorry, there was an error generating a response."

    
def generate_response_with_gemini(text, max_tokens=200): 
    """Generate a response using Google's Gemini API."""
    prompt = (
        "You are having a natural speech conversation with a user. Your responses should be clear, concise, and to the point. "
        "Adjust response length with in 50 words"
        f"User: {text}\n"
        "AI:"
    )

    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt, generation_config={
            "max_output_tokens": max_tokens,
            "temperature": 0.7,
            "top_p": 0.9
        })

        # Ensure response is correctly extracted
        if hasattr(response, "text") and response.text.strip():
            return response.text.strip()
        else:
            return "Sorry, I couldn't generate a response."
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return "Sorry, there was an issue generating a response."


def text_to_speech(text, lang):
    """Convert text to speech and play it."""
    temp_file = "response.mp3"
    tts = gTTS(text=text, lang=lang, slow=False)
    tts.save(temp_file)

    # Play the generated speech
    pygame.mixer.music.load(temp_file)
    pygame.mixer.music.play()

    # Wait for audio to finish playing
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

    # Clean up
    pygame.mixer.music.unload()
    os.remove(temp_file)

def synthesize_and_play_audio(text, api_url="http://27.111.72.61:8001/dia"):
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