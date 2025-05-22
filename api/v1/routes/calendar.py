"""
Calendar API Routes

This module provides API routes for calendar integration, allowing users to:
- List calendar events
- Create calendar events
- Process text to extract calendar events
"""
from flask import Blueprint, Response, current_app, jsonify, request
from api.v1.schemas.calendar import CalendarEventRequest, CalendarEventResponse
from core.auth import auth_required
from integrations.google_calendar_service import GoogleCalendarService

# Create a blueprint for the calendar routes
bp = Blueprint('calendar', __name__, url_prefix='/calendar')

# Initialize logger
from core.logging import get_logger
logger = get_logger(__name__)

@bp.route('/events', methods=['GET'])
@auth_required
def list_calendar_events():
    """
    List calendar events.

    Returns:
        List of calendar events
    """
    try:
        # Get calendar service
        calendar_service = GoogleCalendarService(current_app.config.get("SETTINGS"))
        
        # Get calendar ID (use primary by default)
        calendar_id = request.args.get('calendar_id')
        if not calendar_id:
            calendar_id = 'primary'

        # Get time range parameters
        time_min = request.args.get('time_min')
        time_max = request.args.get('time_max')
        max_results = request.args.get('max_results', 10)

        # Get events
        events = calendar_service.list_events(
            calendar_id=calendar_id,
            time_min=time_min,
            time_max=time_max,
            max_results=max_results
        )

        return jsonify({"events": events}), 200
    except Exception as e:
        logger.error(f"Error listing calendar events: {str(e)}")
        return jsonify({"error": str(e)}), 500

@bp.route('/events', methods=['POST'])
@auth_required
def create_calendar_event():
    """
    Create a calendar event.

    Returns:
        Created event data
    """
    try:
        # Parse request data
        data = request.get_json()
        event_request = CalendarEventRequest(**data)
        
        # Get calendar service
        calendar_service = GoogleCalendarService(current_app.config.get("SETTINGS"))
        
        # Get calendar ID (use primary by default)
        calendar_id = event_request.calendar_id or 'primary'

        # Create event
        event = calendar_service.create_event(
            calendar_id=calendar_id,
            event_data=event_request.dict(exclude_unset=True)
        )

        # Create response
        response = CalendarEventResponse(
            event=event,
            created=True
        )

        return jsonify(response.dict()), 201
    except ValueError as e:
        logger.warning(f"Validation error creating calendar event: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error creating calendar event: {str(e)}")
        return jsonify({"error": str(e)}), 500

@bp.route('/process-text', methods=['POST'])
@auth_required
def process_text_to_calendar():
    """
    Process text with LLM and create a calendar event.

    Returns:
        Created event data
    """
    try:
        # Parse request data
        data = request.get_json()
        text = data.get('text')
        if not text:
            return jsonify({"error": "Input text is required"}), 400
            
        calendar_id = data.get('calendar_id', 'primary')
        create_event = data.get('create_event', False)

        # Get LLM handler
        from llm.factory import get_llm_handler
        llm_handler = get_llm_handler(current_app.config.get("SETTINGS"))
        
        # Process text to extract event details
        result = llm_handler.process_prompt(
            prompt=f"Extract calendar event details from the following text and return a JSON structure with summary, description, location, start and end times: {text}",
            source="calendar",
            type="calendar_event"
        )

        # Parse the result
        import json
        try:
            event_data = json.loads(result)
        except json.JSONDecodeError:
            return jsonify({"error": "Failed to parse LLM output as JSON"}), 500

        # Optionally create the event
        if create_event:
            # Get calendar service
            calendar_service = GoogleCalendarService(current_app.config.get("SETTINGS"))
            
            # Create event
            event = calendar_service.create_event(
                calendar_id=calendar_id,
                event_data=event_data
            )
            
            response = {
                'event': event,
                'created': True
            }
        else:
            response = {
                'event': event_data,
                'created': False
            }

        return jsonify(response), 200
    except ValueError as e:
        logger.warning(f"Validation error processing text to calendar: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error processing text to calendar: {str(e)}")
        return jsonify({"error": str(e)}), 500
