#!/usr/bin/env python3
"""
R2D2 Authentication System Test Suite
Comprehensive testing for token-based authentication
Tests token generation, validation, revocation, and API/WebSocket security
"""

import unittest
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from r2d2_auth_module import (
    AuthManager,
    auth_manager,
    validate_websocket_token,
    validate_api_token,
    get_current_token
)


class TestAuthenticationTokenManagement(unittest.TestCase):
    """Test suite for authentication token management"""

    def setUp(self):
        """Set up test fixtures"""
        self.auth = AuthManager()

    def test_token_generation(self):
        """Test token generation creates valid UUIDs"""
        token = self.auth.generate_token(description="Test token")
        self.assertIsNotNone(token)
        self.assertIsInstance(token, str)
        self.assertEqual(len(token), 36)  # UUID length with dashes
        self.assertIn('-', token)  # UUID format

    def test_token_validation_valid(self):
        """Test valid token is accepted"""
        token = self.auth.generate_token(description="Valid test token")
        self.assertTrue(self.auth.validate_token(token))

    def test_token_validation_invalid(self):
        """Test invalid token is rejected"""
        invalid_token = "invalid_token_12345_not_a_uuid"
        self.assertFalse(self.auth.validate_token(invalid_token))

    def test_token_validation_missing(self):
        """Test missing token is rejected"""
        self.assertFalse(self.auth.validate_token(None))
        self.assertFalse(self.auth.validate_token(""))
        self.assertFalse(self.auth.validate_token("   "))

    def test_token_revocation(self):
        """Test token revocation works correctly"""
        token = self.auth.generate_token(description="Token to revoke")

        # Verify token is valid
        self.assertTrue(self.auth.validate_token(token))

        # Revoke token
        result = self.auth.revoke_token(token)
        self.assertTrue(result)

        # Verify token is now invalid
        self.assertFalse(self.auth.validate_token(token))

    def test_token_revocation_nonexistent(self):
        """Test revoking non-existent token returns False"""
        fake_token = "00000000-0000-0000-0000-000000000000"
        result = self.auth.revoke_token(fake_token)
        self.assertFalse(result)

    def test_multiple_tokens_independent(self):
        """Test multiple tokens work independently"""
        token1 = self.auth.generate_token(description="Token 1")
        token2 = self.auth.generate_token(description="Token 2")
        token3 = self.auth.generate_token(description="Token 3")

        # All tokens valid
        self.assertTrue(self.auth.validate_token(token1))
        self.assertTrue(self.auth.validate_token(token2))
        self.assertTrue(self.auth.validate_token(token3))

        # Revoke token1
        self.auth.revoke_token(token1)

        # token1 invalid, others still valid
        self.assertFalse(self.auth.validate_token(token1))
        self.assertTrue(self.auth.validate_token(token2))
        self.assertTrue(self.auth.validate_token(token3))

        # Revoke token3
        self.auth.revoke_token(token3)

        # token2 still valid
        self.assertFalse(self.auth.validate_token(token1))
        self.assertTrue(self.auth.validate_token(token2))
        self.assertFalse(self.auth.validate_token(token3))


class TestBearerTokenExtraction(unittest.TestCase):
    """Test suite for bearer token extraction"""

    def setUp(self):
        """Set up test fixtures"""
        self.auth = AuthManager()

    def test_extract_bearer_token_valid(self):
        """Test extracting valid bearer token"""
        token = "12345678-1234-5678-1234-567812345678"
        auth_header = f"Bearer {token}"

        extracted = self.auth.extract_bearer_token(auth_header)
        self.assertEqual(extracted, token)

    def test_extract_bearer_token_with_whitespace(self):
        """Test extracting bearer token with extra whitespace"""
        token = "12345678-1234-5678-1234-567812345678"
        auth_header = f"Bearer    {token}   "

        extracted = self.auth.extract_bearer_token(auth_header)
        self.assertEqual(extracted, token)

    def test_extract_bearer_token_missing_prefix(self):
        """Test extraction fails without Bearer prefix"""
        token = "12345678-1234-5678-1234-567812345678"
        auth_header = token  # No "Bearer " prefix

        extracted = self.auth.extract_bearer_token(auth_header)
        self.assertIsNone(extracted)

    def test_extract_bearer_token_wrong_prefix(self):
        """Test extraction fails with wrong prefix"""
        token = "12345678-1234-5678-1234-567812345678"
        auth_header = f"Basic {token}"  # Wrong auth type

        extracted = self.auth.extract_bearer_token(auth_header)
        self.assertIsNone(extracted)

    def test_extract_bearer_token_empty(self):
        """Test extraction fails with empty header"""
        extracted = self.auth.extract_bearer_token("")
        self.assertIsNone(extracted)

        extracted = self.auth.extract_bearer_token(None)
        self.assertIsNone(extracted)


