from flask import Flask, request, jsonify, render_template, send_file
from dotenv import load_dotenv
import os
import openai
from google.cloud import texttospeech, translate
import requests
import json
import tempfile
import logging
import time
from logging.handlers import RotatingFileHandler
from werkzeug.utils import secure_filename
from functools import wraps
from typing import Optional, Dict, Any

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
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['JSON_SORT_KEYS'] = False  # Preserve JSON response order

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Configure API clients
client = openai.Client(api_key=os.getenv('OPENAI_API_KEY'))
logger.info(f"OpenAI API Key loaded: {'Yes' if client.api_key else 'No'}")

tts_client = texttospeech.TextToSpeechClient()
translate_client = translate.TranslationServiceClient()

# Character styles for content generation
CONTENT_STYLES = {
    'ruff': {
        'name': 'Ruff Ruffman',
        'prompt': 'Create an educational, playful summary with science facts and dog-themed humor',
        'voice': 'enthusiastic, friendly',
        'video_style': 'vertical, energetic, educational'
    },
    'felix': {
        'name': 'Felix the Cat',
        'prompt': 'Write a whimsical, clever summary with classic cartoon charm and subtle humor',
        'voice': 'smooth, mischievous',
        'video_style': 'vertical, animated, playful'
    },
    'cronkite': {
        'name': 'Walter Cronkite Style',
        'prompt': 'Deliver a trustworthy, authoritative summary in classic broadcast style',
        'voice': 'deep, authoritative',
        'video_style': 'vertical, professional, news-style'
    },
    'wordgirl': {
        'name': 'WordGirl',
        'prompt': 'Create an educational summary that explains complex words and concepts',
        'voice': 'confident, educational',
        'video_style': 'vertical, superhero, educational'
    },
    'anime': {
        'name': 'Anime Style',
        'prompt': 'Write an engaging summary with anime-style narrative flair and emotional depth',
        'voice': 'expressive, dynamic',
        'video_style': 'vertical, anime-inspired, dramatic'
    }
}

SUPPORTED_LANGUAGES = {
    'en': 'English',
    'es': 'Spanish',
    'hmn': 'Hmong',
    'so': 'Somali'
}

@app.route('/')
def index():
    return render_template('index.html', languages=SUPPORTED_LANGUAGES)

def validate_request(required_fields: Dict[str, type] = None) -> callable:
    """Decorator to validate request data"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                data = request.get_json()
                if data is None:
                    return jsonify({'error': 'No JSON data provided'}), 400
                
                if required_fields:
                    for field, field_type in required_fields.items():
                        value = data.get(field)
                        if value is None:
                            return jsonify({'error': f'Missing required field: {field}'}), 400
                        if not isinstance(value, field_type):
                            return jsonify({'error': f'Invalid type for field {field}. Expected {field_type.__name__}'}), 400
                
                return f(*args, **kwargs)
            except Exception as e:
                logger.error(f'Request validation error: {str(e)}')
                return jsonify({'error': 'Invalid request format'}), 400
        return wrapper
    return decorator

def handle_api_error(func: callable) -> callable:
    """Decorator to handle API errors consistently"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f'API error in {func.__name__}: {str(e)}', exc_info=True)
            return jsonify({
                'error': 'Internal server error',
                'message': str(e)
            }), 500
    return wrapper

