# integrations/google_auth.py
import os
import json
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta

from flask import current_app, redirect, request, session, url_for
import requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from core.exceptions import AuthenticationError

class GoogleOAuth:
    """Handles Google OAuth authentication flow."""

    SCOPES = ['https://www.googleapis.com/auth/calendar.events']

    def __init__(self, credentials_file: str):
        """
        Initialize Google OAuth handler.

        Args:
            credentials_file: Path to the Google OAuth credentials JSON file
        """
        if not os.path.exists(credentials_file):
            raise FileNotFoundError(f"Google credentials file not found: {credentials_file}")

        self.credentials_file = credentials_file
        self.token_storage = GoogleTokenStorage()

    def get_authorization_url(self, user_id: str) -> str:
        """
        Get the Google authorization URL.

        Args:
            user_id: Unique identifier for the user

        Returns:
            Authorization URL for redirecting the user
        """
        flow = self._create_flow()

        # Store the flow state in a secure location
        session['google_auth_state'] = {
            'user_id': user_id,
            'created_at': datetime.utcnow().isoformat()
        }

        authorization_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'  # Force to get refresh token
        )

        return authorization_url

    def handle_callback(self, callback_data: Dict) -> Dict:
        """
        Handle the OAuth callback from Google.

        Args:
            callback_data: Callback data from Google

        Returns:
            Dict with user ID and success status

        Raises:
            AuthenticationError: If authentication fails
        """
        if 'error' in callback_data:
            raise AuthenticationError(f"Google OAuth error: {callback_data['error']}")

        if 'code' not in callback_data:
            raise AuthenticationError("Missing authorization code in callback")

        state = session.get('google_auth_state')
        if not state:
            raise AuthenticationError("Invalid state: authentication session expired")

        # Check if the state is too old (10 minutes maximum)
        created_at = datetime.fromisoformat(state['created_at'])
        if datetime.utcnow() - created_at > timedelta(minutes=10):
            raise AuthenticationError("Authentication session expired")

        user_id = state['user_id']

        # Exchange code for tokens
        flow = self._create_flow()
        flow.fetch_token(code=callback_data['code'])
        credentials = flow.credentials

        # Store the credentials
        token_data = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes,
            'expiry': credentials.expiry.isoformat() if credentials.expiry else None
        }

        self.token_storage.store_token(user_id, token_data)

        # Clear the state
        session.pop('google_auth_state', None)

        return {
            'user_id': user_id,
            'success': True
        }

    def get_credentials(self, user_id: str) -> Optional[Credentials]:
        """
        Get Google credentials for a user.

        Args:
            user_id: Unique identifier for the user

        Returns:
            Google Credentials object or None if not authenticated
        """
        token_data = self.token_storage.get_token(user_id)
        if not token_data:
            return None

        # Convert expiry string back to datetime
        if token_data.get('expiry'):
            expiry = datetime.fromisoformat(token_data['expiry'])
        else:
            expiry = None

        credentials = Credentials(
            token=token_data['token'],
            refresh_token=token_data['refresh_token'],
            token_uri=token_data['token_uri'],
            client_id=token_data['client_id'],
            client_secret=token_data['client_secret'],
            scopes=token_data['scopes'],
            expiry=expiry
        )

        # Check if token needs refresh
        if credentials.expired:
            try:
                credentials.refresh(requests.Request())

                # Update stored token with refreshed data
                token_data = {
                    'token': credentials.token,
                    'refresh_token': credentials.refresh_token or token_data['refresh_token'],
                    'token_uri': credentials.token_uri,
                    'client_id': credentials.client_id,
                    'client_secret': credentials.client_secret,
                    'scopes': credentials.scopes,
                    'expiry': credentials.expiry.isoformat() if credentials.expiry else None
                }
                self.token_storage.store_token(user_id, token_data)
            except Exception as e:
                current_app.logger.error(f"Error refreshing token for user {user_id}: {str(e)}")
                return None

        return credentials

    def revoke_access(self, user_id: str) -> bool:
        """
        Revoke Google access for a user.

        Args:
            user_id: Unique identifier for the user

        Returns:
            True if successful, False otherwise
        """
        token_data = self.token_storage.get_token(user_id)
        if not token_data:
            return True  # Already revoked

        try:
            # Revoke access token
            token = token_data['token']
            response = requests.post(
                'https://oauth2.googleapis.com/revoke',
                params={'token': token},
                headers={'content-type': 'application/x-www-form-urlencoded'}
            )

            # Remove stored token
            self.token_storage.delete_token(user_id)

            return response.status_code == 200
        except Exception as e:
            current_app.logger.error(f"Error revoking access for user {user_id}: {str(e)}")
            return False

    def _create_flow(self) -> Flow:
        """
        Create an OAuth flow instance.

        Returns:
            Flow object for OAuth process
        """
        with open(self.credentials_file, 'r') as f:
            client_config = json.load(f)

        redirect_uri = url_for('api_v1.calendar_auth_callback', _external=True)

        return Flow.from_client_config(
            client_config=client_config,
            scopes=self.SCOPES,
            redirect_uri=redirect_uri
        )


