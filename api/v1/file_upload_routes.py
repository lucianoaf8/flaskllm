# tests/integration/test_calendar_api.py
import json
from unittest.mock import patch

import pytest

from app import create_app
from core.config import Settings, EnvironmentType


@pytest.fixture
def app():
    """Create an application for testing."""
    # Create test settings
    test_settings = Settings(
        environment=EnvironmentType.TESTING,
        api_token="test_token",
        openai_api_key="test_openai_key",
        debug=True,
        rate_limit_enabled=False,
        google_credentials_file="tests/fixtures/mock_google_credentials.json"
    )

    # Create app with test settings
    app = create_app(test_settings)
    return app


@pytest.fixture
def client(app):
    """Create a test client."""
    with app.test_client() as client:
        yield client


@pytest.fixture
def auth_headers():
    """Create headers with authentication token for testing."""
    return {"X-API-Token": "test_token", "Content-Type": "application/json"}


@patch('integrations.google_auth.GoogleOAuth.get_credentials')
@patch('googleapiclient.discovery.build')
def test_list_calendar_events(mock_build, mock_get_credentials, client, auth_headers):
    """Test listing calendar events."""
    # Mock the calendar service
    mock_service = mock_build.return_value
    mock_events = mock_service.events.return_value
    mock_list = mock_events.list.return_value

    # Set up the mock response
    mock_list.execute.return_value = {
        'items': [
            {
                'id': 'event123',
                'summary': 'Team Meeting',
                'start': {
                    'dateTime': '2025-06-01T10:00:00-04:00',
                    'timeZone': 'America/New_York'
                },
                'end': {
                    'dateTime': '2025-06-01T11:00:00-04:00',
                    'timeZone': 'America/New_York'
                }
            }
        ]
    }

    # Make the request
    response = client.get('/api/v1/calendar/events', headers=auth_headers)

    # Check the response
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'events' in data
    assert len(data['events']) == 1
    assert data['events'][0]['id'] == 'event123'
    assert data['events'][0]['summary'] == 'Team Meeting'


@patch('integrations.google_auth.GoogleOAuth.get_credentials')
@patch('googleapiclient.discovery.build')
def test_create_calendar_event(mock_build, mock_get_credentials, client, auth_headers):
    """Test creating a calendar event."""
    # Mock the calendar service
    mock_service = mock_build.return_value
    mock_events = mock_service.events.return_value
    mock_insert = mock_events.insert.return_value

    # Set up the mock response
    mock_insert.execute.return_value = {
        'id': 'event123',
        'summary': 'Team Meeting',
        'htmlLink': 'https://calendar.google.com/event?id=event123'
    }

    # Prepare the request data
    event_data = {
        'summary': 'Team Meeting',
        'start': {
            'dateTime': '2025-06-01T10:00:00-04:00',
            'timeZone': 'America/New_York'
        },
        'end': {
            'dateTime': '2025-06-01T11:00:00-04:00',
            'timeZone': 'America/New_York'
        }
    }

    # Make the request
    response = client.post(
        '/api/v1/calendar/events',
        headers=auth_headers,
        json={
            'event': event_data
        }
    )

    # Check the response
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'event' in data
    assert data['event']['id'] == 'event123'
    assert data['event']['summary'] == 'Team Meeting'


@patch('integrations.google_auth.GoogleOAuth.get_credentials')
@patch('googleapiclient.discovery.build')
@patch('llm.openai_handler.OpenAIHandler.process_prompt')
def test_process_text_to_calendar(mock_process_prompt, mock_build, mock_get_credentials, client, auth_headers):
    """Test processing text to calendar event."""
    # Mock the LLM response
    mock_process_prompt.return_value = json.dumps({
        'summary': 'Team Meeting',
        'description': 'Weekly team sync',
        'location': 'Conference Room A',
        'start': '2025-06-01T10:00:00',
        'end': '2025-06-01T11:00:00'
    })

    # Mock the calendar service for event creation
    mock_service = mock_build.return_value
    mock_events = mock_service.events.return_value
    mock_insert = mock_events.insert.return_value

    # Set up the mock response
    mock_insert.execute.return_value = {
        'id': 'event123',
        'summary': 'Team Meeting',
        'htmlLink': 'https://calendar.google.com/event?id=event123'
    }

    # Make the request
    response = client.post(
        '/api/v1/calendar/process-text',
        headers=auth_headers,
        json={
            'text': 'Schedule a team meeting on June 1st at 10 AM in Conference Room A',
            'create_event': True
        }
    )

    # Check the response
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'event' in data
    assert data['created'] is True
    assert data['event']['id'] == 'event123'
    assert data['event']['summary'] == 'Team Meeting'

    # Check that the LLM was called correctly
    mock_process_prompt.assert_called_once()
    assert 'Schedule a team meeting' in mock_process_prompt.call_args[1]['prompt']
    assert mock_process_prompt.call_args[1]['source'] == 'calendar'
    assert mock_process_prompt.call_args[1]['type'] == 'calendar_event'


@patch('integrations.google_auth.GoogleOAuth.get_authorization_url')
def test_calendar_auth(mock_get_authorization_url, client, auth_headers):
    """Test initiating calendar authentication."""
    # Mock the authorization URL
    mock_get_authorization_url.return_value = 'https://accounts.google.com/o/oauth2/auth?...'

    # Make the request
    response = client.get('/api/v1/calendar/auth', headers=auth_headers)

    # Check the response (should be a redirect)
    assert response.status_code == 302
    assert response.headers['Location'] == 'https://accounts.google.com/o/oauth2/auth?...'

    # Check that the auth URL was requested with the correct user ID
    mock_get_authorization_url.assert_called_once_with('test_token')