@app.route('/api/summarize', methods=['POST'])
@validate_request({'text': str, 'target_language': str, 'style': str})
@handle_api_error
def summarize():
    logger.info("=== Starting summarize request ===")
    data = request.json
    text = data['text'].strip()
    target_lang = data['target_language']
    style = data['style']
    
    # Validate input length
    if len(text) < 10:
        return jsonify({'error': 'Text is too short. Minimum 10 characters required.'}), 400
    if len(text) > 5000:
        return jsonify({'error': 'Text is too long. Maximum 5000 characters allowed.'}), 400
        
    # Validate style and language
    if style not in CONTENT_STYLES:
        return jsonify({
            'error': 'Invalid style selected',
            'valid_styles': list(CONTENT_STYLES.keys())
        }), 400
    
    if target_lang not in SUPPORTED_LANGUAGES:
        return jsonify({
            'error': 'Unsupported target language',
            'supported_languages': SUPPORTED_LANGUAGES
        }), 400
            
    style_config = CONTENT_STYLES[style]
    logger.info(f"Processing {style_config['name']} style summary for {SUPPORTED_LANGUAGES[target_lang]}")
    
    # Generate styled summary using OpenAI
    summary_prompt = f"{style_config['prompt']}. Optimize for TikTok/Instagram vertical video format (30-60 seconds):\n\n{text}"
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": f"You are {style_config['name']}. Create engaging, mobile-first content that's perfect for social media."},
            {"role": "user", "content": summary_prompt}
        ],
        max_tokens=500,  # Limit response length
        temperature=0.7  # Balance creativity and consistency
    )
    
    summary = response.choices[0].message.content
    logger.info(f"Generated {style_config['name']} summary: {summary[:100]}...")
    
    if not summary.strip():
        raise ValueError("Generated summary is empty")

    # Translate if needed
    if target_lang != 'en':
        logger.info(f"Translating to {SUPPORTED_LANGUAGES[target_lang]}")
        translation_prompt = f"Translate this {style_config['name']} style content to {SUPPORTED_LANGUAGES[target_lang]}. Maintain the style and tone:\n\n{summary}"
        
        translation_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"You are a creative translator specializing in {style_config['name']} style content."},
                {"role": "user", "content": translation_prompt}
            ],
            max_tokens=600,  # Allow slightly more tokens for translation
            temperature=0.3  # Lower temperature for more accurate translations
        )
        
        translated_summary = translation_response.choices[0].message.content
        if not translated_summary.strip():
            raise ValueError("Translation returned empty result")
            
        summary = translated_summary
        logger.info(f"Translation completed: {summary[:100]}...")

    # Prepare response with metadata
    response_data = {
        'summary': summary,
        'metadata': {
            'style': style_config['name'],
            'voice_style': style_config['voice'],
            'video_style': style_config['video_style'],
            'language': SUPPORTED_LANGUAGES[target_lang],
            'original_length': len(text),
            'summary_length': len(summary)
        }
    }
    
    logger.info(f"Successfully processed request for {style_config['name']} in {SUPPORTED_LANGUAGES[target_lang]}")
    return jsonify(response_data)



@app.route('/api/generate-speech', methods=['POST'])
@validate_request({'text': str, 'voice_style': str})
@handle_api_error
def generate_speech():
    data = request.json
    text = data['text'].strip()
    voice_style = data['voice_style']
    language_code = data.get('language_code', 'en-US')
    
    if len(text) < 1 or len(text) > 5000:
        return jsonify({'error': 'Text length must be between 1 and 5000 characters'}), 400

    # Configure TTS request
    synthesis_input = texttospeech.SynthesisInput(text=text)
    
    # Select voice based on style
    voice_params = texttospeech.VoiceSelectionParams(
        language_code=language_code,
        name=f"{language_code}-Wavenet-D"  # Using Wavenet for better quality
    )
    
    # Configure audio settings
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=1.0,  # Normal speed
        pitch=0.0  # Normal pitch
    )

    # Generate speech
    logger.info(f"Generating speech for text of length {len(text)} in {language_code}")
    response = tts_client.synthesize_speech(
        input=synthesis_input,
        voice=voice_params,
        audio_config=audio_config
    )

    if not response.audio_content:
        raise ValueError("No audio content generated")

    # Save the audio file with a secure filename
    output_filename = secure_filename(f"speech_{int(time.time())}.mp3")
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
    
    with open(output_path, "wb") as out:
        out.write(response.audio_content)

    logger.info(f"Successfully generated speech file: {output_filename}")
    return jsonify({
        'filename': output_filename,
        'url': f'/uploads/{output_filename}',
        'metadata': {
            'language': language_code,
            'voice_style': voice_style,
            'duration_seconds': len(response.audio_content) / 16000  # Approximate duration
        }
    })

@app.route('/api/generate-video', methods=['POST'])
@validate_request({'text': str, 'style': str})
@handle_api_error
def generate_video():
    data = request.json
    text = data['text']
    style = data['style']
    
    if len(text) < 1 or len(text) > 5000:
        return jsonify({'error': 'Text length must be between 1 and 5000 characters'}), 400
    
    if style not in CONTENT_STYLES:
        return jsonify({
            'error': 'Invalid style selected',
            'valid_styles': list(CONTENT_STYLES.keys())
        }), 400
    
    style_config = CONTENT_STYLES[style]
    
    # For now, return a mock response
    logger.info(f"Video generation requested for style: {style}")
    return jsonify({
        'status': 'success',
        'message': 'Video generation endpoint placeholder',
        'metadata': {
            'style': style_config['name'],
            'video_style': style_config['video_style']
        }
    })

@app.route('/uploads/<path:filename>')
@handle_api_error
def serve_file(filename):
    if not filename or '..' in filename:
        return jsonify({'error': 'Invalid filename'}), 400
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(filename))
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
        
    return send_file(file_path)

if __name__ == '__main__':
    app.run(debug=True, port=5004)
