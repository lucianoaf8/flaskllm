# Example of a more secure database-based token storage
# integrations/google_auth.py (enhanced version)

from cryptography.fernet import Fernet
from core.database import db

class SecureGoogleTokenStorage:
    """Securely stores Google OAuth tokens in the database with encryption."""

    def __init__(self):
        """Initialize the token storage with encryption key."""
        # In production, this key should be stored securely and not in code
        # You might load it from an environment variable or a secure key management service
        encryption_key = current_app.config.get('GOOGLE_TOKEN_ENCRYPTION_KEY')
        if not encryption_key:
            raise ValueError("Missing GOOGLE_TOKEN_ENCRYPTION_KEY configuration")

        self.cipher = Fernet(encryption_key)

    def store_token(self, user_id: str, token_data: Dict) -> None:
        """Store an encrypted token in the database."""
        token_json = json.dumps(token_data)
        encrypted_token = self.cipher.encrypt(token_json.encode())

        # Using SQLAlchemy ORM
        token_record = GoogleToken.query.filter_by(user_id=user_id).first()

        if token_record:
            token_record.token_data = encrypted_token
            token_record.updated_at = datetime.utcnow()
        else:
            token_record = GoogleToken(
                user_id=user_id,
                token_data=encrypted_token,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(token_record)

        db.session.commit()

    def get_token(self, user_id: str) -> Optional[Dict]:
        """Retrieve and decrypt a token from the database."""
        token_record = GoogleToken.query.filter_by(user_id=user_id).first()

        if not token_record:
            return None

        try:
            decrypted_token = self.cipher.decrypt(token_record.token_data)
            return json.loads(decrypted_token.decode())
        except Exception as e:
            current_app.logger.error(f"Error decrypting token for user {user_id}: {str(e)}")
            return None

    def delete_token(self, user_id: str) -> None:
        """Delete a token from the database."""
        token_record = GoogleToken.query.filter_by(user_id=user_id).first()

        if token_record:
            db.session.delete(token_record)
            db.session.commit()


# Database model for token storage
class GoogleToken(db.Model):
    """Model for storing encrypted Google OAuth tokens."""

    __tablename__ = 'google_tokens'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(255), unique=True, nullable=False)
    token_data = db.Column(db.LargeBinary, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f"<GoogleToken user_id={self.user_id}>"
