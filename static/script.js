let mediaRecorder;
let recordedChunks = [];
let typingIndicator = null; // Global reference for typing indicator
let animation; // Avatar animation

// Dynamic API base URL based on environment
const getApiBaseUrl = () => {
  const hostname = window.location.hostname;
  const protocol = window.location.protocol;
  
  // If running on Render (production)
  if (hostname.includes('onrender.com')) {
    return `${protocol}//${hostname}`;
  }
  
  // If running on specific production server
  if (hostname === '27.111.72.61') {
    return `http://27.111.72.61:5001`;
  }
  
  // Default to localhost for development
  return 'http://127.0.0.1:5001';
};

const API_BASE_URL = getApiBaseUrl();

const startBtn = document.getElementById('start');
const stopBtn = document.getElementById('stop');
const asrText = document.getElementById('asrText');
const recordingStatus = document.getElementById('recordingStatus');
const micAnimation = document.getElementById('micAnimation');
const avatarContainer = document.getElementById('avatarContainer');
const avatarSection = document.getElementById('avatarSection');

// --- Helper to load avatar animation and show first frame ---
function loadAvatarAnimation(path, autoplay = false, onReady = null) {
  if (animation) animation.destroy();
  animation = lottie.loadAnimation({
    container: avatarContainer,
    renderer: 'svg',
    loop: true,
    autoplay,
    path
  });
  animation.isDestroyed = false;
  animation.addEventListener('DOMLoaded', () => {
    if (!autoplay) animation.goToAndStop(animation.totalFrames - 1, true); // Show first frame
    if (typeof onReady === 'function') onReady();
  });
}

startBtn.addEventListener('click', async () => {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  mediaRecorder = new MediaRecorder(stream);
  recordedChunks = [];

  mediaRecorder.ondataavailable = e => {
    if (e.data.size > 0) recordedChunks.push(e.data);
  };

  mediaRecorder.onstop = async () => {
    recordingStatus.style.display = 'none';
    const blob = new Blob(recordedChunks, { type: 'audio/webm' });
    const wavBlob = await convertToWav(blob);

    const formData = new FormData();
    formData.append('file', wavBlob, 'recorded.wav');

    const typingIndicator = document.createElement('div');
    typingIndicator.className = 'message bot typing';
    typingIndicator.innerText = '🤖 is thinking...';
    asrText.appendChild(typingIndicator);
    typingIndicator.scrollIntoView({ behavior: 'smooth' });

    micAnimation.style.display = 'block';

    try {
      const response = await fetch(`${API_BASE_URL}/converse`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) throw new Error(`Status ${response.status}`);
      const result = await response.json();

      micAnimation.style.display = 'none';
      typingIndicator.remove();

      const userMsg = document.createElement('div');
      userMsg.className = 'message user';
      userMsg.innerText = `🧑 ${result.user_input}`;
      asrText.appendChild(userMsg);

      const botMsg = document.createElement('div');
      botMsg.className = 'message bot';
      botMsg.innerText = `🤖 ${result.ai_response}`;
      asrText.appendChild(botMsg);

      botMsg.scrollIntoView({ behavior: 'smooth' });
    } catch (err) {
      micAnimation.style.display = 'none';
      typingIndicator.remove();

      const errorMsg = document.createElement('div');
      errorMsg.className = 'message bot';
      errorMsg.innerText = '❌ Failed to get AI response.';
      asrText.appendChild(errorMsg);
    }
  };

  mediaRecorder.start();
  startBtn.disabled = true;
  stopBtn.disabled = false;
  recordingStatus.style.display = 'block';
});

stopBtn.addEventListener('click', () => {
  mediaRecorder.stop();
  startBtn.disabled = false;
  stopBtn.disabled = true;
});

async function convertToWav(blob) {
  const arrayBuffer = await blob.arrayBuffer();
  const audioContext = new AudioContext();
  const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
  const wavBuffer = encodeWAV(audioBuffer);
  return new Blob([wavBuffer], { type: 'audio/wav' });
}

function encodeWAV(audioBuffer) {
  const numChannels = audioBuffer.numberOfChannels;
  const sampleRate = audioBuffer.sampleRate;
  const format = 1;
  const bitDepth = 16;
  const samples = audioBuffer.length;
  const buffer = new ArrayBuffer(44 + samples * numChannels * 2);
  const view = new DataView(buffer);

  function writeString(view, offset, string) {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  }

  writeString(view, 0, 'RIFF');
  view.setUint32(4, 36 + samples * numChannels * 2, true);
  writeString(view, 8, 'WAVE');
  writeString(view, 12, 'fmt ');
  view.setUint32(16, 16, true);
  view.setUint16(20, format, true);
  view.setUint16(22, numChannels, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * numChannels * 2, true);
  view.setUint16(32, numChannels * 2, true);
  view.setUint16(34, bitDepth, true);
  writeString(view, 36, 'data');
  view.setUint32(40, samples * numChannels * 2, true);

  let offset = 44;
  for (let i = 0; i < samples; i++) {
    for (let ch = 0; ch < numChannels; ch++) {
      const sample = audioBuffer.getChannelData(ch)[i];
      const s = Math.max(-1, Math.min(1, sample));
      view.setInt16(offset, s * 0x7FFF, true);
      offset += 2;
    }
  }

  return view;
}

// --- On page load: show avatar's first frame ---
window.addEventListener('DOMContentLoaded', async () => {
  loadAvatarAnimation('https://lottie.host/61afd9a0-e462-4c31-b8b3-d12f41a63fc0/P9a5StytCO.json', false);

  // Optionally: greet the user
  try {
    const response = await fetch(`${API_BASE_URL}/greet`);
    const data = await response.json();
    if (data.greeting) {
      const botGreeting = document.createElement('div');
      botGreeting.className = 'message bot';
      botGreeting.innerText = `🤖 ${data.greeting}`;
      asrText.appendChild(botGreeting);
    }
  } catch (err) {
    console.error("Failed to fetch greeting:", err);
  }
});

// --- Load a random gesture (avatar pose) and show its first frame ---
function loadRandomGesture() {
  const gestures = ['gesture1.json', 'gesture2.json', 'gesture3.json'];
  const randomGesture = gestures[Math.floor(Math.random() * gestures.length)];
  loadAvatarAnimation(`../static/${randomGesture}`, false);
}
