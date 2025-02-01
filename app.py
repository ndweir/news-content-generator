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
        
        print(f"Processing summary for language: {target_lang}")
        
        # Generate summary using OpenAI
        summary_prompt = f"Summarize this article in under 75 words. Keep it factual and do not add information not present in the text:\n\n{text}"
        
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional news summarizer. Create concise, accurate summaries without adding any information not present in the original text."},
                    {"role": "user", "content": summary_prompt}
                ]
            )
            
            # TEMPORARY TEST OVERRIDE
            summary = get_mock_style_summary("news", target_lang)
            # summary = response.choices[0].message.content
            print(f"Generated English summary: {summary[:100]}...")

            # Translate if needed
            if target_lang != 'en':
                print(f"Translating to {SUPPORTED_LANGUAGES[target_lang]}")
                translation_prompt = f"Translate this text to {SUPPORTED_LANGUAGES[target_lang]}:\n\n{summary}"
                
                try:
                    translation_response = openai.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": f"You are a professional translator. Translate the following text to {SUPPORTED_LANGUAGES[target_lang]} while maintaining the original meaning."},
                            {"role": "user", "content": translation_prompt}
                        ]
                    )
                    summary = translation_response.choices[0].message.content
                    print(f"Translation completed: {summary[:100]}...")
                    
                except Exception as translation_error:
                    print(f"Translation error: {str(translation_error)}")
                    return jsonify({'error': f'Translation failed: {str(translation_error)}'}), 500

            return jsonify({'summary': summary})
            
        except Exception as openai_error:
            print(f"OpenAI API error: {str(openai_error)}")
            return jsonify({'error': f'OpenAI API error: {str(openai_error)}'}), 500

    except Exception as e:
        import traceback
        print(f"Error in summarize endpoint: {str(e)}")
        print("Full traceback:")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

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
