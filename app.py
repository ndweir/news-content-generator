from flask import Flask, request, jsonify, render_template, send_file, url_for
from dotenv import load_dotenv
import os
import json
import tempfile
import logging
import time
from logging.handlers import RotatingFileHandler
from werkzeug.utils import secure_filename
from functools import wraps
from typing import Dict, Any, Optional
from pathlib import Path

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

# Initialize demo paths
demo_video_path = os.path.join('static', 'demo', 'demo.mp4')
demo_audio_path = os.path.join('static', 'demo', 'demo.mp3')

# Log initialization
logger.info('Running in demo mode - API keys not required')

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

        # Demo transcription
        return jsonify({
            'transcription': 'This is a demo transcription. In production, this would be the actual transcribed text from your audio file.',
            'language': 'en'
        })
    except Exception as e:
        logger.error(f'Transcription error: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate', methods=['POST'])
def generate_content():
    try:
        # Handle form data and files
        input_type = request.form.get('inputType', 'text')
        languages = request.form.getlist('languages[]')
        output_formats = request.form.getlist('outputFormats[]')
        style = request.form.get('style', 'news')
        cc_type = request.form.get('ccType', 'auto')

        if not languages or not output_formats:
            return jsonify({'error': 'Missing required fields'}), 400

        # For demo purposes, we'll return the demo video URL
        video_url = url_for('static', filename='demo/demo.mp4')
        
        return jsonify({
            'status': 'success',
            'message': 'Content generated successfully',
            'data': {
                'video_url': video_url,
                'languages': languages,
                'style': style
            }
        })
    except Exception as e:
        logger.error(f'Generation error: {str(e)}')
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
    """Demo version - returns mock translation"""
    # Original version with OpenAI API:
    '''
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
    '''
    
    # Demo version - returns mock translation
    if language == 'en':
        return f"[DEMO] English summary: {text[:100]}..."
    elif language == 'es':
        return f"[DEMO] Resumen en español: {text[:100]}..."
    elif language == 'fr':
        return f"[DEMO] Résumé en français: {text[:100]}..."
    else:
        return f"[DEMO] Translation to {LANGUAGES[language]['name']}: {text[:100]}..."

def generate_speech(text: str, language: str, style: str) -> str:
    """Demo version - returns path to demo audio file"""
    # Original version with OpenAI API:
    '''
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
    '''
    
    # Demo version - copy sample audio file
    import shutil
    timestamp = int(time.time())
    demo_path = os.path.join('static', 'demo', f'sample_{language}.mp3')
    output_path = os.path.join(app.config['AUDIO_FOLDER'], f'demo_{timestamp}.mp3')
    
    # Create demo audio file with text content
    from gtts import gTTS
    tts = gTTS(text[:100], lang=language)
    tts.save(output_path)
    
    return output_path

def generate_video(audio_path: str, style: str, cc_path: Optional[str] = None) -> str:
    """Demo version - returns demo video ID"""
    # Original version with D-ID API:
    '''
    style_params = VOICE_STYLES[style]
    
    with open(audio_path, 'rb') as audio_file:
        files = {
            'audio': ('audio.mp3', audio_file, 'audio/mpeg')
        }
        
        # Add captions file if provided
        if cc_path and os.path.exists(cc_path):
            with open(cc_path, 'rb') as cc_file:
                files['captions'] = ('captions.srt', cc_file, 'text/plain')
        
        payload = {
            'source_url': f"d-id://avatar/{style_params['avatar_id']}",
            'config': {
                'result_format': 'mp4',
                'style': style_params['video_style'],
                'subtitles': bool(cc_path)
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
    '''
    
    # Demo version - copy sample video and return ID
    import shutil
    timestamp = int(time.time())
    video_id = f'demo_{timestamp}'
    
    # Copy demo video to output directory
    demo_path = os.path.join('static', 'demo', 'sample_video.mp4')
    output_path = os.path.join(app.config['VIDEO_FOLDER'], f'{video_id}.mp4')
    
    # Create a short demo video using moviepy
    from moviepy.editor import AudioFileClip, ColorClip, TextClip, CompositeVideoClip
    
    # Create audio clip from the generated audio
    audio = AudioFileClip(audio_path)
    duration = audio.duration
    
    # Create a background
    bg = ColorClip(size=(1280, 720), color=(25, 25, 25), duration=duration)
    
    # Create text
    text = TextClip("Demo Video", fontsize=70, color='white', duration=duration)
    text = text.set_position('center')
    
    # Combine clips
    video = CompositeVideoClip([bg, text])
    video = video.set_audio(audio)
    
    # Add captions if provided
    if cc_path and os.path.exists(cc_path):
        with open(cc_path, 'r') as f:
            captions = f.read()
        caption_clip = TextClip(captions, fontsize=30, color='white', duration=duration)
        caption_clip = caption_clip.set_position(('center', 600))
        video = CompositeVideoClip([video, caption_clip])
    
    # Write video file
    video.write_videofile(output_path, fps=24, codec='libx264')
    
    return video_id

