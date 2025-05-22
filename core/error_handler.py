# core/exceptions.py (addition)

class CalendarError(APIError):
    """Error for calendar operations."""

    status_code = 400
    message = "Calendar operation failed"
