#!/usr/bin/env python3
"""
R2D2 Authentication System
Production-ready token-based authentication for API endpoints and WebSocket connections
Supports UUID-based bearer tokens with extensibility for JWT in future

Security Features:
- Bearer token authentication
- Token generation and validation
- Environment variable support for API keys
- Token revocation support
- Request/response logging for security audits
- Rate limiting ready (decorator-based)
"""

import os
import uuid
import time
import logging
from typing import Dict, Optional, Set, Callable
from functools import wraps
from datetime import datetime, timedelta

# FastAPI imports (for WCB API)
try:
    from fastapi import HTTPException, status, Request
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    HTTPException = None
    status = None
    Request = None

# WebSocket imports (for Vision system)
try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# TOKEN STORAGE AND MANAGEMENT
# ============================================================================

class TokenStore:
    """
    In-memory token storage with metadata tracking
    Production upgrade path: Replace with Redis or database backend
    """

    def __init__(self):
        # Token storage: {token: metadata}
        self._tokens: Dict[str, Dict] = {}

        # Revoked tokens (for invalidation)
        self._revoked_tokens: Set[str] = set()

        # Token metadata tracking
        self._token_metadata: Dict[str, Dict] = {}

        # Lock for thread safety (future enhancement)
        # self._lock = threading.Lock()

    def add_token(self, token: str, metadata: Optional[Dict] = None) -> None:
        """
        Add token to valid token store

        Args:
            token: Token string
            metadata: Optional metadata (created_at, expires_at, scope, etc.)
        """
        if metadata is None:
            metadata = {}

        # Add default metadata
        metadata.setdefault('created_at', datetime.now().isoformat())
        metadata.setdefault('last_used', None)
        metadata.setdefault('usage_count', 0)
        metadata.setdefault('scope', 'full_access')  # Future: role-based access

        self._tokens[token] = metadata
        logger.info(f"Token added: {token[:8]}... (scope: {metadata.get('scope', 'unknown')})")

    def validate_token(self, token: str) -> bool:
        """
        Validate token exists and is not revoked

        Args:
            token: Token to validate

        Returns:
            True if token is valid, False otherwise
        """
        # Check if token is revoked
        if token in self._revoked_tokens:
            logger.warning(f"Revoked token attempted: {token[:8]}...")
            return False

        # Check if token exists
        if token not in self._tokens:
            logger.warning(f"Invalid token attempted: {token[:8]}...")
            return False

        # Update usage metadata
        self._tokens[token]['last_used'] = datetime.now().isoformat()
        self._tokens[token]['usage_count'] += 1

        return True

    def revoke_token(self, token: str) -> bool:
        """
        Revoke a token (invalidate it)

        Args:
            token: Token to revoke

        Returns:
            True if token was revoked, False if not found
        """
        if token in self._tokens:
            self._revoked_tokens.add(token)
            logger.info(f"Token revoked: {token[:8]}...")
            return True
        return False

    def get_token_metadata(self, token: str) -> Optional[Dict]:
        """Get metadata for a token"""
        return self._tokens.get(token)

    def list_active_tokens(self) -> Dict[str, Dict]:
        """List all active (non-revoked) tokens with metadata"""
        return {
            token: metadata
            for token, metadata in self._tokens.items()
            if token not in self._revoked_tokens
        }

    def cleanup_expired_tokens(self) -> int:
        """
        Remove expired tokens from storage
        Future enhancement: Add expiration support

        Returns:
            Number of tokens cleaned up
        """
        # Placeholder for future expiration logic
        return 0


# ============================================================================
# AUTHENTICATION MANAGER
# ============================================================================

