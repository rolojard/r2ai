"""
R2D2 Authentication Module
Token-based authentication for WCB API and Vision WebSocket
Production-ready security implementation with UUID bearer tokens
"""

import uuid
import logging
import os
from functools import wraps
from typing import Dict, Optional, Callable, Set
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class AuthManager:
    """
    Authentication manager for R2D2 system
    Handles token generation, validation, and revocation
    Thread-safe singleton pattern for centralized auth management
    """

    def __init__(self):
        """Initialize authentication manager with persistent token"""
        self.valid_tokens: Dict[str, dict] = {}
        self.revoked_tokens: Set[str] = set()
        self.primary_token: Optional[str] = None
        self.load_or_create_initial_tokens()

    def load_or_create_initial_tokens(self):
        """Load tokens from environment or create initial persistent token"""
        # Check if token already set in environment
        existing_token = os.environ.get('R2D2_AUTH_TOKEN')

        if existing_token:
            # Use existing token from environment (most important!)
            self.primary_token = existing_token
            self.valid_tokens[existing_token] = {
                'created': datetime.now(),
                'active': True,
                'source': 'environment',
                'description': 'Persistent token from R2D2_AUTH_TOKEN'
            }
            logger.info(f"✅ Using existing R2D2_AUTH_TOKEN from environment: {existing_token[:8]}...")
            print(f"✅ Using existing R2D2_AUTH_TOKEN: {existing_token[:8]}...")
        else:
            # Generate NEW token and store in environment
            self.primary_token = str(uuid.uuid4())
            os.environ['R2D2_AUTH_TOKEN'] = self.primary_token
            self.valid_tokens[self.primary_token] = {
                'created': datetime.now(),
                'active': True,
                'source': 'generated',
                'description': 'Generated persistent token'
            }
            logger.info(f"✅ Generated new R2D2_AUTH_TOKEN: {self.primary_token}")
            print(f"✅ Generated new R2D2_AUTH_TOKEN: {self.primary_token}")
            logger.info("="*70)
            logger.info("R2D2 AUTHENTICATION INITIALIZED")
            logger.info("="*70)
            logger.info(f"Primary Token: {self.primary_token}")
            logger.info(f"Total Active Tokens: {len(self.valid_tokens)}")
            logger.info("="*70)
            logger.warning("SAVE THIS TOKEN - Required for all API/WebSocket requests")
            logger.info("="*70)

    def get_primary_token(self) -> str:
        """
        Get the primary token that should be used by all clients

        Returns:
            str: The primary authentication token
        """
        return self.primary_token

    def generate_token(self, description: str = "Generated token") -> str:
        """
        Generate new bearer token (UUID-based)

        Args:
            description: Token description for tracking

        Returns:
            str: New UUID-based token
        """
        token = str(uuid.uuid4())
        self.valid_tokens[token] = {
            'created': datetime.now(),
            'active': True,
            'source': 'generated',
            'description': description,
            'last_used': None,
            'use_count': 0
        }
        logger.info(f"New token generated: {token[:8]}... ({description})")
        return token

    def validate_token(self, token: Optional[str]) -> bool:
        """
        Validate if token is valid and active

        Args:
            token: Bearer token to validate

        Returns:
            bool: True if valid, False otherwise
        """
        if not token:
            logger.warning("Token validation failed: No token provided")
            return False

        # Check if token is revoked
        if token in self.revoked_tokens:
            logger.warning(f"Token validation failed: Token revoked ({token[:8]}...)")
            return False

        # Check if token exists and is active
        if token not in self.valid_tokens:
            logger.warning(f"Token validation failed: Invalid token ({token[:8]}...)")
            return False

        if not self.valid_tokens[token]['active']:
            logger.warning(f"Token validation failed: Token inactive ({token[:8]}...)")
            return False

        # Update usage statistics
        self.valid_tokens[token]['last_used'] = datetime.now()
        self.valid_tokens[token]['use_count'] += 1

        # Log validation success (debug level to avoid spam)
        logger.debug(f"Token validated: {token[:8]}... (uses: {self.valid_tokens[token]['use_count']})")
        return True

    def revoke_token(self, token: str) -> bool:
        """
        Revoke a token permanently

        Args:
            token: Token to revoke

        Returns:
            bool: True if revoked, False if not found
        """
        if token in self.valid_tokens:
            self.valid_tokens[token]['active'] = False
            self.revoked_tokens.add(token)
            logger.info(f"Token revoked: {token[:8]}...")
            return True

        logger.warning(f"Cannot revoke token: Not found ({token[:8]}...)")
        return False

    def get_token_info(self, token: str) -> Optional[Dict]:
        """
        Get information about a token

        Args:
            token: Token to query

        Returns:
            dict: Token information or None if not found
        """
        if token in self.valid_tokens:
            info = self.valid_tokens[token].copy()
            # Convert datetime to ISO format
            info['created'] = info['created'].isoformat()
            if info['last_used']:
                info['last_used'] = info['last_used'].isoformat()
            return info
        return None

    def list_active_tokens(self) -> list:
        """
        List all active tokens (for admin purposes)

        Returns:
            list: List of active token information (partial tokens for security)
        """
        active_tokens = []
        for token, info in self.valid_tokens.items():
            if info['active']:
                active_tokens.append({
                    'token_prefix': token[:8] + '...',
                    'created': info['created'].isoformat(),
                    'description': info['description'],
                    'use_count': info['use_count'],
                    'last_used': info['last_used'].isoformat() if info['last_used'] else None
                })
        return active_tokens

    def extract_bearer_token(self, auth_header: Optional[str]) -> Optional[str]:
        """
        Extract bearer token from Authorization header

        Args:
            auth_header: Authorization header value

        Returns:
            str: Extracted token or None if invalid format
        """
        if not auth_header:
            return None

        if not auth_header.startswith('Bearer '):
            logger.warning(f"Invalid auth header format: {auth_header[:20]}...")
            return None

        return auth_header[7:].strip()  # Remove 'Bearer ' prefix

    def require_auth(self, func: Callable):
        """
        Decorator for auth-required endpoints (FastAPI compatible)

        Usage:
            @auth_manager.require_auth
            async def protected_endpoint(request):
                ...
        """
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request object (varies by framework)
            # This is a generic implementation
            request = None
            for arg in args:
                if hasattr(arg, 'headers'):
                    request = arg
                    break

            if not request:
                logger.error("Cannot extract request from decorator arguments")
                raise Exception("Authentication decorator misconfigured")

            # Extract and validate token
            auth_header = request.headers.get('Authorization', '')
            token = self.extract_bearer_token(auth_header)

            if not self.validate_token(token):
                logger.warning(f"Unauthorized access attempt to {func.__name__}")
                raise Exception("Unauthorized")  # Framework should catch this

            # Call original function
            return await func(*args, **kwargs)

        return wrapper


