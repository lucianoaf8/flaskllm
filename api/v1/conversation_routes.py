# examples/calendar_integration.py
"""
Examples of using the FlaskLLM API calendar integration.

This script demonstrates how to use the FlaskLLM API to create calendar events
from natural language text, including authentication, event creation, and more.
"""
import json
import requests

# Configuration
API_URL = "https://yourusername.pythonanywhere.com"
API_TOKEN = "your_api_token"

def authenticate_calendar():
    """Start the calendar authentication flow."""
    print("Opening browser for Google Calendar authentication...")
    print(f"Visit: {API_URL}/api/v1/calendar/auth")
    print("Headers: X-API-Token: your_api_token")
    print("After authentication, you'll be redirected to a success page.")
    print("Once complete, you can use the calendar integration.")

def list_calendar_events():
    """List calendar events for the next week."""
    headers = {
        "Content-Type": "application/json",
        "X-API-Token": API_TOKEN
    }

    response = requests.get(
        f"{API_URL}/api/v1/calendar/events",
        headers=headers
    )

    if response.status_code == 200:
        events = response.json().get("events", [])
        print(f"Found {len(events)} events:")
        for event in events:
            print(f"- {event['summary']}")
            start = event.get("start", {}).get("dateTime", event.get("start", {}).get("date", "No date"))
            print(f"  When: {start}")
            print(f"  Link: {event.get('htmlLink', 'No link')}")
            print("")
    else:
        print(f"Error: {response.status_code}")
        print(response.json())

def create_calendar_event():
    """Create a calendar event from structured data."""
    headers = {
        "Content-Type": "application/json",
        "X-API-Token": API_TOKEN
    }

    event_data = {
        "summary": "Team Meeting",
        "description": "Weekly team sync to discuss ongoing projects",
        "location": "Conference Room A",
        "start": {
            "dateTime": "2025-06-01T10:00:00-04:00",
            "timeZone": "America/New_York"
        },
        "end": {
            "dateTime": "2025-06-01T11:00:00-04:00",
            "timeZone": "America/New_York"
        },
        "attendees": [
            {"email": "john@example.com"},
            {"email": "jane@example.com"}
        ]
    }

    response = requests.post(
        f"{API_URL}/api/v1/calendar/events",
        headers=headers,
        json={"event": event_data}
    )

    if response.status_code == 200:
        event = response.json().get("event", {})
        print("Event created successfully!")
        print(f"Summary: {event.get('summary')}")
        print(f"Link: {event.get('htmlLink')}")
    else:
        print(f"Error: {response.status_code}")
        print(response.json())

def process_text_to_calendar():
    """Process natural language text to create a calendar event."""
    headers = {
        "Content-Type": "application/json",
        "X-API-Token": API_TOKEN
    }

    text = "Let's have a team meeting on June 1st at 10 AM in Conference Room A to discuss the Q2 roadmap. Please invite John and Jane."

    response = requests.post(
        f"{API_URL}/api/v1/calendar/process-text",
        headers=headers,
        json={
            "text": text,
            "create_event": True
        }
    )

    if response.status_code == 200:
        result = response.json()
        event = result.get("event", {})
        created = result.get("created", False)

        print(f"Text processed successfully!")
        print(f"Event {'created' if created else 'extracted'}:")
        print(f"Summary: {event.get('summary')}")
        print(f"Description: {event.get('description')}")
        print(f"Location: {event.get('location')}")
        print(f"Start: {event.get('start')}")
        print(f"End: {event.get('end')}")
        if created:
            print(f"Link: {event.get('htmlLink')}")
    else:
        print(f"Error: {response.status_code}")
        print(response.json())

def use_webhook_for_calendar():
    """Use the webhook endpoint to create a calendar event."""
    headers = {
        "Content-Type": "application/json",
        "X-API-Token": API_TOKEN
    }

    response = requests.post(
        f"{API_URL}/api/v1/webhook",
        headers=headers,
        json={
            "prompt": "Schedule a team meeting on June 1st at 10 AM in Conference Room A to discuss the Q2 roadmap",
            "source": "email",
            "type": "calendar_event"
        }
    )

    if response.status_code == 200:
        result = response.json()
        event = result.get("event", {})
        created = result.get("created", False)

        print(f"Webhook processed successfully!")
        print(f"Event {'created' if created else 'extracted'}:")
        print(f"Summary: {event.get('summary')}")
        print(f"Start: {event.get('start')}")
        print(f"End: {event.get('end')}")
        if created:
            print(f"Link: {event.get('htmlLink')}")
    else:
        print(f"Error: {response.status_code}")
        print(response.json())

def revoke_calendar_access():
    """Revoke the application's access to Google Calendar."""
    headers = {
        "Content-Type": "application/json",
        "X-API-Token": API_TOKEN
    }

    response = requests.post(
        f"{API_URL}/api/v1/calendar/auth/revoke",
        headers=headers
    )

    if response.status_code == 200:
        result = response.json()
        print(f"Status: {result.get('status')}")
        print(f"Message: {result.get('message')}")
    else:
        print(f"Error: {response.status_code}")
        print(response.json())

def show_menu():
    """Show menu of example functions."""
    print("\nFlaskLLM API Calendar Integration Examples")
    print("------------------------------------------")
    print("1. Authenticate with Google Calendar")
    print("2. List Calendar Events")
    print("3. Create Calendar Event")
    print("4. Process Text to Calendar Event")
    print("5. Use Webhook for Calendar Event")
    print("6. Revoke Calendar Access")
    print("0. Exit")

    choice = input("\nEnter your choice (0-6): ")

    if choice == "1":
        authenticate_calendar()
    elif choice == "2":
        list_calendar_events()
    elif choice == "3":
        create_calendar_event()
    elif choice == "4":
        process_text_to_calendar()
    elif choice == "5":
        use_webhook_for_calendar()
    elif choice == "6":
        revoke_calendar_access()
    elif choice == "0":
        return False
    else:
        print("Invalid choice. Please try again.")

    return True

if __name__ == "__main__":
    print("Welcome to the FlaskLLM API Calendar Integration Examples")
    print("This script demonstrates how to use the FlaskLLM API calendar integration features.")
    print("Make sure to update the API_URL and API_TOKEN variables at the top of the script.")

    continue_running = True
    while continue_running:
        continue_running = show_menu()

    print("Thank you for trying the FlaskLLM API calendar integration examples!")