class AuthManager:
    """
    Central authentication manager for R2D2 system
    Handles token generation, validation, and security enforcement
    """

    def __init__(self, enable_env_token: bool = True):
        """
        Initialize authentication manager

        Args:
            enable_env_token: Load API_KEY from environment variable
        """
        self.token_store = TokenStore()
        self.security_events: list = []
        self.max_security_events = 1000  # Keep last 1000 events

        # Load environment token if enabled
        if enable_env_token:
            env_token = os.getenv('R2D2_API_KEY')
            if env_token:
                self.token_store.add_token(env_token, {
                    'source': 'environment',
                    'scope': 'full_access',
                    'created_at': datetime.now().isoformat()
                })
                logger.info(f"Loaded API key from environment: {env_token[:8]}...")
            else:
                logger.warning("R2D2_API_KEY environment variable not set")

    def generate_token(self, metadata: Optional[Dict] = None) -> str:
        """
        Generate new authentication token

        Args:
            metadata: Optional metadata to associate with token

        Returns:
            Generated token string
        """
        token = str(uuid.uuid4())

        if metadata is None:
            metadata = {}

        metadata['source'] = metadata.get('source', 'generated')

        self.token_store.add_token(token, metadata)

        self._log_security_event('token_generated', {
            'token_prefix': token[:8],
            'timestamp': datetime.now().isoformat()
        })

        logger.info(f"Generated new token: {token[:8]}...")
        return token

    def validate_token(self, token: str) -> bool:
        """
        Validate authentication token

        Args:
            token: Token to validate

        Returns:
            True if valid, False otherwise
        """
        is_valid = self.token_store.validate_token(token)

        self._log_security_event(
            'token_validation',
            {
                'token_prefix': token[:8] if token else 'none',
                'valid': is_valid,
                'timestamp': datetime.now().isoformat()
            }
        )

        return is_valid

    def revoke_token(self, token: str) -> bool:
        """
        Revoke a token

        Args:
            token: Token to revoke

        Returns:
            True if revoked successfully
        """
        revoked = self.token_store.revoke_token(token)

        if revoked:
            self._log_security_event('token_revoked', {
                'token_prefix': token[:8],
                'timestamp': datetime.now().isoformat()
            })

        return revoked

    def extract_bearer_token(self, auth_header: str) -> Optional[str]:
        """
        Extract token from Authorization header

        Args:
            auth_header: Authorization header value (e.g., "Bearer {token}")

        Returns:
            Extracted token or None if invalid format
        """
        if not auth_header:
            return None

        parts = auth_header.split()

        if len(parts) != 2 or parts[0].lower() != 'bearer':
            logger.warning(f"Invalid authorization header format: {auth_header[:20]}...")
            return None

        return parts[1]

    def _log_security_event(self, event_type: str, data: Dict) -> None:
        """Log security event for audit trail"""
        event = {
            'type': event_type,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }

        self.security_events.append(event)

        # Keep only recent events
        if len(self.security_events) > self.max_security_events:
            self.security_events = self.security_events[-self.max_security_events:]

    def get_security_events(self, limit: int = 100) -> list:
        """Get recent security events for audit"""
        return self.security_events[-limit:]

    def get_stats(self) -> Dict:
        """Get authentication statistics"""
        active_tokens = self.token_store.list_active_tokens()

        return {
            'active_tokens': len(active_tokens),
            'revoked_tokens': len(self.token_store._revoked_tokens),
            'total_security_events': len(self.security_events),
            'token_usage': {
                token[:8]: metadata.get('usage_count', 0)
                for token, metadata in active_tokens.items()
            }
        }


# ============================================================================
# FASTAPI AUTHENTICATION DECORATORS AND DEPENDENCIES
# ============================================================================

# Global auth manager instance
auth_manager = AuthManager()

if FASTAPI_AVAILABLE:
    # FastAPI security scheme
    bearer_scheme = HTTPBearer(auto_error=False)

    async def get_current_token(
        credentials: HTTPAuthorizationCredentials = None
    ) -> str:
        """
        FastAPI dependency for token authentication

        Args:
            credentials: HTTP Authorization credentials

        Returns:
            Valid token string

        Raises:
            HTTPException: 401 if authentication fails
        """
        # Check if credentials provided
        if credentials is None:
            logger.warning("Authentication failed: No credentials provided")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required. Provide valid Bearer token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = credentials.credentials

        # Validate token
        if not auth_manager.validate_token(token):
            logger.warning(f"Authentication failed: Invalid token {token[:8]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authentication token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        auth_manager._log_security_event('api_auth_success', {
            'token_prefix': token[:8],
            'timestamp': datetime.now().isoformat()
        })

        return token

    def require_auth(func):
        """
        Decorator for FastAPI endpoints requiring authentication

        Usage:
            @app.get("/api/protected")
            @require_auth
            async def protected_endpoint():
                return {"message": "Authenticated!"}
        """
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get request object from kwargs
            request = kwargs.get('request')

            if not request:
                # Try to find request in args
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request object not found in endpoint"
                )

            # Extract authorization header
            auth_header = request.headers.get('Authorization')

            if not auth_header:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authorization header missing. Provide Bearer token.",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Extract and validate token
            token = auth_manager.extract_bearer_token(auth_header)

            if not token or not auth_manager.validate_token(token):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired authentication token.",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Call original function
            return await func(*args, **kwargs)

        return wrapper


# ============================================================================
# WEBSOCKET AUTHENTICATION UTILITIES
# ============================================================================

class WebSocketAuthError(Exception):
    """WebSocket authentication error"""
    pass


async def authenticate_websocket(websocket, auth_manager_instance: AuthManager = None) -> bool:
    """
    Authenticate WebSocket connection

    Args:
        websocket: WebSocket connection object
        auth_manager_instance: Optional auth manager instance (uses global if None)

    Returns:
        True if authenticated successfully

    Raises:
        WebSocketAuthError: If authentication fails
    """
    if auth_manager_instance is None:
        auth_manager_instance = auth_manager

    try:
        # Request authentication on connection
        # Client should send: {"type": "auth", "token": "bearer_token"}

        # Check for Authorization header in initial handshake
        if hasattr(websocket, 'request_headers'):
            auth_header = websocket.request_headers.get('Authorization')

            if auth_header:
                token = auth_manager_instance.extract_bearer_token(auth_header)

                if token and auth_manager_instance.validate_token(token):
                    logger.info(f"WebSocket authenticated via header: {token[:8]}...")
                    return True

        # Alternative: Wait for auth message from client
        # This allows client-side authentication after connection
        logger.warning("WebSocket authentication: No valid Authorization header found")

        # For now, return False to close connection
        # Future: Implement auth message exchange
        raise WebSocketAuthError("Authentication required. Provide Authorization header with Bearer token.")

    except Exception as e:
        logger.error(f"WebSocket authentication error: {e}")
        raise WebSocketAuthError(f"Authentication failed: {str(e)}")