def extract_audio(video_path: str) -> str:
    """Extract audio from video file using moviepy"""
    try:
        from moviepy.editor import VideoFileClip
        
        video = VideoFileClip(video_path)
        output_path = video_path.rsplit('.', 1)[0] + '.mp3'
        video.audio.write_audiofile(output_path)
        video.close()
        
        return output_path
    except Exception as e:
        logger.error(f"Audio extraction error: {str(e)}")
        raise

def generate_captions(text: str, language: str) -> str:
    """Demo version - returns path to demo captions file"""
    # Original version with OpenAI API:
    '''
    try:
        # Use GPT-4 to generate properly timed captions
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Generate properly formatted SRT subtitles with timing for the following text. Ensure natural breaks and appropriate duration for each subtitle."},
                {"role": "user", "content": text}
            ]
        )
        
        srt_content = response.choices[0].message.content
        
        # Save SRT file
        timestamp = int(time.time())
        srt_path = f"uploads/captions_{timestamp}.srt"
        with open(srt_path, 'w', encoding='utf-8') as f:
            f.write(srt_content)
        
        return srt_path
    except Exception as e:
        logger.error(f"Caption generation error: {str(e)}")
        raise
    '''
    
    # Demo version - create simple SRT file
    try:
        timestamp = int(time.time())
        srt_path = os.path.join(app.config['UPLOAD_FOLDER'], f'captions_{timestamp}.srt')
        
        # Create a simple SRT file with the text split into 3-second segments
        words = text.split()
        srt_content = []
        words_per_segment = 10
        duration = 3  # seconds per segment
        
        for i in range(0, len(words), words_per_segment):
            segment_num = i // words_per_segment + 1
            start_time = (i // words_per_segment) * duration
            end_time = start_time + duration
            
            segment_words = words[i:i + words_per_segment]
            segment_text = ' '.join(segment_words)
            
            srt_content.append(f"{segment_num}\n")
            srt_content.append(f"{format_time(start_time)} --> {format_time(end_time)}\n")
            srt_content.append(f"{segment_text}\n\n")
        
        with open(srt_path, 'w', encoding='utf-8') as f:
            f.writelines(srt_content)
        
        return srt_path
    except Exception as e:
        logger.error(f"Caption generation error: {str(e)}")
        raise

def format_time(seconds):
    """Format seconds into SRT timestamp format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    milliseconds = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

def save_captions(file, video_id: str, language: str) -> str:
    """Save uploaded SRT captions file"""
    try:
        filename = secure_filename(file.filename)
        srt_path = os.path.join(app.config['UPLOAD_FOLDER'], f'captions_{video_id}_{language}.srt')
        file.save(srt_path)
        return srt_path
    except Exception as e:
        logger.error(f"Caption save error: {str(e)}")
        raise

if __name__ == '__main__':
    app.run(debug=True, port=5005)
