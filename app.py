from flask import Flask, request, jsonify, render_template, send_file
from dotenv import load_dotenv
import os
import openai
from google.cloud import texttospeech, translate
import requests
import json
import tempfile
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Configure API clients
client = openai.Client(api_key=os.getenv('OPENAI_API_KEY'))
print(f"OpenAI API Key loaded: {'Yes' if client.api_key else 'No'}")
print(f"OpenAI API Key first 10 chars: {client.api_key[:10] if client.api_key else 'None'}")

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

@app.route('/api/summarize', methods=['POST'])
def summarize():
    print("\n=== Starting summarize request ===")
    try:
        data = request.json
        text = data.get('text')
        target_lang = data.get('target_language', 'en')
        style = data.get('style', 'cronkite')
        
        if style not in CONTENT_STYLES:
            return jsonify({'error': 'Invalid style selected'}), 400
            
        style_config = CONTENT_STYLES[style]
        print(f"Processing {style_config['name']} style summary for {SUPPORTED_LANGUAGES[target_lang]}")
        
        # Generate styled summary using OpenAI
        summary_prompt = f"{style_config['prompt']}. Optimize for TikTok/Instagram vertical video format (30-60 seconds):\n\n{text}"
        
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": f"You are {style_config['name']}. Create engaging, mobile-first content that's perfect for social media."},
                    {"role": "user", "content": summary_prompt}
                ]
            )
            
            summary = response.choices[0].message.content
            print(f"Generated {style_config['name']} summary: {summary[:100]}...")

            # Translate if needed
            if target_lang != 'en':
                print(f"Translating to {SUPPORTED_LANGUAGES[target_lang]}")
                translation_prompt = f"Translate this {style_config['name']} style content to {SUPPORTED_LANGUAGES[target_lang]}. Maintain the style and tone:\n\n{summary}"
                
                try:
                    translation_response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": f"You are a creative translator specializing in {style_config['name']} style content."},
                            {"role": "user", "content": translation_prompt}
                        ]
                    )
                    summary = translation_response.choices[0].message.content
                    print(f"Translation completed: {summary[:100]}...")
                    
                except Exception as translation_error:
                    print(f"Translation error: {str(translation_error)}")
                    return jsonify({
                        'error': 'Translation failed',
                        'details': str(translation_error)
                    }), 500

            return jsonify({
                'summary': summary,
                'style': style_config['name'],
                'voice_style': style_config['voice'],
                'video_style': style_config['video_style']
            })
            
        except Exception as openai_error:
            print(f"OpenAI API error: {str(openai_error)}")
            return jsonify({
                'error': 'Content generation failed',
                'details': str(openai_error)
            }), 500

    except Exception as e:
        import traceback
        print(f"Error in summarize endpoint: {str(e)}")
        print("Full traceback:")
        print(traceback.format_exc())
        return jsonify({
            'error': 'Server error',
            'details': str(e)
        }), 500

@app.route('/api/generate-speech', methods=['POST'])
def generate_speech():
    try:
        data = request.json
        text = data.get('text')
        language_code = data.get('language_code', 'en-US')

        # Configure TTS request
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        voice = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        )
        
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        response = tts_client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )

        # Save the audio file
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], 'output.mp3')
        with open(audio_path, 'wb') as out:
            out.write(response.audio_content)

        return jsonify({'audio_path': 'output.mp3'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-video', methods=['POST'])
def generate_video():
    try:
        data = request.json
        audio_path = data.get('audio_path')
        
        # D-ID API configuration
        d_id_key = os.getenv('D_ID_API_KEY')
        d_id_url = "https://api.d-id.com/talks"
        
        headers = {
            "Authorization": f"Basic {d_id_key}",
            "Content-Type": "application/json"
        }
        
        # Read audio file
        with open(os.path.join(app.config['UPLOAD_FOLDER'], audio_path), 'rb') as audio_file:
            files = {
                'audio': audio_file,
                'config': json.dumps({
                    "source_url": "https://create-images-results.d-id.com/DefaultPresenters/Emma_f/image.jpeg"
                })
            }
            
            response = requests.post(d_id_url, headers=headers, files=files)
            
            if response.status_code == 201:
                talk_id = response.json()['id']
                return jsonify({'talk_id': talk_id})
            else:
                return jsonify({'error': 'Failed to generate video'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/uploads/<path:filename>')
def serve_file(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))

if __name__ == '__main__':
    app.run(debug=True, port=5004)
