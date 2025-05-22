from marshmallow import Schema, fields, validates, validates_schema, ValidationError

class CalendarEventTimeSchema(Schema):
    """Schema for calendar event time."""
    date = fields.String(required=False)
    dateTime = fields.String(required=False)
    timeZone = fields.String(required=False)

    @validates_schema
    def validate_time(self, data, **kwargs):
        """Validate that either date or dateTime is provided."""
        if 'date' not in data and 'dateTime' not in data:
            raise ValidationError("Either date or dateTime must be provided")

class CalendarEventAttendeeSchema(Schema):
    """Schema for calendar event attendee."""
    email = fields.Email(required=False)
    displayName = fields.String(required=False)
    responseStatus = fields.String(required=False)

    @validates_schema
    def validate_attendee(self, data, **kwargs):
        """Validate that either email or displayName is provided."""
        if 'email' not in data and 'displayName' not in data:
            raise ValidationError("Either email or displayName must be provided")

class CalendarEventSchema(Schema):
    """Schema for calendar event."""
    summary = fields.String(required=True)
    description = fields.String(required=False)
    location = fields.String(required=False)
    start = fields.Nested(CalendarEventTimeSchema, required=True)
    end = fields.Nested(CalendarEventTimeSchema, required=True)
    attendees = fields.List(fields.Nested(CalendarEventAttendeeSchema), required=False)
    reminders = fields.Dict(required=False)

class CalendarProcessTextSchema(Schema):
    """Schema for processing text to calendar event."""
    text = fields.String(required=True)
    calendar_id = fields.String(required=False)
    create_event = fields.Boolean(required=False, default=False)