def validate_websocket_auth_header(auth_header: Optional[str],
                                   auth_manager_instance: AuthManager = None) -> bool:
    """
    Validate WebSocket authentication header

    Args:
        auth_header: Authorization header value
        auth_manager_instance: Optional auth manager instance

    Returns:
        True if valid, False otherwise
    """
    if auth_manager_instance is None:
        auth_manager_instance = auth_manager

    if not auth_header:
        return False

    token = auth_manager_instance.extract_bearer_token(auth_header)

    if not token:
        return False

    return auth_manager_instance.validate_token(token)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def generate_test_token() -> str:
    """
    Generate a test token for development/testing
    Automatically adds to global auth manager

    Returns:
        Generated test token
    """
    token = auth_manager.generate_token({
        'source': 'test',
        'scope': 'full_access',
        'description': 'Development/testing token'
    })

    print("="*80)
    print("TEST TOKEN GENERATED")
    print("="*80)
    print(f"Token: {token}")
    print(f"Usage: Authorization: Bearer {token}")
    print("="*80)

    return token


def revoke_all_tokens() -> int:
    """
    Revoke all active tokens (emergency use)

    Returns:
        Number of tokens revoked
    """
    active_tokens = auth_manager.token_store.list_active_tokens()
    count = 0

    for token in active_tokens.keys():
        if auth_manager.revoke_token(token):
            count += 1

    logger.warning(f"EMERGENCY: Revoked all {count} active tokens")
    return count


def print_auth_stats() -> None:
    """Print authentication statistics"""
    stats = auth_manager.get_stats()

    print("\n" + "="*80)
    print("R2D2 AUTHENTICATION STATISTICS")
    print("="*80)
    print(f"Active Tokens: {stats['active_tokens']}")
    print(f"Revoked Tokens: {stats['revoked_tokens']}")
    print(f"Security Events: {stats['total_security_events']}")
    print("\nToken Usage:")
    for token_prefix, usage_count in stats['token_usage'].items():
        print(f"  {token_prefix}...: {usage_count} requests")
    print("="*80 + "\n")


# ============================================================================
# INITIALIZATION AND STARTUP
# ============================================================================

def initialize_auth_system(generate_initial_token: bool = True) -> Optional[str]:
    """
    Initialize authentication system on startup

    Args:
        generate_initial_token: Whether to generate an initial token

    Returns:
        Initial token if generated, None otherwise
    """
    logger.info("="*80)
    logger.info("Initializing R2D2 Authentication System")
    logger.info("="*80)

    # Check for environment token
    env_token = os.getenv('R2D2_API_KEY')
    if env_token:
        logger.info(f"✅ Environment token loaded: {env_token[:8]}...")
    else:
        logger.warning("⚠️  No R2D2_API_KEY environment variable found")

    # Generate initial token if requested
    initial_token = None
    if generate_initial_token:
        initial_token = generate_test_token()

    logger.info("="*80)
    logger.info("Authentication system initialized successfully")
    logger.info("="*80)

    return initial_token


# ============================================================================
# MAIN (for testing and token generation)
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='R2D2 Authentication System - Token Management',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--generate', '-g',
        action='store_true',
        help='Generate a new authentication token'
    )

    parser.add_argument(
        '--validate', '-v',
        type=str,
        help='Validate a token'
    )

    parser.add_argument(
        '--stats', '-s',
        action='store_true',
        help='Print authentication statistics'
    )

    parser.add_argument(
        '--revoke', '-r',
        type=str,
        help='Revoke a specific token'
    )

    args = parser.parse_args()

    # Initialize system
    initialize_auth_system(generate_initial_token=False)

    if args.generate:
        generate_test_token()

    if args.validate:
        is_valid = auth_manager.validate_token(args.validate)
        print(f"\nToken {args.validate[:8]}... is {'VALID' if is_valid else 'INVALID'}\n")

    if args.revoke:
        revoked = auth_manager.revoke_token(args.revoke)
        print(f"\nToken {args.revoke[:8]}... {'REVOKED' if revoked else 'NOT FOUND'}\n")

    if args.stats:
        print_auth_stats()

    # If no args, generate a token
    if not any([args.generate, args.validate, args.stats, args.revoke]):
        print("\nNo arguments provided. Generating test token...\n")
        generate_test_token()
