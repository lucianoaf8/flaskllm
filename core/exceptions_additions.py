# core/exceptions.py (additions)
class TemplateError(APIError):
    """Error for template operations."""

    status_code = 400
    message = "Template operation failed"

class ConversationError(APIError):
    """Error for conversation operations."""

    status_code = 400
    message = "Conversation operation failed"

class FileProcessingError(APIError):
    """Error for file processing operations."""

    status_code = 400
    message = "File processing failed"

class SettingsError(APIError):
    """Error for settings operations."""

    status_code = 400
    message = "Settings operation failed"
