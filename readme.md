# Vocab Assist - AI Voice Chat Application

This is the backend service for the Vocab Assist feature, providing AI-powered voice chat capabilities.

## Features

- Real-time voice chat with AI
- Speech-to-text and text-to-speech conversion
- Conversation history tracking
- Low-latency response generation
- Cross-origin resource sharing (CORS) enabled for web integration

## Prerequisites

- Python 3.x
- Virtual environment (recommended)
- Required Python packages (see requirements.txt)

## Installation

1. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

### Manual Start
To start the server manually:
```bash
python new_app.py
```
The server will start at http://127.0.0.1:5001

### Automatic Start
The server can be started automatically through the main website:
1. Navigate to the Services section
2. Click on "Vocab Assist"
3. The server will start automatically and redirect you to the interface

## API Endpoints

- `GET /`: Serves the main UI interface
- `POST /converse`: Handles audio file uploads and conversation
- `GET /greet`: Provides initial greeting

## Integration with Main Website

The Vocab Assist feature is integrated with the main website (localhost:3000) and can be accessed through:
1. Desktop: Services dropdown menu
2. Mobile: Services section in mobile menu

## Development

- Main application file: `new_app.py`
- Processing logic: `updated_processing.py`
- Server startup script: `start_server.py`

## Troubleshooting

If you encounter a 403 Forbidden error:
1. Ensure the Flask server is running
2. Check that CORS is properly configured
3. Verify you're accessing from the correct origin (localhost:3000)

## License

[Your License Information]



