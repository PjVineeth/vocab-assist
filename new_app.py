from flask import Flask, jsonify, render_template, request
import time
import os
from flask_cors import CORS
from updated_processing import *
import traceback
import time
import logging
import base64

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure CORS to allow requests from your Next.js app
CORS(app, resources={
    r"/*": {
        "origins": [
            "http://localhost:3000", 
            "http://localhost:5001", 
            "http://127.0.0.1:5001", 
            "http://27.111.72.61:4003",           # Your actual production URL
            "http://27.111.72.61.nip.io:4003",    # Alternative domain
            "https://27.111.72.61:4003"           # HTTPS version
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Get the current directory where the Python script is running
script_dir = os.path.dirname(os.path.abspath(__file__))
# Target path: uploads/files/recorded.wav relative to the script location
save_dir = os.path.join(script_dir, 'uploads')
os.makedirs(save_dir, exist_ok=True)


# Initialize conversation history
conversation_history = []

@app.route('/')
def index():
    """Serve the UI"""
    return render_template('index_latest.html')



def conversation_loop_new(file_path): 
    # print("Customer Care Agent is ready to assist you. Speak now. Say 'exit' to end the conversation.")
    print("Cred Agent is happy to help you , please let me know your query .")
    
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

    # 4. Generate AI response
    start = time.time()
    response = query_cred_chat_api(text)
    latencies['generate_response_Rag(AI)_Response'] = time.time() - start

    print(f"Agent: {response}")

    # 5. Update conversation history
    start = time.time()
    conversation_history.append({"user": text, "agent": response})

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


@app.route('/converse', methods=['POST'])
def converse():
    try:
        logger.info("🎤 Request received at /converse")

        audio = request.files.get('file')
        if not audio:
            logger.error("❌ No file in request")
            return jsonify({"error": "No audio file received"}), 400

        logger.info(f"📁 Received file: {audio.filename}")

        save_path = os.path.join(save_dir, audio.filename)
        audio.save(save_path)
        logger.info(f"💾 Saved file to {save_path}")

        logger.info("🔄 Processing conversation...")
        result = conversation_loop_new(save_path)
        
        logger.info(f"👤 User: {result.get('user_input', 'N/A')}")
        logger.info(f"🤖 AI: {result.get('ai_response', 'N/A')}")
        
        return result, 200

    except Exception as e:
        logger.error(f"❌ Error during /converse: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

greeting_played = False
@app.route("/greet", methods=["GET"])
def greet_user():
    global greeting_played
    if not greeting_played:
        # greeting = "Customer Care Agent is ready to assist you. Speak now. Say 'exit' to end the conversation."
        greeting = "Cred Agent is happy to help you , please let me know your query ."
        logger.info("👋 Sending greeting to user")
        # Don't play on server - just return text
        logger.info(f"🤖 Greeting: {greeting}")
        # greeting_played = True
        return jsonify({"greeting": greeting})
    else:
        logger.info("👋 Greeting already sent, skipping")
        return jsonify({"greeting": None})


@app.route("/tts", methods=["POST"])
def text_to_speech_endpoint():
    """Convert text to speech and return audio data for frontend playback."""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            logger.error("❌ No text provided for TTS")
            return jsonify({"error": "No text provided"}), 400
        
        logger.info(f"🔊 Converting text to speech: {text[:50]}...")
        
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
        
        logger.info("✅ TTS audio generated successfully")
        
        return jsonify({
            "success": True,
            "audio": audio_base64,
            "format": "mp3"
        })
        
    except Exception as e:
        logger.error(f"❌ TTS Error: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    logger.info("🚀 Starting Vocab Assist Backend Server...")
    logger.info("🌐 Server will be available at http://0.0.0.0:5001")
    logger.info("🔧 Debug mode: ON")
    logger.info("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5001)
