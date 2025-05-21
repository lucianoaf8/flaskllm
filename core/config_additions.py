# core/config.py (additions)
class Settings(BaseSettings):
    """Application settings."""

    # Add new settings
    max_file_size_mb: int = Field(default=10, description="Maximum file size in MB")
    templates_dir: Optional[str] = Field(
        default=None, description="Directory for prompt templates"
    )
    conversation_storage_dir: Optional[str] = Field(
        default=None, description="Directory for conversation storage"
    )
    user_settings_storage_dir: Optional[str] = Field(
        default=None, description="Directory for user settings storage"
    )
