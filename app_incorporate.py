# app.py (additions)
from core.token_service import TokenService
from core.token_storage import TokenStorage

def create_app(settings: Optional[Settings] = None) -> Flask:
    # ... existing code ...
    
    # Initialize token management
    token_storage = TokenStorage(
        db_path=settings.token_db_path,
        encryption_key=settings.token_encryption_key
    )
    token_service = TokenService(token_storage)
    
    # Store in app config for access in routes
    app.config["TOKEN_SERVICE"] = token_service
    
    # Migrate legacy token if it exists
    if hasattr(settings, "api_token") and settings.api_token:
        token_service.migrate_legacy_token(settings.api_token, "Migrated legacy token")
    
    # ... rest of existing code ...