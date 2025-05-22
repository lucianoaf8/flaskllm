# api/v1/routes.py (additional calendar endpoints)

from flask import Blueprint, current_app, redirect, request, session, url_for
from marshmallow import ValidationError

from core.auth import require_api_token
from core.exceptions import CalendarError
from integrations.google_auth import GoogleOAuth
from integrations.google_calendar import GoogleCalendarService, EventMapper
from llm.factory import get_llm_handler

from .schemas import CalendarEventSchema

# Initialize services
google_oauth = GoogleOAuth(
    credentials_file=current_app.config.get('GOOGLE_CREDENTIALS_FILE')
)
calendar_service = GoogleCalendarService(google_oauth)
event_mapper = EventMapper(timezone=current_app.config.get('DEFAULT_TIMEZONE', 'UTC'))

@api_v1.route('/calendar/events', methods=['GET'])
@require_api_token
def list_calendar_events():
    """
    List calendar events.

    Returns:
        List of calendar events
    """
    user_id = request.headers.get('X-API-Token')

    try:
        # Get calendar ID (use primary by default)
        calendar_id = request.args.get('calendar_id')
        if not calendar_id:
            calendar_id = calendar_service.get_primary_calendar_id(user_id)

        # Get time range (default to next 7 days)
        time_min = request.args.get('time_min', datetime.utcnow().isoformat() + 'Z')
        time_max = request.args.get(
            'time_max',
            (datetime.utcnow() + timedelta(days=7)).isoformat() + 'Z'
        )

        # Get events
        service = calendar_service.get_service(user_id)
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            maxResults=10,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])

        return {
            'events': events
        }
    except CalendarError as e:
        return {
            'error': 'Calendar Error',
            'details': str(e),
            'code': 'CALENDAR_ERROR'
        }, 400
    except Exception as e:
        current_app.logger.error(f"Error listing calendar events: {str(e)}", exc_info=True)
        return {
            'error': 'Server Error',
            'details': str(e),
            'code': 'SERVER_ERROR'
        }, 500

@api_v1.route('/calendar/events', methods=['POST'])
@require_api_token
def create_calendar_event():
    """
    Create a calendar event.

    Returns:
        Created event data
    """
    user_id = request.headers.get('X-API-Token')

    try:
        # Get calendar ID (use primary by default)
        calendar_id = request.json.get('calendar_id')
        if not calendar_id:
            calendar_id = calendar_service.get_primary_calendar_id(user_id)

        # Get event data
        schema = CalendarEventSchema()
        event_data = schema.load(request.json.get('event', {}))

        # Create event
        event = calendar_service.create_event(user_id, calendar_id, event_data)

        return {
            'event': event
        }
    except ValidationError as e:
        return {
            'error': 'Validation Error',
            'details': str(e),
            'code': 'VALIDATION_ERROR'
        }, 400
    except CalendarError as e:
        return {
            'error': 'Calendar Error',
            'details': str(e),
            'code': 'CALENDAR_ERROR'
        }, 400
    except Exception as e:
        current_app.logger.error(f"Error creating calendar event: {str(e)}", exc_info=True)
        return {
            'error': 'Server Error',
            'details': str(e),
            'code': 'SERVER_ERROR'
        }, 500

@api_v1.route('/calendar/process-text', methods=['POST'])
@require_api_token
def process_text_to_calendar():
    """
    Process text with LLM and create a calendar event.

    Returns:
        Created event data
    """
    user_id = request.headers.get('X-API-Token')

    try:
        # Get input text
        text = request.json.get('text')
        if not text:
            return {
                'error': 'Validation Error',
                'details': 'Input text is required',
                'code': 'VALIDATION_ERROR'
            }, 400

        # Get optional parameters
        calendar_id = request.json.get('calendar_id')
        create_event = request.json.get('create_event', False)

        # Use LLM to process the text
        llm_handler = get_llm_handler()
        result = llm_handler.process_prompt(
            prompt=f"Extract calendar event details from the following text and return a JSON structure with summary, description, location, start and end times: {text}",
            source="calendar",
            type="calendar_event"
        )

        # Map the result to a calendar event
        try:
            event_data = event_mapper.map_from_llm_output(result)
        except ValueError as e:
            return {
                'error': 'Processing Error',
                'details': f"Failed to extract event details: {str(e)}",
                'code': 'PROCESSING_ERROR'
            }, 400

        # Optionally create the event
        if create_event:
            if not calendar_id:
                calendar_id = calendar_service.get_primary_calendar_id(user_id)

            event = calendar_service.create_event(user_id, calendar_id, event_data)

            return {
                'event': event,
                'created': True
            }
        else:
            return {
                'event': event_data,
                'created': False
            }
    except CalendarError as e:
        return {
            'error': 'Calendar Error',
            'details': str(e),
            'code': 'CALENDAR_ERROR'
        }, 400
    except Exception as e:
        current_app.logger.error(f"Error processing text to calendar: {str(e)}", exc_info=True)
        return {
            'error': 'Server Error',
            'details': str(e),
            'code': 'SERVER_ERROR'
        }, 500
