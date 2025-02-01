from flask import Flask, request, jsonify, render_template, send_file
from dotenv import load_dotenv
import os
import openai
import requests
import json
import tempfile
import logging
import time
from logging.handlers import RotatingFileHandler
from werkzeug.utils import secure_filename
from functools import wraps
from typing import Dict, Any, Optional
from pathlib import Path
import whisper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=3)
handler.setFormatter(logging.Formatter(
    '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
))
logger.addHandler(handler)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['AUDIO_FOLDER'] = 'uploads/audio'
app.config['VIDEO_FOLDER'] = 'uploads/video'
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB max file size
app.config['JSON_SORT_KEYS'] = False

# Create necessary directories
for folder in [app.config['UPLOAD_FOLDER'], app.config['AUDIO_FOLDER'], app.config['VIDEO_FOLDER']]:
    Path(folder).mkdir(parents=True, exist_ok=True)

# Initialize API clients
client = openai.Client(api_key=os.getenv('OPENAI_API_KEY'))

# Load Whisper model for transcription
whisper_model = whisper.load_model('base')

# Initialize D-ID client
did_api_key = os.getenv('DID_API_KEY')
did_api_url = 'https://api.d-id.com'

# Log initialization status
logger.info(f"OpenAI API Key loaded: {'Yes' if os.getenv('OPENAI_API_KEY') else 'No'}")
logger.info(f"D-ID API Key loaded: {'Yes' if did_api_key else 'No'}")

# Language configurations
LANGUAGES = {
    'en': {
        'name': 'English',
        'voice': {
            'news': 'nova',      # Professional and clear
            'cronkite': 'echo',  # Authoritative and trustworthy
            'friendly': 'shimmer', # Warm and approachable
            'casual': 'fable'    # Youthful and engaging
        },
        'whisper_code': 'en',
        'did_code': 'en-US'
    },
    'es': {
        'name': 'Spanish',
        'voice': {
            'news': 'nova',
            'cronkite': 'echo',
            'friendly': 'shimmer',
            'casual': 'fable'
        },
        'whisper_code': 'es',
        'did_code': 'es-ES'
    },
    'so': {
        'name': 'Somali',
        'voice': {
            'news': 'nova',
            'cronkite': 'echo',
            'friendly': 'shimmer',
            'casual': 'fable'
        },
        'whisper_code': 'so',
        'did_code': 'so-SO'
    },
    'hmn': {
        'name': 'Hmong',
        'voice': {
            'news': 'nova',
            'cronkite': 'echo',
            'friendly': 'shimmer',
            'casual': 'fable'
        },
        'whisper_code': 'hmn',
        'did_code': 'hmn'
    }
}

# Voice styles
VOICE_STYLES = {
    'news': {
        'name': 'News Anchor',
        'prompt': 'Create a concise, factual news summary suitable for broadcast. Focus on key facts and maintain journalistic neutrality.',
        'model': 'tts-1-hd',  # Higher quality for professional broadcasts
        'avatar_id': 'news_anchor_1',
        'video_style': 'professional'
    },
    'cronkite': {
        'name': 'Walter Cronkite Style',
        'prompt': 'Create a trustworthy, authoritative news summary in the style of Walter Cronkite. Use clear, direct language and emphasize the gravity of the news.',
        'model': 'tts-1-hd',  # Higher quality for classic broadcast style
        'avatar_id': 'cronkite_style',
        'video_style': 'classic_broadcast'
    },
    'friendly': {
        'name': 'Friendly Presenter',
        'prompt': 'Create an engaging, conversational summary that feels warm and approachable. Break down complex topics into simple terms.',
        'model': 'tts-1',  # Standard quality for casual content
        'avatar_id': 'friendly_presenter',
        'video_style': 'casual'
    },
    'casual': {
        'name': 'Social Media Style',
        'prompt': 'Create a relaxed, informal summary suitable for social media. Use contemporary language while maintaining accuracy.',
        'model': 'tts-1',  # Standard quality for social content
        'avatar_id': 'social_presenter',
        'video_style': 'social'
    }
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/transcribe', methods=['POST'])
def transcribe_audio():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if not file.filename:
        return jsonify({'error': 'No file selected'}), 400

    try:
        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['AUDIO_FOLDER'], filename)
        file.save(filepath)

        # Transcribe using Whisper
        result = whisper_model.transcribe(filepath)
        
        return jsonify({
            'transcription': result['text'],
            'language': result['language']
        })
    except Exception as e:
        logger.error(f'Transcription error: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate', methods=['POST'])
