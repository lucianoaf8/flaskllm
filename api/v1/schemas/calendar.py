# api/v1/schemas/calendar.py - Updated for Pydantic V2
"""
Calendar Schema Definitions - Updated for Pydantic V2
"""
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator

class CalendarEventTime(BaseModel):
    """Schema for calendar event time."""
    date: Optional[str] = None
    dateTime: Optional[str] = None
    timeZone: Optional[str] = None

    @model_validator(mode='after')
    def validate_time_fields(self):
        """Validate that either date or dateTime is provided."""
        if not self.date and not self.dateTime:
            raise ValueError("Either date or dateTime must be provided")
        return self

class CalendarEventAttendee(BaseModel):
    """Schema for calendar event attendee."""
    email: Optional[str] = None
    displayName: Optional[str] = None
    responseStatus: Optional[str] = None

    @model_validator(mode='after')
    def validate_attendee_fields(self):
        """Validate that either email or displayName is provided."""
        if not self.email and not self.displayName:
            raise ValueError("Either email or displayName must be provided")
        return self

class CalendarEventRequest(BaseModel):
    """Schema for calendar event creation request."""
    summary: str
    description: Optional[str] = None
    location: Optional[str] = None
    start: CalendarEventTime
    end: CalendarEventTime
    attendees: Optional[List[CalendarEventAttendee]] = None
    reminders: Optional[Dict[str, Any]] = None
    calendar_id: Optional[str] = None

class CalendarEventResponse(BaseModel):
    """Schema for calendar event response."""
    event: Dict[str, Any]
    created: bool = False

class CalendarProcessTextRequest(BaseModel):
    """Schema for processing text to calendar event."""
    text: str
    calendar_id: Optional[str] = None
    create_event: bool = False