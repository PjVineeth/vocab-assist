FROM python:3.10-slim

# Install system dependencies for pygame mixer and pyaudio
RUN apt-get update && apt-get install -y \
    build-essential \
    libglib2.0-0 \
    libgl1 \
    libasound2 \
    libx11-6 \
    libxcursor1 \
    libxrandr2 \
    libxinerama1 \
    libxi6 \
    libsm6 \
    libxext6 \
    portaudio19-dev \
    libasound2-dev \
    python3-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the required packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the port the app runs on
EXPOSE 5001

# Run the application with gunicorn
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:$PORT new_app:app"]