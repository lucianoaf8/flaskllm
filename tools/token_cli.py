# tools/token_cli.py
#!/usr/bin/env python3
"""
Token Management CLI

This script provides a command-line interface for managing API tokens.
"""
import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Updated imports to use the core.auth module
from core.auth import TokenModel as Token, TokenScope, TokenService, TokenStorage


def create_token(
    storage: TokenStorage,
    description: str,
    scopes: List[str],
    expires_in_days: Optional[int] = None,
) -> Token:
    """
    Create a new token.
    
    Args:
        storage: Token storage
        description: Token description
        scopes: Token scopes
        expires_in_days: Days until token expires
        
    Returns:
        The created token
    """
    # Convert scope strings to enum values
    token_scopes = []
    for scope in scopes:
        try:
            token_scopes.append(TokenScope(scope))
        except ValueError:
            print(f"Invalid scope: {scope}")
            print(f"Valid scopes: {[s.value for s in TokenScope]}")
            sys.exit(1)
    
    token_service = TokenService(storage)
    token = token_service.create_token(
        description=description,
        scope=token_scopes,
        expires_in_days=expires_in_days
    )
    
    return token


def list_tokens(storage: TokenStorage) -> List[Token]:
    """
    List all tokens.
    
    Args:
        storage: Token storage
        
    Returns:
        List of tokens
    """
    token_service = TokenService(storage)
    return token_service.list_tokens()


def revoke_token(storage: TokenStorage, token_id: str) -> bool:
    """
    Revoke a token.
    
    Args:
        storage: Token storage
        token_id: Token ID
        
    Returns:
        True if token was revoked, False otherwise
    """
    token_service = TokenService(storage)
    return token_service.revoke_token(token_id)


def rotate_token(
    storage: TokenStorage, token_id: str, expiration_days: int
) -> Optional[Token]:
    """
    Rotate a token.
    
    Args:
        storage: Token storage
        token_id: Token ID
        expiration_days: Days until old token expires
        
    Returns:
        New token if rotation was successful, None otherwise
    """
    token_service = TokenService(storage)
    return token_service.rotate_token(token_id, expiration_days)


def main() -> None:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="Token Management CLI")
    
    # Common arguments
    parser.add_argument(
        "--db-path",
        dest="db_path",
        help="Path to the token database",
        default=os.environ.get("TOKEN_DB_PATH", "data/tokens.db")
    )
    parser.add_argument(
        "--encryption-key",
        dest="encryption_key",
        help="Encryption key for token storage",
        default=os.environ.get("TOKEN_ENCRYPTION_KEY")
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new token")
    create_parser.add_argument(
        "--description", "-d", required=True, help="Token description"
    )
    create_parser.add_argument(
        "--scope", "-s", 
        action="append", 
        default=["read", "write"],
        help="Token scope (can be specified multiple times)"
    )
    create_parser.add_argument(
        "--expires-in", "-e", 
        type=int, 
        help="Days until token expires"
    )
    
    # List command
    list_parser = subparsers.add_parser("list", help="List all tokens")
    list_parser.add_argument(
        "--json", "-j", 
        action="store_true", 
        help="Output as JSON"
    )
    
    # Revoke command
    revoke_parser = subparsers.add_parser("revoke", help="Revoke a token")
    revoke_parser.add_argument(
        "token_id", help="ID of the token to revoke"
    )
    
    # Rotate command
    rotate_parser = subparsers.add_parser("rotate", help="Rotate a token")
    rotate_parser.add_argument(
        "token_id", help="ID of the token to rotate"
    )
    rotate_parser.add_argument(
        "--expiration-days", "-e", 
        type=int, 
        default=30,
        help="Days until old token expires"
    )
    
    args = parser.parse_args()
    
    # Initialize token storage
    storage = TokenStorage(args.db_path, args.encryption_key)
    
    # Execute command
    if args.command == "create":
        token = create_token(
            storage, 
            args.description, 
            args.scope, 
            args.expires_in
        )
        
        print(f"Token created successfully!")
        print(f"Token ID: {token.token_id}")
        print(f"Token value: {token.token_value}")
        print(f"Description: {token.description}")
        print(f"Scope: {[s.value for s in token.scope]}")
        print(f"Created at: {token.created_at}")
        print(f"Expires at: {token.expires_at or 'Never'}")
        
    elif args.command == "list":
        tokens = list_tokens(storage)
        
        if args.json:
            token_data = [token.to_dict() for token in tokens]
            # Mask token values
            for data in token_data:
                if data.get("token_value"):
                    data["token_value"] = "****" + data["token_value"][-4:]
            print(json.dumps(token_data, indent=2))
        else:
            print(f"Found {len(tokens)} tokens:")
            for token in tokens:
                expired = " (EXPIRED)" if token.is_expired else ""
                expires_at = token.expires_at or "Never"
                print(f"- {token.token_id}: {token.description}{expired}")
                print(f"  Scope: {[s.value for s in token.scope]}")
                print(f"  Created: {token.created_at}")
                print(f"  Expires: {expires_at}")
                print(f"  Last used: {token.last_used_at or 'Never'}")
                if token.token_value:
                    masked_value = "****" + token.token_value[-4:]
                    print(f"  Value: {masked_value}")
                print()
        
    elif args.command == "revoke":
        success = revoke_token(storage, args.token_id)
        if success:
            print(f"Token {args.token_id} revoked successfully")
        else:
            print(f"Token {args.token_id} not found")
            sys.exit(1)
        
    elif args.command == "rotate":
        new_token = rotate_token(storage, args.token_id, args.expiration_days)
        if new_token:
            print(f"Token rotated successfully!")
            print(f"Old token ID: {args.token_id}")
            print(f"New token ID: {new_token.token_id}")
            print(f"New token value: {new_token.token_value}")
            print(f"Description: {new_token.description}")
            print(f"Scope: {[s.value for s in new_token.scope]}")
            print(f"Created at: {new_token.created_at}")
            print(f"Old token expires in {args.expiration_days} days")
        else:
            print(f"Token {args.token_id} not found")
            sys.exit(1)
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()