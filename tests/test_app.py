import pytest
from app import app
import json
from unittest.mock import patch, MagicMock

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture(autouse=True)
def mock_openai():
    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock(message=MagicMock(content="Test summary"))]
    
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_completion
    
    with patch('app.client', mock_client):
        yield mock_client

def test_index_route(client):
    """Test if the index route returns the correct template"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'html' in response.data

@pytest.mark.parametrize('target_lang', ['en', 'es', 'hmn', 'so'])
def test_summarize_route(client, mock_openai, target_lang):
    """Test the summarize endpoint with different languages"""
    test_data = {
        'text': 'This is a test article about art shanties.',
        'target_language': target_lang,
        'style': 'cronkite'
    }
    
    response = client.post('/api/summarize',
                         data=json.dumps(test_data),
                         content_type='application/json')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'summary' in data
    assert 'metadata' in data
    assert 'style' in data['metadata']
    assert 'voice_style' in data['metadata']
    assert 'video_style' in data['metadata']

def test_summarize_invalid_style(client):
    """Test the summarize endpoint with an invalid style"""
    test_data = {
        'text': 'Test article',
        'target_language': 'en',
        'style': 'invalid_style'
    }
    
    response = client.post('/api/summarize',
                          data=json.dumps(test_data),
                          content_type='application/json')
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'valid_styles' in data

def test_summarize_missing_text(client):
    """Test the summarize endpoint with missing text"""
    test_data = {
        'target_language': 'en',
        'style': 'cronkite'
    }
    
    response = client.post('/api/summarize',
                          data=json.dumps(test_data),
                          content_type='application/json')
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data

def test_summarize_short_text(client):
    """Test the summarize endpoint with text that's too short"""
    test_data = {
        'text': 'Short',
        'target_language': 'en',
        'style': 'cronkite'
    }
    
    response = client.post('/api/summarize',
                          data=json.dumps(test_data),
                          content_type='application/json')
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'too short' in data['error'].lower()

def test_summarize_long_text(client):
    """Test the summarize endpoint with text that's too long"""
    test_data = {
        'text': 'x' * 5001,  # Create text longer than 5000 chars
        'target_language': 'en',
        'style': 'cronkite'
    }
    
    response = client.post('/api/summarize',
                          data=json.dumps(test_data),
                          content_type='application/json')
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'too long' in data['error'].lower()

def test_summarize_invalid_language(client):
    """Test the summarize endpoint with an unsupported language"""
    test_data = {
        'text': 'This is a test article.',
        'target_language': 'invalid_lang',
        'style': 'cronkite'
    }
    
    response = client.post('/api/summarize',
                          data=json.dumps(test_data),
                          content_type='application/json')
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'supported_languages' in data