class TestTokenUsageTracking(unittest.TestCase):
    """Test suite for token usage tracking"""

    def setUp(self):
        """Set up test fixtures"""
        self.auth = AuthManager()

    def test_token_usage_count(self):
        """Test token usage is tracked"""
        token = self.auth.generate_token(description="Usage test token")

        # Get initial info
        info = self.auth.get_token_info(token)
        self.assertEqual(info['use_count'], 0)
        self.assertIsNone(info['last_used'])

        # Use token
        self.auth.validate_token(token)

        # Check updated info
        info = self.auth.get_token_info(token)
        self.assertEqual(info['use_count'], 1)
        self.assertIsNotNone(info['last_used'])

        # Use token again
        self.auth.validate_token(token)
        self.auth.validate_token(token)

        # Check count increased
        info = self.auth.get_token_info(token)
        self.assertEqual(info['use_count'], 3)

    def test_token_info_nonexistent(self):
        """Test getting info for non-existent token"""
        fake_token = "00000000-0000-0000-0000-000000000000"
        info = self.auth.get_token_info(fake_token)
        self.assertIsNone(info)

    def test_list_active_tokens(self):
        """Test listing active tokens"""
        # Generate multiple tokens
        token1 = self.auth.generate_token(description="Active token 1")
        token2 = self.auth.generate_token(description="Active token 2")
        token3 = self.auth.generate_token(description="Active token 3")

        # Get active tokens
        active_tokens = self.auth.list_active_tokens()

        # Should have at least 3 active tokens (plus any from initialization)
        self.assertGreaterEqual(len(active_tokens), 3)

        # Revoke one token
        self.auth.revoke_token(token2)

        # Active count should decrease
        new_active_tokens = self.auth.list_active_tokens()
        self.assertEqual(len(new_active_tokens), len(active_tokens) - 1)


class TestHelperFunctions(unittest.TestCase):
    """Test suite for helper functions"""

    def test_validate_api_token_valid(self):
        """Test API token validation with valid token"""
        token = auth_manager.generate_token(description="API test token")
        auth_header = f"Bearer {token}"

        result = validate_api_token(auth_header)
        self.assertTrue(result)

    def test_validate_api_token_invalid(self):
        """Test API token validation with invalid token"""
        auth_header = "Bearer invalid_token_xyz"

        result = validate_api_token(auth_header)
        self.assertFalse(result)

    def test_validate_websocket_token_valid(self):
        """Test WebSocket token validation with valid token"""
        token = auth_manager.generate_token(description="WebSocket test token")
        headers = {'Authorization': f'Bearer {token}'}

        result = validate_websocket_token(headers)
        self.assertTrue(result)

    def test_validate_websocket_token_lowercase_header(self):
        """Test WebSocket token validation with lowercase header key"""
        token = auth_manager.generate_token(description="WebSocket test token")
        headers = {'authorization': f'Bearer {token}'}

        result = validate_websocket_token(headers)
        self.assertTrue(result)

    def test_validate_websocket_token_invalid(self):
        """Test WebSocket token validation with invalid token"""
        headers = {'Authorization': 'Bearer invalid_token_xyz'}

        result = validate_websocket_token(headers)
        self.assertFalse(result)

    def test_validate_websocket_token_missing(self):
        """Test WebSocket token validation with missing header"""
        headers = {}

        result = validate_websocket_token(headers)
        self.assertFalse(result)

    def test_get_current_token_valid(self):
        """Test getting current token with valid auth"""
        token = auth_manager.generate_token(description="Current token test")
        auth_header = f"Bearer {token}"

        result = get_current_token(auth_header)
        self.assertEqual(result, token)

    def test_get_current_token_invalid(self):
        """Test getting current token with invalid auth"""
        auth_header = "Bearer invalid_token_xyz"

        result = get_current_token(auth_header)
        self.assertIsNone(result)


class TestSecurityProperties(unittest.TestCase):
    """Test suite for security properties"""

    def test_token_uniqueness(self):
        """Test that generated tokens are unique"""
        tokens = set()
        for i in range(100):
            token = auth_manager.generate_token(description=f"Uniqueness test {i}")
            tokens.add(token)

        # All 100 tokens should be unique
        self.assertEqual(len(tokens), 100)

    def test_token_format_security(self):
        """Test token format follows UUID standard"""
        token = auth_manager.generate_token(description="Format test")

        # UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
        parts = token.split('-')
        self.assertEqual(len(parts), 5)
        self.assertEqual(len(parts[0]), 8)
        self.assertEqual(len(parts[1]), 4)
        self.assertEqual(len(parts[2]), 4)
        self.assertEqual(len(parts[3]), 4)
        self.assertEqual(len(parts[4]), 12)

    def test_revoked_tokens_remain_revoked(self):
        """Test that revoked tokens cannot be re-activated"""
        token = auth_manager.generate_token(description="Revoke persistence test")

        # Revoke token
        auth_manager.revoke_token(token)
        self.assertFalse(auth_manager.validate_token(token))

        # Try to validate multiple times (should remain invalid)
        for _ in range(10):
            self.assertFalse(auth_manager.validate_token(token))

    def test_case_sensitive_tokens(self):
        """Test that tokens are case-sensitive"""
        token = auth_manager.generate_token(description="Case sensitivity test")

        # Original token is valid
        self.assertTrue(auth_manager.validate_token(token))

        # Uppercase version should be invalid
        self.assertFalse(auth_manager.validate_token(token.upper()))

        # Lowercase version should be invalid (if different)
        if token != token.lower():
            self.assertFalse(auth_manager.validate_token(token.lower()))


def run_tests():
    """Run all test suites"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestAuthenticationTokenManagement))
    suite.addTests(loader.loadTestsFromTestCase(TestBearerTokenExtraction))
    suite.addTests(loader.loadTestsFromTestCase(TestTokenUsageTracking))
    suite.addTests(loader.loadTestsFromTestCase(TestHelperFunctions))
    suite.addTests(loader.loadTestsFromTestCase(TestSecurityProperties))

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "="*70)
    print("AUTHENTICATION TEST SUITE SUMMARY")
    print("="*70)
    print(f"Tests Run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success Rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print("="*70)

    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
