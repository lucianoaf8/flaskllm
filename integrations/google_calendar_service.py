# integrations/google_calendar.py
from datetime import datetime, timedelta
import json
import re
from typing import Dict, List, Optional, Tuple, Union

from flask import current_app
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pytz

from core.exceptions import CalendarError
from integrations.google_auth import GoogleOAuth


class GoogleCalendarService:
    """
    Service for interacting with Google Calendar API.
    """

    def __init__(self, google_auth: GoogleOAuth):
        """
        Initialize the Google Calendar service.

        Args:
            google_auth: GoogleOAuth instance for authentication
        """
        self.google_auth = google_auth

    def get_service(self, user_id: str):
        """
        Get a Google Calendar API service instance.

        Args:
            user_id: Unique identifier for the user

        Returns:
            Google Calendar API service

        Raises:
            CalendarError: If authentication fails
        """
        credentials = self.google_auth.get_credentials(user_id)

        if not credentials:
            raise CalendarError("Not authenticated with Google Calendar")

        return build('calendar', 'v3', credentials=credentials)

    def list_calendars(self, user_id: str) -> List[Dict]:
        """
        List available calendars for a user.

        Args:
            user_id: Unique identifier for the user

        Returns:
            List of calendar information

        Raises:
            CalendarError: If the API request fails
        """
        try:
            service = self.get_service(user_id)

            calendars = []
            page_token = None

            while True:
                calendar_list = service.calendarList().list(pageToken=page_token).execute()

                for calendar in calendar_list['items']:
                    calendars.append({
                        'id': calendar['id'],
                        'summary': calendar['summary'],
                        'description': calendar.get('description', ''),
                        'primary': calendar.get('primary', False),
                        'access_role': calendar.get('accessRole', '')
                    })

                page_token = calendar_list.get('nextPageToken')
                if not page_token:
                    break

            return calendars
        except HttpError as e:
            error_content = json.loads(e.content.decode())
            error_message = error_content.get('error', {}).get('message', str(e))
            current_app.logger.error(f"Google Calendar API error: {error_message}")
            raise CalendarError(f"Failed to list calendars: {error_message}")

    def create_event(
        self,
        user_id: str,
        calendar_id: str,
        event_data: Dict
    ) -> Dict:
        """
        Create a calendar event.

        Args:
            user_id: Unique identifier for the user
            calendar_id: ID of the calendar
            event_data: Event data

        Returns:
            Created event data

        Raises:
            CalendarError: If the API request fails
        """
        try:
            service = self.get_service(user_id)

            # Ensure event has the required fields
            if 'start' not in event_data or 'end' not in event_data:
                raise CalendarError("Event must have start and end times")

            # Create the event
            event = service.events().insert(
                calendarId=calendar_id,
                body=event_data,
                sendNotifications=False
            ).execute()

            return {
                'id': event['id'],
                'summary': event.get('summary', ''),
                'description': event.get('description', ''),
                'location': event.get('location', ''),
                'start': event.get('start', {}),
                'end': event.get('end', {}),
                'htmlLink': event.get('htmlLink', '')
            }
        except HttpError as e:
            error_content = json.loads(e.content.decode())
            error_message = error_content.get('error', {}).get('message', str(e))
            current_app.logger.error(f"Google Calendar API error: {error_message}")
            raise CalendarError(f"Failed to create event: {error_message}")

    def update_event(
        self,
        user_id: str,
        calendar_id: str,
        event_id: str,
        event_data: Dict
    ) -> Dict:
        """
        Update a calendar event.

        Args:
            user_id: Unique identifier for the user
            calendar_id: ID of the calendar
            event_id: ID of the event
            event_data: Event data

        Returns:
            Updated event data

        Raises:
            CalendarError: If the API request fails
        """
        try:
            service = self.get_service(user_id)

            # Get the existing event first
            existing_event = service.events().get(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()

            # Update the event with new data
            for key, value in event_data.items():
                existing_event[key] = value

            # Update the event
            updated_event = service.events().update(
                calendarId=calendar_id,
                eventId=event_id,
                body=existing_event
            ).execute()

            return {
                'id': updated_event['id'],
                'summary': updated_event.get('summary', ''),
                'description': updated_event.get('description', ''),
                'location': updated_event.get('location', ''),
                'start': updated_event.get('start', {}),
                'end': updated_event.get('end', {}),
                'htmlLink': updated_event.get('htmlLink', '')
            }
        except HttpError as e:
            error_content = json.loads(e.content.decode())
            error_message = error_content.get('error', {}).get('message', str(e))
            current_app.logger.error(f"Google Calendar API error: {error_message}")
            raise CalendarError(f"Failed to update event: {error_message}")

    def delete_event(self, user_id: str, calendar_id: str, event_id: str) -> bool:
        """
        Delete a calendar event.

        Args:
            user_id: Unique identifier for the user
            calendar_id: ID of the calendar
            event_id: ID of the event

        Returns:
            True if successful

        Raises:
            CalendarError: If the API request fails
        """
        try:
            service = self.get_service(user_id)

            # Delete the event
            service.events().delete(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()

            return True
        except HttpError as e:
            error_content = json.loads(e.content.decode())
            error_message = error_content.get('error', {}).get('message', str(e))
            current_app.logger.error(f"Google Calendar API error: {error_message}")
            raise CalendarError(f"Failed to delete event: {error_message}")

    def get_primary_calendar_id(self, user_id: str) -> str:
        """
        Get the primary calendar ID for a user.

        Args:
            user_id: Unique identifier for the user

        Returns:
            Primary calendar ID

        Raises:
            CalendarError: If the API request fails or no primary calendar
        """
        try:
            calendars = self.list_calendars(user_id)

            for calendar in calendars:
                if calendar.get('primary'):
                    return calendar['id']

            # If no primary calendar found, use the first one
            if calendars:
                return calendars[0]['id']

            raise CalendarError("No calendars found for user")
        except Exception as e:
            raise CalendarError(f"Failed to get primary calendar: {str(e)}")


class EventMapper:
    """
    Maps LLM output to Google Calendar event structure.
    """

    def __init__(self, timezone: str = 'UTC'):
        """
        Initialize the event mapper.

        Args:
            timezone: Default timezone for events
        """
        self.timezone = timezone

    def map_from_llm_output(self, llm_output: str) -> Dict:
        """
        Map LLM output to calendar event data.

        Args:
            llm_output: Processed output from LLM

        Returns:
            Mapped event data

        Raises:
            ValueError: If required fields cannot be extracted
        """
        # The LLM should provide structured data, but we'll also handle free-form text

        # Check if the output is valid JSON
        try:
            event_data = json.loads(llm_output)

            # Verify required fields
            if 'summary' not in event_data:
                raise ValueError("Event summary not found in LLM output")

            # Format dates if provided as strings
            self._format_event_dates(event_data)

            return event_data
        except json.JSONDecodeError:
            # Handle free-form text
            current_app.logger.info("LLM output is not JSON, extracting event data from text")
            return self._extract_event_from_text(llm_output)

    def _extract_event_from_text(self, text: str) -> Dict:
        """
        Extract event data from free-form text.

        Args:
            text: Free-form text description of an event

        Returns:
            Extracted event data

        Raises:
            ValueError: If required fields cannot be extracted
        """
        event_data = {
            'summary': '',
            'description': '',
            'location': '',
            'start': {},
            'end': {}
        }

        # Extract summary/title
        title_patterns = [
            r'Event: ([^\n]+)',
            r'Title: ([^\n]+)',
            r'Summary: ([^\n]+)',
            r'Meeting: ([^\n]+)',
            r'^([^\n]+)'  # Fallback to first line
        ]

        for pattern in title_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                event_data['summary'] = match.group(1).strip()
                break

        if not event_data['summary']:
            raise ValueError("Could not extract event title from text")

        # Extract description
        desc_patterns = [
            r'Description: ([\s\S]+?)(?=Location:|Date:|Time:|When:|Attendees:|$)',
            r'Details: ([\s\S]+?)(?=Location:|Date:|Time:|When:|Attendees:|$)',
            r'Notes: ([\s\S]+?)(?=Location:|Date:|Time:|When:|Attendees:|$)'
        ]

        for pattern in desc_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                event_data['description'] = match.group(1).strip()
                break

        # Extract location
        location_patterns = [
            r'Location: ([^\n]+)',
            r'Place: ([^\n]+)',
            r'Venue: ([^\n]+)'
        ]

        for pattern in location_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                event_data['location'] = match.group(1).strip()
                break

        # Extract date and time
        date_patterns = [
            # Date and time range in one line
            r'(?:Date|Time|When):\s*([A-Za-z]+,?\s+[A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})?(?:\s+(?:from|at)\s+)?(\d{1,2}:\d{2}\s*[AP]M)\s*(?:-|to)\s*(\d{1,2}:\d{2}\s*[AP]M)',
            r'(?:Date|Time|When):\s*([A-Za-z]+,?\s+[A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})?(?:\s+(?:from|at)\s+)?(\d{1,2}:\d{2}\s*(?:am|pm|AM|PM)?)(?:\s*(?:-|to|–)\s*(\d{1,2}:\d{2}\s*(?:am|pm|AM|PM)?))?',

            # Date followed by time
            r'Date:\s*([A-Za-z]+,?\s+[A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})',
            r'Time:\s*(\d{1,2}:\d{2}\s*(?:am|pm|AM|PM)?)(?:\s*(?:-|to|–)\s*(\d{1,2}:\d{2}\s*(?:am|pm|AM|PM)?))?',

            # Datetime in more flexible formats
            r'(\d{1,2}/\d{1,2}/\d{2,4})\s+(?:at|from)?\s*(\d{1,2}:\d{2}\s*(?:am|pm|AM|PM)?)(?:\s*(?:-|to|–)\s*(\d{1,2}:\d{2}\s*(?:am|pm|AM|PM)?))?',
            r'([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})\s+(?:at|from)?\s*(\d{1,2}:\d{2}\s*(?:am|pm|AM|PM)?)(?:\s*(?:-|to|–)\s*(\d{1,2}:\d{2}\s*(?:am|pm|AM|PM)?))?'
        ]

        # Try to extract date and time
        date_str = None
        start_time_str = None
        end_time_str = None

        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) >= 1 and groups[0]:
                    date_str = groups[0]
                if len(groups) >= 2 and groups[1]:
                    start_time_str = groups[1]
                if len(groups) >= 3 and groups[2]:
                    end_time_str = groups[2]
                break

        # If we couldn't extract structured date/time, fallback to today or tomorrow
        # and make an educated guess at duration (e.g., 1 hour meeting)
        if not date_str:
            # Check if text mentions "tomorrow"
            if re.search(r'\btomorrow\b', text, re.IGNORECASE):
                date_str = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            else:
                date_str = datetime.now().strftime('%Y-%m-%d')

        # Try to extract time if not found yet
        if not start_time_str:
            time_match = re.search(r'(\d{1,2}(?::\d{2})?\s*(?:am|pm|AM|PM))', text)
            if time_match:
                start_time_str = time_match.group(1)

                # Look for duration or end time
                duration_match = re.search(r'for\s+(\d+)\s+(?:hour|hr)s?', text, re.IGNORECASE)
                if duration_match:
                    try:
                        duration_hours = int(duration_match.group(1))

                        # Parse the start time
                        start_dt = self._parse_datetime_parts(date_str, start_time_str)
                        if start_dt:
                            end_dt = start_dt + timedelta(hours=duration_hours)
                            end_time_str = end_dt.strftime('%I:%M %p')
                    except (ValueError, TypeError):
                        pass

        # Set default times if not found
        if not start_time_str:
            # Default to business hours if not specified
            current_hour = datetime.now().hour
            if current_hour < 12:
                start_time_str = "9:00 AM"
            else:
                start_time_str = "2:00 PM"

        if not end_time_str:
            # Default to 1 hour meeting
            try:
                start_dt = self._parse_datetime_parts(date_str, start_time_str)
                if start_dt:
                    end_dt = start_dt + timedelta(hours=1)
                    end_time_str = end_dt.strftime('%I:%M %p')
                else:
                    # Fallback
                    if "AM" in start_time_str.upper():
                        end_time_str = start_time_str.upper().replace("AM", "PM")
                    else:
                        end_time_str = "1 hour later"
            except (ValueError, TypeError):
                end_time_str = "1 hour after start"

        # Convert to Google Calendar format
        try:
            start_dt = self._parse_datetime_parts(date_str, start_time_str)
            end_dt = self._parse_datetime_parts(date_str, end_time_str)

            if start_dt and end_dt:
                # If end time is earlier than start time, assume it's the next day
                if end_dt < start_dt:
                    end_dt = end_dt + timedelta(days=1)

                # Format for Google Calendar
                event_data['start'] = {
                    'dateTime': start_dt.isoformat(),
                    'timeZone': self.timezone
                }

                event_data['end'] = {
                    'dateTime': end_dt.isoformat(),
                    'timeZone': self.timezone
                }
            else:
                # Fallback to all-day event
                try:
                    all_day_date = self._parse_date(date_str)
                    event_data['start'] = {
                        'date': all_day_date.strftime('%Y-%m-%d')
                    }
                    event_data['end'] = {
                        'date': (all_day_date + timedelta(days=1)).strftime('%Y-%m-%d')
                    }
                except (ValueError, TypeError):
                    raise ValueError("Could not parse event date and time")
        except Exception as e:
            current_app.logger.error(f"Error parsing date/time: {str(e)}")
            raise ValueError(f"Failed to parse event date and time: {str(e)}")

        # Extract attendees (optional)
        attendees_match = re.search(r'Attendees:(.+?)(?=\n\n|\n[A-Z]|$)', text, re.IGNORECASE | re.DOTALL)
        if attendees_match:
            attendees_text = attendees_match.group(1).strip()
            attendees = []

            # Look for emails or names
            email_pattern = r'[\w\.-]+@[\w\.-]+'
            emails = re.findall(email_pattern, attendees_text)

            for email in emails:
                attendees.append({'email': email})

            # If no emails found, try to extract names
            if not attendees:
                names = [name.strip() for name in attendees_text.split(',')]
                for name in names:
                    if name:
                        attendees.append({'displayName': name})

            if attendees:
                event_data['attendees'] = attendees

        return event_data

    def _format_event_dates(self, event_data: Dict) -> None:
        """
        Format dates in event data to Google Calendar format.

        Args:
            event_data: Event data dictionary to modify in place
        """
        # Handle start date/time
        if 'start' in event_data:
            if isinstance(event_data['start'], str):
                # Convert string to dateTime format
                try:
                    start_dt = self._parse_datetime(event_data['start'])
                    event_data['start'] = {
                        'dateTime': start_dt.isoformat(),
                        'timeZone': self.timezone
                    }
                except (ValueError, TypeError):
                    # Try as date only
                    try:
                        start_date = self._parse_date(event_data['start'])
                        event_data['start'] = {
                            'date': start_date.strftime('%Y-%m-%d')
                        }
                    except (ValueError, TypeError):
                        raise ValueError(f"Invalid start date/time format: {event_data['start']}")

        # Handle end date/time
        if 'end' in event_data:
            if isinstance(event_data['end'], str):
                # Check if start is date-only
                if 'start' in event_data and 'date' in event_data['start']:
                    # End should be date-only too
                    try:
                        end_date = self._parse_date(event_data['end'])
                        event_data['end'] = {
                            'date': end_date.strftime('%Y-%m-%d')
                        }
                    except (ValueError, TypeError):
                        raise ValueError(f"Invalid end date format: {event_data['end']}")
                else:
                    # Convert string to dateTime format
                    try:
                        end_dt = self._parse_datetime(event_data['end'])
                        event_data['end'] = {
                            'dateTime': end_dt.isoformat(),
                            'timeZone': self.timezone
                        }
                    except (ValueError, TypeError):
                        raise ValueError(f"Invalid end date/time format: {event_data['end']}")

        # If we have a start but no end, default to 1 hour later
        if 'start' in event_data and 'end' not in event_data:
            if 'dateTime' in event_data['start']:
                start_dt = datetime.fromisoformat(event_data['start']['dateTime'].replace('Z', '+00:00'))
                end_dt = start_dt + timedelta(hours=1)
                event_data['end'] = {
                    'dateTime': end_dt.isoformat(),
                    'timeZone': event_data['start']['timeZone']
                }
            elif 'date' in event_data['start']:
                start_date = datetime.strptime(event_data['start']['date'], '%Y-%m-%d')
                end_date = start_date + timedelta(days=1)
                event_data['end'] = {
                    'date': end_date.strftime('%Y-%m-%d')
                }

    def _parse_datetime(self, date_string: str) -> datetime:
        """
        Parse a datetime string in various formats.

        Args:
            date_string: String representation of date/time

        Returns:
            datetime object

        Raises:
            ValueError: If the string cannot be parsed
        """
        formats = [
            '%Y-%m-%dT%H:%M:%S',  # ISO format
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%d %H:%M:%S',
            '%m/%d/%Y %H:%M:%S',
            '%m/%d/%Y %I:%M %p',
            '%B %d, %Y %I:%M %p',
            '%B %d %Y %I:%M %p',
            '%b %d, %Y %I:%M %p',
            '%b %d %Y %I:%M %p',
            '%d %B %Y %I:%M %p',
            '%d %b %Y %I:%M %p',
            '%Y-%m-%d %I:%M %p',
            '%m/%d/%y %I:%M %p'
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(date_string, fmt)
                if dt.tzinfo is None:
                    # Add timezone if not present
                    tz = pytz.timezone(self.timezone)
                    dt = tz.localize(dt)
                return dt
            except ValueError:
                pass

        raise ValueError(f"Could not parse datetime: {date_string}")

    def _parse_date(self, date_string: str) -> datetime:
        """
        Parse a date string in various formats.

        Args:
            date_string: String representation of date

        Returns:
            datetime object (date only)

        Raises:
            ValueError: If the string cannot be parsed
        """
        formats = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%B %d, %Y',
            '%B %d %Y',
            '%b %d, %Y',
            '%b %d %Y',
            '%d %B %Y',
            '%d %b %Y',
            '%m/%d/%y'
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_string, fmt)
            except ValueError:
                pass

        raise ValueError(f"Could not parse date: {date_string}")

    def _parse_datetime_parts(self, date_str: str, time_str: str) -> Optional[datetime]:
        """
        Parse date and time strings separately and combine them.

        Args:
            date_str: String representation of date
            time_str: String representation of time

        Returns:
            datetime object or None if parsing fails
        """
        try:
            # Parse date
            date_obj = self._parse_date(date_str)

            # Parse time
            time_formats = [
                '%I:%M %p',
                '%I:%M%p',
                '%I%p',
                '%H:%M',
                '%H:%M:%S'
            ]

            # Normalize time string
            time_str = time_str.strip().upper()
            if 'AM' not in time_str and 'PM' not in time_str:
                # Add AM/PM if missing
                hour = int(re.search(r'^\d{1,2}', time_str).group(0))
                if hour < 8:  # Assume evening hours if less than 8
                    time_str += ' PM'
                else:
                    time_str += ' AM'

            time_obj = None
            for fmt in time_formats:
                try:
                    time_obj = datetime.strptime(time_str, fmt)
                    break
                except ValueError:
                    pass

            if time_obj is None:
                return None

            # Combine date and time
            tz = pytz.timezone(self.timezone)
            return tz.localize(datetime.combine(date_obj.date(), time_obj.time()))
        except Exception as e:
            current_app.logger.error(f"Error parsing datetime parts: {str(e)}")
            return None