class GoogleTokenStorage:
    """
    Handles secure storage of Google OAuth tokens.

    This is a placeholder implementation using a file-based storage.
    In production, you should use a secure database with encryption.
    """

    def __init__(self):
        """Initialize the token storage."""
        self.storage_dir = os.path.join(current_app.config['INSTANCE_PATH'], 'google_tokens')
        os.makedirs(self.storage_dir, exist_ok=True)

    def store_token(self, user_id: str, token_data: Dict) -> None:
        """
        Store a token for a user.

        Args:
            user_id: Unique identifier for the user
            token_data: Token data to store
        """
        file_path = self._get_token_file_path(user_id)

        with open(file_path, 'w') as f:
            json.dump(token_data, f)

        # Secure the file
        os.chmod(file_path, 0o600)

    def get_token(self, user_id: str) -> Optional[Dict]:
        """
        Get the token for a user.

        Args:
            user_id: Unique identifier for the user

        Returns:
            Token data or None if not found
        """
        file_path = self._get_token_file_path(user_id)

        if not os.path.exists(file_path):
            return None

        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            current_app.logger.error(f"Error reading token for user {user_id}: {str(e)}")
            return None

    def delete_token(self, user_id: str) -> None:
        """
        Delete the token for a user.

        Args:
            user_id: Unique identifier for the user
        """
        file_path = self._get_token_file_path(user_id)

        if os.path.exists(file_path):
            os.remove(file_path)

    def _get_token_file_path(self, user_id: str) -> str:
        """
        Get the file path for a user's token.

        Args:
            user_id: Unique identifier for the user

        Returns:
            Path to the token file
        """
        # Sanitize user_id to prevent path traversal
        safe_user_id = user_id.replace('/', '_').replace('\\', '_')
        return os.path.join(self.storage_dir, f"{safe_user_id}.json")


class GoogleAuthHandler:
    """
    Handler for Google authentication and authorization.
    
    Provides a simplified interface for Flask routes to work with Google OAuth.
    """
    
    def __init__(self, credentials_file: Optional[str] = None):
        """
        Initialize the Google Auth Handler.
        
        Args:
            credentials_file: Path to the Google OAuth credentials JSON file.
                If None, uses the path from app config.
        """
        if credentials_file is None:
            credentials_file = current_app.config.get(
                'GOOGLE_CREDENTIALS_FILE',
                os.path.join(current_app.config['INSTANCE_PATH'], 'google_credentials.json')
            )
        
        self.oauth = GoogleOAuth(credentials_file)
    
    def get_auth_url(self, user_id: str) -> str:
        """
        Get the Google authorization URL for a user.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            Authorization URL for redirecting the user
        """
        return self.oauth.get_authorization_url(user_id)
    
    def process_callback(self, callback_data: Dict) -> Dict:
        """
        Process the OAuth callback from Google.
        
        Args:
            callback_data: Callback data from Google
            
        Returns:
            Dict with user ID and success status
            
        Raises:
            AuthenticationError: If authentication fails
        """
        return self.oauth.handle_callback(callback_data)
    
    def get_credentials(self, user_id: str) -> Optional[Credentials]:
        """
        Get Google credentials for a user.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            Google Credentials object or None if not authenticated
        """
        return self.oauth.get_credentials(user_id)
    
    def is_authenticated(self, user_id: str) -> bool:
        """
        Check if a user is authenticated with Google.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            True if authenticated, False otherwise
        """
        return self.oauth.get_credentials(user_id) is not None
    
    def revoke_access(self, user_id: str) -> bool:
        """
        Revoke Google access for a user.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            True if successful, False otherwise
        """
        return self.oauth.revoke_access(user_id)
