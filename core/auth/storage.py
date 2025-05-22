# core/auth/storage.py
import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import cryptography.fernet
from cryptography.fernet import Fernet

from ..logging import get_logger
from .tokens import TokenModel as Token, TokenScope

logger = get_logger(__name__)

class TokenStorage:
    """
    Secure storage for API tokens.
    
    This class handles the storage and retrieval of API tokens,
    with encryption for sensitive token data.
    """
    
    def __init__(self, db_path: str, encryption_key: Optional[str] = None):
        """
        Initialize the token storage.
        
        Args:
            db_path: Path to the SQLite database file
            encryption_key: Key for encrypting token values (generated if not provided)
        """
        self.db_path = db_path
        self.encryption_key = encryption_key
        
        # Create encryption key if not provided
        if not self.encryption_key:
            key_path = Path(db_path).with_suffix('.key')
            if os.path.exists(key_path):
                with open(key_path, 'rb') as key_file:
                    self.encryption_key = key_file.read()
            else:
                self.encryption_key = Fernet.generate_key()
                with open(key_path, 'wb') as key_file:
                    key_file.write(self.encryption_key)
                # Secure the key file
                os.chmod(key_path, 0o600)
        
        self.cipher = Fernet(self.encryption_key)
        self._initialize_db()
    
    def _initialize_db(self) -> None:
        """Initialize the database schema."""
        # Create the database directory if it doesn't exist
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tokens table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tokens (
            token_id TEXT PRIMARY KEY,
            token_value TEXT NOT NULL,
            description TEXT NOT NULL,
            scope TEXT NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT,
            last_used_at TEXT
        )
        ''')
        
        conn.commit()
        conn.close()
        
        # Secure the database file
        try:
            os.chmod(self.db_path, 0o600)
        except:
            logger.warning(f"Could not set secure permissions on database file: {self.db_path}")
    
    def _encrypt_token(self, token_value: str) -> str:
        """
        Encrypt a token value.
        
        Args:
            token_value: The token value to encrypt
            
        Returns:
            Encrypted token value
        """
        return self.cipher.encrypt(token_value.encode()).decode()
    
    def _decrypt_token(self, encrypted_token: str) -> str:
        """
        Decrypt a token value.
        
        Args:
            encrypted_token: The encrypted token value
            
        Returns:
            Decrypted token value
        """
        return self.cipher.decrypt(encrypted_token.encode()).decode()
    
    def add_token(self, token: Token) -> None:
        """
        Add a token to storage.
        
        Args:
            token: The token to add
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Encrypt the token value
        encrypted_token = self._encrypt_token(token.token_value)
        
        cursor.execute(
            '''
            INSERT INTO tokens (
                token_id, token_value, description, scope, 
                created_at, expires_at, last_used_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                token.token_id,
                encrypted_token,
                token.description,
                json.dumps([s.value for s in token.scope]),
                token.created_at.isoformat() if token.created_at else None,
                token.expires_at.isoformat() if token.expires_at else None,
                token.last_used_at.isoformat() if token.last_used_at else None,
            )
        )
        
        conn.commit()
        conn.close()
    
    def get_token(self, token_id: str) -> Optional[Token]:
        """
        Get a token by ID.
        
        Args:
            token_id: The token ID
            
        Returns:
            The token if found, None otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM tokens WHERE token_id = ?", (token_id,))
        row = cursor.fetchone()
        
        conn.close()
        
        if not row:
            return None
        
        return self._row_to_token(row)
    
    def get_token_by_value(self, token_value: str) -> Optional[Token]:
        """
        Get a token by its value.
        
        Args:
            token_value: The token value
            
        Returns:
            The token if found, None otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM tokens")
        rows = cursor.fetchall()
        
        conn.close()
        
        for row in rows:
            encrypted_token = row[1]
            try:
                decrypted_token = self._decrypt_token(encrypted_token)
                if decrypted_token == token_value:
                    return self._row_to_token(row)
            except (cryptography.fernet.InvalidToken, Exception) as e:
                logger.warning(f"Error decrypting token: {e}")
                continue
        
        return None
    
    def list_tokens(self) -> List[Token]:
        """
        List all tokens.
        
        Returns:
            List of all tokens
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM tokens")
        rows = cursor.fetchall()
        
        conn.close()
        
        return [self._row_to_token(row) for row in rows]
    
    def update_token(self, token: Token) -> None:
        """
        Update a token.
        
        Args:
            token: The token to update
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Encrypt the token value
        encrypted_token = self._encrypt_token(token.token_value)
        
        cursor.execute(
            '''
            UPDATE tokens SET
                token_value = ?,
                description = ?,
                scope = ?,
                expires_at = ?,
                last_used_at = ?
            WHERE token_id = ?
            ''',
            (
                encrypted_token,
                token.description,
                json.dumps([s.value for s in token.scope]),
                token.expires_at.isoformat() if token.expires_at else None,
                token.last_used_at.isoformat() if token.last_used_at else None,
                token.token_id,
            )
        )
        
        conn.commit()
        conn.close()
    
    def delete_token(self, token_id: str) -> bool:
        """
        Delete a token.
        
        Args:
            token_id: The token ID
            
        Returns:
            True if the token was deleted, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM tokens WHERE token_id = ?", (token_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return deleted
    
    def _row_to_token(self, row: tuple) -> Token:
        """
        Convert a database row to a token.
        
        Args:
            row: Database row
            
        Returns:
            Token object
        """
        token_id, encrypted_token, description, scope_json, created_at, expires_at, last_used_at = row
        
        # Decrypt the token value
        token_value = self._decrypt_token(encrypted_token)
        
        # Parse the scope
        scope = [TokenScope(s) for s in json.loads(scope_json)]
        
        # Create the token
        token_data = {
            "token_id": token_id,
            "token_value": token_value,
            "description": description,
            "scope": scope,
            "created_at": created_at,
            "expires_at": expires_at,
            "last_used_at": last_used_at,
        }
        
        return Token.from_dict(token_data)


# Default token storage instance
_default_storage = None


def get_default_token_storage() -> TokenStorage:
    """
    Get the default token storage instance.
    
    Creates a new instance if one doesn't exist.
    
    Returns:
        The default token storage instance
    """
    global _default_storage
    
    if _default_storage is None:
        # Get data directory from environment or use default
        data_dir = os.environ.get(
            'FLASK_DATA_DIR', 
            os.path.join(os.path.expanduser('~'), '.flaskllm')
        )
        
        # Create default storage with SQLite database in data directory
        db_path = os.path.join(data_dir, 'tokens.db')
        _default_storage = TokenStorage(db_path)
        
        logger.info(f"Initialized default token storage at {db_path}")
    
    return _default_storage
