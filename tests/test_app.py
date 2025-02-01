import pytest
from app import app
import json
from unittest.mock import patch, MagicMock

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index_route(client):
    """Test if the index route returns the correct template"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'html' in response.data

@pytest.mark.parametrize('target_lang', ['en', 'es', 'fr'])
def test_summarize_route(client, target_lang):
    """Test the summarize endpoint with different languages"""
    test_data = {
        'text': 'This is a test article about art shanties.',
        'target_language': target_lang,
        'style': 'cronkite'
    }
    
    # Mock OpenAI API response
    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock(message=MagicMock(content="Test summary"))]
    
    with patch('openai.Client.chat.completions.create', return_value=mock_completion):
        response = client.post('/api/summarize',
                             data=json.dumps(test_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'summary' in data
        assert 'style' in data
        assert 'voice_style' in data
        assert 'video_style' in data

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
