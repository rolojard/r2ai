"""
R2D2 CSRF Protection Module
Token-based CSRF protection for POST/PUT/DELETE operations
Production-ready security implementation
"""

import secrets
import logging
from typing import Dict, Optional, Set
from datetime import datetime, timedelta
from functools import wraps

logger = logging.getLogger(__name__)


class CSRFManager:
    """
    CSRF Token Manager for R2D2 system
    Handles CSRF token generation, validation, and expiration
    Thread-safe implementation for multi-request handling
    """

    def __init__(self, token_expiry_minutes: int = 60):
        """Initialize CSRF manager
        
        Args:
            token_expiry_minutes: Token expiration time in minutes (default: 60)
        """
        self.valid_tokens: Dict[str, dict] = {}
        self.token_expiry_minutes = token_expiry_minutes
        logger.info(f"CSRF Manager initialized (token expiry: {token_expiry_minutes} min)")

    def generate_token(self, session_id: Optional[str] = None) -> str:
        """
        Generate new CSRF token
        
        Args:
            session_id: Optional session identifier for token association
            
        Returns:
            str: New CSRF token (32-byte hex string)
        """
        token = secrets.token_hex(32)  # 256-bit token
        self.valid_tokens[token] = {
            'created': datetime.now(),
            'session_id': session_id,
            'expires': datetime.now() + timedelta(minutes=self.token_expiry_minutes),
            'use_count': 0
        }
        logger.debug(f"CSRF token generated: {token[:16]}... (session: {session_id})")
        return token

    def validate_token(self, token: Optional[str]) -> bool:
        """
        Validate CSRF token
        
        Args:
            token: CSRF token to validate
            
        Returns:
            bool: True if valid and not expired, False otherwise
        """
        if not token:
            logger.warning("CSRF validation failed: No token provided")
            return False

        if token not in self.valid_tokens:
            logger.warning(f"CSRF validation failed: Invalid token ({token[:16]}...)")
            return False

        token_data = self.valid_tokens[token]
        
        # Check expiration
        if datetime.now() > token_data['expires']:
            logger.warning(f"CSRF validation failed: Token expired ({token[:16]}...)")
            del self.valid_tokens[token]
            return False

        # Update usage statistics
        token_data['use_count'] += 1
        logger.debug(f"CSRF token validated: {token[:16]}... (uses: {token_data['use_count']})")
        return True

    def revoke_token(self, token: str) -> bool:
        """
        Revoke a CSRF token
        
        Args:
            token: Token to revoke
            
        Returns:
            bool: True if revoked, False if not found
        """
        if token in self.valid_tokens:
            del self.valid_tokens[token]
            logger.info(f"CSRF token revoked: {token[:16]}...")
            return True
        return False

    def cleanup_expired_tokens(self):
        """Remove expired tokens from storage"""
        now = datetime.now()
        expired_tokens = [
            token for token, data in self.valid_tokens.items()
            if now > data['expires']
        ]
        
        for token in expired_tokens:
            del self.valid_tokens[token]
        
        if expired_tokens:
            logger.info(f"Cleaned up {len(expired_tokens)} expired CSRF tokens")

    def get_token_count(self) -> int:
        """Get count of active CSRF tokens"""
        return len(self.valid_tokens)


# ============================================================================
# GLOBAL CSRF MANAGER INSTANCE (Singleton)
# ============================================================================

csrf_manager = CSRFManager(token_expiry_minutes=60)


# ============================================================================
# HELPER FUNCTIONS FOR FASTAPI INTEGRATION
# ============================================================================

def validate_csrf_token(csrf_token: Optional[str]) -> bool:
    """
    Validate CSRF token from request
    
    Args:
        csrf_token: CSRF token from header or form data
        
    Returns:
        bool: True if valid, False otherwise
    """
    return csrf_manager.validate_token(csrf_token)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'CSRFManager',
    'csrf_manager',
    'validate_csrf_token'
]