# ============================================================================
# GLOBAL AUTH MANAGER INSTANCE (Singleton)
# ============================================================================

auth_manager = AuthManager()


# ============================================================================
# HELPER FUNCTIONS FOR COMMON USE CASES
# ============================================================================

def validate_websocket_token(headers: dict) -> bool:
    """
    Validate WebSocket connection token from headers

    Args:
        headers: WebSocket request headers

    Returns:
        bool: True if authenticated, False otherwise
    """
    auth_header = headers.get('Authorization', headers.get('authorization', ''))
    token = auth_manager.extract_bearer_token(auth_header)
    return auth_manager.validate_token(token)


def validate_api_token(auth_header: Optional[str]) -> bool:
    """
    Validate API request token

    Args:
        auth_header: Authorization header value

    Returns:
        bool: True if authenticated, False otherwise
    """
    token = auth_manager.extract_bearer_token(auth_header)
    return auth_manager.validate_token(token)


def get_current_token(auth_header: Optional[str]) -> Optional[str]:
    """
    Extract and validate token, returning the token itself

    Args:
        auth_header: Authorization header value

    Returns:
        str: Valid token or None
    """
    token = auth_manager.extract_bearer_token(auth_header)
    if auth_manager.validate_token(token):
        return token
    return None


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'AuthManager',
    'auth_manager',
    'validate_websocket_token',
    'validate_api_token',
    'get_current_token'
]
