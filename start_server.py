import subprocess
import sys
import os

def start_flask_server():
    # Get the directory of the current script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Set environment variable to make Flask bind to all interfaces
    os.environ['FLASK_HOST'] = '0.0.0.0'
    os.environ['FLASK_PORT'] = '5001'
    
    # Activate virtual environment and start Flask server
    if sys.platform == "win32":
        activate_script = os.path.join(current_dir, ".venv", "Scripts", "activate")
        command = f"cmd /c {activate_script} && python new_app.py"
    else:
        activate_script = os.path.join(current_dir, ".venv", "bin", "activate")
        command = f"source {activate_script} && python new_app.py"
    
    try:
        # Start the server in the background
        process = subprocess.Popen(command, shell=True, cwd=current_dir)
        print(f"Flask server started successfully with PID: {process.pid}")
        print("Server will be available at http://0.0.0.0:5001")
        return process
    except Exception as e:
        print(f"Error starting Flask server: {e}")
        return None

if __name__ == "__main__":
    start_flask_server() 