def generate_content():
    data = request.json
    if not data or 'text' not in data or 'language' not in data or 'style' not in data:
        return jsonify({'error': 'Missing required fields'}), 400

    text = data['text']
    language = data['language']
    style = data['style']

    try:
        # Generate summary
        summary = summarize(text, language, style)

        # Generate speech
        audio_path = generate_speech(summary, language, style)

        # Generate video
        video_id = generate_video(audio_path, style)

        return jsonify({
            'summary': summary,
            'video_id': video_id
        })
    except Exception as e:
        logger.error(f'Content generation error: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/video-status/<video_id>')
def check_video_status(video_id):
    try:
        headers = {'Authorization': f'Basic {did_api_key}'}
        response = requests.get(f'{did_api_url}/talks/{video_id}', headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            status = data['status']
            
            if status == 'done':
                # Download the video
                video_url = data['result_url']
                video_response = requests.get(video_url)
                
                if video_response.status_code == 200:
                    # Save the video locally
                    video_path = os.path.join(app.config['VIDEO_FOLDER'], f'{video_id}.mp4')
                    with open(video_path, 'wb') as f:
                        f.write(video_response.content)
                    
                    return jsonify({
                        'status': 'done',
                        'local_url': f'/video/{video_id}.mp4'
                    })
            
            return jsonify({'status': status})
        
        return jsonify({'error': 'Failed to check video status'}), response.status_code
    except Exception as e:
        logger.error(f'Video status check error: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/video/<path:filename>')
def serve_video(filename):
    return send_file(
        os.path.join(app.config['VIDEO_FOLDER'], filename),
        mimetype='video/mp4'
    )

def summarize(text: str, language: str, style: str) -> str:
    system_prompt = f"You are a professional news content creator. {VOICE_STYLES[style]['prompt']}"
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Summarize this news content in {LANGUAGES[language]['name']}: {text}"}
    ]
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        temperature=0.7,
        max_tokens=500
    )
    
    return response.choices[0].message.content

def generate_speech(text: str, language: str, style: str) -> str:
    voice = LANGUAGES[language]['voice'][style]
    model = VOICE_STYLES[style]['model']
    
    response = client.audio.speech.create(
        model=model,
        voice=voice,
        input=text
    )
    
    audio_path = os.path.join(app.config['AUDIO_FOLDER'], f'{int(time.time())}.mp3')
    response.stream_to_file(audio_path)
    
    return audio_path

def generate_video(audio_path: str, style: str) -> str:
    style_params = VOICE_STYLES[style]
    
    with open(audio_path, 'rb') as audio_file:
        files = {
            'audio': ('audio.mp3', audio_file, 'audio/mpeg')
        }
        
        payload = {
            'source_url': f"d-id://avatar/{style_params['avatar_id']}",
            'config': {
                'result_format': 'mp4',
                'style': style_params['video_style']
            }
        }
        
        headers = {
            'Authorization': f'Basic {did_api_key}'
        }
        
        response = requests.post(
            f'{did_api_url}/talks',
            headers=headers,
            data={'json': json.dumps(payload)},
            files=files
        )
        
        if response.status_code == 201:
            return response.json()['id']
        else:
            raise Exception(f'Failed to generate video: {response.text}')

if __name__ == '__main__':
    app.run(debug=True, port=5005)
