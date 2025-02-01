# Multilingual News Generator

A full-stack web application that converts news articles into multilingual video content for social media platforms. This tool is specifically designed for Minnesota news outlets to reach diverse communities speaking different languages.

## Features

- Text and audio input support
- Multi-language summarization and translation
- Text-to-Speech generation in multiple languages
- Avatar-based video generation
- Support for multiple output formats

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
Create a `.env` file with:
```
OPENAI_API_KEY=your_key_here
GOOGLE_APPLICATION_CREDENTIALS=path_to_credentials.json
D_ID_API_KEY=your_key_here
```

3. Run the application:
```bash
python app.py
```

## API Keys Required

- OpenAI API key for summarization and translation
- Google Cloud credentials for TTS and translation
- D-ID API key for avatar generation

## Usage

1. Access the web interface at `http://localhost:5000`
2. Paste your article text or upload audio
3. Select target languages
4. Generate and download the video content

## Tech Stack

- Backend: Flask (Python)
- Frontend: HTML, CSS, JavaScript
- APIs: OpenAI, Google Cloud TTS, D-ID
- Storage: Local file system
