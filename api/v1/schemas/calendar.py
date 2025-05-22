"""
Calendar Schema Definitions

This module contains Pydantic schemas for calendar-related operations.
"""
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator

class CalendarEventTime(BaseModel):
    """Schema for calendar event time."""
    date: Optional[str] = None
    dateTime: Optional[str] = None
    timeZone: Optional[str] = None

    @validator('date', 'dateTime', always=True)
    def validate_time(cls, v, values):
        """Validate that either date or dateTime is provided."""
        if not v and 'date' not in values and 'dateTime' not in values:
            raise ValueError("Either date or dateTime must be provided")
        return v

class CalendarEventAttendee(BaseModel):
    """Schema for calendar event attendee."""
    email: Optional[str] = None
    displayName: Optional[str] = None
    responseStatus: Optional[str] = None

    @validator('email', 'displayName', always=True)
    def validate_attendee(cls, v, values):
        """Validate that either email or displayName is provided."""
        if not v and 'email' not in values and 'displayName' not in values:
            raise ValueError("Either email or displayName must be provided")
        return v

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
