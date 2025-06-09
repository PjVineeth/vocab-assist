from flask import Flask, jsonify, render_template, request
import time
import threading
from processing import *
from werkzeug.utils import secure_filename
from langchain_google_genai import ChatGoogleGenerativeAI
from flask_cors import CORS
import traceback
import time
import base64


app = Flask(__name__)
CORS(app)  # This enables CORS for all routes
 # Get the current directory where the Python script is running
script_dir = os.path.dirname(os.path.abspath(__file__))
 # Target path: uploads/files/recorded.wav relative to the script location
save_dir = os.path.join(script_dir, 'uploads')
os.makedirs(save_dir, exist_ok=True)
# Set your API key securely
GOOGLE_API_KEY = "AIzaSyDdlpRoOhsmj8KPWiX5krNFOfTCwSMj8LY"
genai.configure(api_key=GOOGLE_API_KEY)
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GOOGLE_API_KEY)


# Initialize FAISS index from a fixed PDF path
guidelines_pdf_path = r"E:\VocabProject\VoiceProject\Speech_model\uploads\guidelines.pdf"
guidelines_index, guidelines_chunks = initialize_faiss(guidelines_pdf_path)
# Store session data
session_data = {
    "faiss_index": None,
    "text_chunks": None,
    "conversation_history": []
}


# Initialize conversation history
conversation_history = []

@app.route('/')
def index():
    """Serve the UI"""
    return render_template('index_latest.html')

# Updated conversation loop to support RAG when FAISS index is available
def conversation_loop(file_path):
    print("Customer Care Agent is ready to assist you. Speak now. Say 'exit' to end the conversation.")
    first_agent_response = "Good morning, thank you for contacting CRED-Help. How can I assist you today?"
    print(f"Agent: {first_agent_response}")
    conversation_history.append({"user": "Hello", "agent": first_agent_response})
    
    while True:
        # Step 1: Listen for speech
        # text, detected_language = listen_for_speech()
        # try: 
            text = send_audio_to_server_new(file_path)
            if not text:
                print("Didn't catch that. Please speak again...")
                continue

            print(f"User said: {text}")
            # Exit if user says 'exit'
            if text.strip().lower() == "exit":
                print("Agent: Thank you for reaching out to CRED. Have a great day!")
                break
            # Step 2: Generate AI Response
            # Generate agent response
            response = generate_response(
                query=text,
                guidelines_index=guidelines_index,
                guidelines_chunks=guidelines_chunks,
                llm=llm,
                conversation_history=conversation_history,
            )
            print(f"Agent: {response}")

            print(f"AI response: {response}")
        

            # Step 3: Convert response to speech
            # text_to_speech(response_text, lang=detected_language)
            # synthesize_and_play_audio(response)
        # finally:
        #     # Clean up
        #     if os.path.exists(file_path):
        #         os.remove(file_path)



def conversation_loop_new(file_path): 
    print("Customer Care Agent is ready to assist you. Speak now. Say 'exit' to end the conversation.")
    
    latencies = {}

    # 1. Get the audio transcription
    start = time.time()
    text = send_audio_to_server_new(file_path)
    latencies['send_audio_to_asr_server'] = time.time() - start

    if not text:
        print("Didn't catch that. Please speak again...")
        return {"user_input": None, "ai_response": "Could not understand input."}

    print(f"User said: {text}")

    # 2. Exit condition check (no timing needed)
    if text.strip().lower() == "exit":
        farewell = "Thank you for reaching out to CRED. Have a great day!"
        print(f"Agent: {farewell}")
        return {"user_input": text, "ai_response": farewell}

    # 3. First interaction check/response
    if not conversation_history:
        start = time.time()
        first_agent_response = "Good morning, thank you for contacting CRED-Help. How can I assist you today?"
        conversation_history.append({"user": "Hello", "agent": first_agent_response})
        latencies['first_response_append'] = time.time() - start

    # 4. Generate AI response
    start = time.time()
    response = generate_response(
        query=text,
        guidelines_index=guidelines_index,
        guidelines_chunks=guidelines_chunks,
        llm=llm,
        conversation_history=conversation_history,
    )
    latencies['generate_response_AP_Response'] = time.time() - start

    print(f"Agent: {response}")

    # 5. Update conversation history
    start = time.time()
    conversation_history.append({"user": text, "agent": response})
    latencies['update_history_for_conversation'] = time.time() - start

    # 6. Generate audio for frontend (don't play on server)
    start = time.time()
    # Don't play audio on server - let frontend handle it
    # synthesize_and_play_audio(response)
    latencies['audio_generation_skipped'] = time.time() - start

    # Print latencies
    print("\n--- Latency Report ---")
    for func_name, duration in latencies.items():
        print(f"{func_name}: {duration:.3f} seconds")
    print("----------------------\n")

    # Return the result as a dictionary
    return {"user_input": text, "ai_response": response}


@app.route('/start', methods=['GET'])
def start_conversation():
    """Start the speech conversation loop."""
    if not guidelines_index:
        return jsonify({"error": "Failed to initialize FAISS index"}), 500
    threading.Thread(target=conversation_loop).start()
    return jsonify({"message": "Speech conversation started"}), 200

@app.route('/converse', methods=['POST'])
def converse():
    try:
        print("Request received at /converse")

        audio = request.files.get('file')
        if not audio:
            print("No file in request")
            return jsonify({"error": "No audio file received"}), 400

        print(f"Received file: {audio.filename}")
        # uploads_dir = os.path.join(PROJECT_ROOT, 'uploads')
        # os.makedirs(uploads_dir, exist_ok=True)  # Ensure uploads folder exists

        save_path = os.path.join(save_dir, audio.filename)
        audio.save(save_path)
        print(f"Saved file to {save_path}")

        # threading.Thread(target=conversation_loop, args=(save_path,)).start()
        result = conversation_loop_new(save_path)
        return result, 200

    except Exception as e:
        print("Error during /converse:", e)
        traceback.print_exc()  # Shows full error in the server logs
        return jsonify({"error": str(e)}), 500

greeting_played = False
@app.route("/greet", methods=["GET"])
def greet_user():
    global greeting_played
    if not greeting_played:
        greeting = "Customer Care Agent is ready to assist you. Speak now. Say 'exit' to end the conversation."
        # Don't play on server - just return text
        print(greeting)
        # greeting_played = True
        return jsonify({"greeting": greeting})
    else:
        return jsonify({"greeting": None})

@app.route("/tts", methods=["POST"])
def text_to_speech_endpoint():
    """Convert text to speech and return audio data for frontend playback."""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({"error": "No text provided"}), 400
        
        # Create TTS audio
        temp_file = "temp_response.mp3"
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(temp_file)
        
        # Read the audio file and convert to base64
        with open(temp_file, 'rb') as audio_file:
            audio_data = audio_file.read()
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        # Clean up temp file
        os.remove(temp_file)
        
        return jsonify({
            "success": True,
            "audio": audio_base64,
            "format": "mp3"
        })
        
    except Exception as e:
        print(f"TTS Error: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
